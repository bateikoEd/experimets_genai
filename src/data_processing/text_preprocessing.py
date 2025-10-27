"""
Text feature processing utilities for NLP features.
"""

import pandas as pd
import numpy as np
import re
import string
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.pipeline import Pipeline
import logging
from typing import List, Optional, Union, Dict, Tuple

logger = logging.getLogger(__name__)


class TextPreprocessor(BaseEstimator, TransformerMixin):
    """
    Text preprocessing utilities with NLTK and spaCy integration.
    
    Handles text cleaning, tokenization, and NER feature extraction.
    """
    
    def __init__(self,
                 max_features: int = 5000,
                 min_df: int = 2,
                 max_df: float = 0.95,
                 ngram_range: Tuple[int, int] = (1, 2),
                 use_ner: bool = True,
                 spacy_model: str = 'en_core_web_sm',
                 clean_text: bool = True):
        """
        Initialize text preprocessor.
        
        Args:
            max_features: Maximum number of TF-IDF features
            min_df: Minimum document frequency for TF-IDF
            max_df: Maximum document frequency for TF-IDF
            ngram_range: N-gram range for TF-IDF
            use_ner: Whether to extract NER features
            spacy_model: spaCy model name for NER
            clean_text: Whether to apply text cleaning
        """
        self.max_features = max_features
        self.min_df = min_df
        self.max_df = max_df
        self.ngram_range = ngram_range
        self.use_ner = use_ner
        self.spacy_model = spacy_model
        self.clean_text = clean_text
        
        # Will be set during fit
        self.tfidf_vectorizer = None
        self.nlp = None
        self.feature_names = []
        self.n_features_in_ = None
        self.ner_feature_names = []
        
    def fit(self, X: Union[pd.DataFrame, np.ndarray], y=None):
        """
        Fit the text preprocessor to training data.
        
        Args:
            X: Training text data
            y: Target values (ignored)
            
        Returns:
            self
        """
        # Convert to DataFrame if needed
        if isinstance(X, np.ndarray):
            X = pd.DataFrame(X, columns=[f'text_{i}' for i in range(X.shape[1])])
        
        self.feature_names = list(X.columns)
        self.n_features_in_ = X.shape[1]
        
        logger.info(f"Fitting text preprocessor on {len(self.feature_names)} text features")
        
        # Initialize spaCy model if using NER
        if self.use_ner:
            self._initialize_spacy()
        
        # Combine all text columns for TF-IDF fitting
        combined_text = self._combine_text_columns(X)
        
        # Fit TF-IDF vectorizer
        self._fit_tfidf(combined_text)
        
        # Set up NER feature names
        if self.use_ner:
            self._setup_ner_features()
        
        return self
    
    def transform(self, X: Union[pd.DataFrame, np.ndarray]) -> np.ndarray:
        """
        Transform text data using fitted preprocessor.
        
        Args:
            X: Input text data
            
        Returns:
            Transformed data as numpy array
        """
        # Convert to DataFrame if needed
        if isinstance(X, np.ndarray):
            X = pd.DataFrame(X, columns=self.feature_names)
        
        # Validate input
        if X.shape[1] != self.n_features_in_:
            raise ValueError(f"Expected {self.n_features_in_} features, got {X.shape[1]}")
        
        # Combine text columns
        combined_text = self._combine_text_columns(X)
        
        # Extract TF-IDF features
        tfidf_features = self.tfidf_vectorizer.transform(combined_text)
        
        # Extract NER features if enabled
        if self.use_ner:
            ner_features = self._extract_ner_features(X)
            
            # Combine TF-IDF and NER features
            from scipy.sparse import hstack
            features = hstack([tfidf_features, ner_features])
        else:
            features = tfidf_features
        
        return features.toarray() if hasattr(features, 'toarray') else features
    
    def _initialize_spacy(self):
        """Initialize spaCy model for NER."""
        try:
            import spacy
            self.nlp = spacy.load(self.spacy_model)
            logger.info(f"Loaded spaCy model: {self.spacy_model}")
        except ImportError:
            logger.warning("spaCy not available. Disabling NER features.")
            self.use_ner = False
            self.nlp = None
        except OSError:
            logger.warning(f"spaCy model '{self.spacy_model}' not found. Disabling NER features.")
            logger.warning("Install with: python -m spacy download en_core_web_sm")
            self.use_ner = False
            self.nlp = None
    
    def _combine_text_columns(self, X: pd.DataFrame) -> List[str]:
        """Combine multiple text columns into single text per row."""
        combined_texts = []
        
        for _, row in X.iterrows():
            text_parts = []
            for col in self.feature_names:
                text = str(row[col]) if pd.notna(row[col]) else ''
                if self.clean_text and text:
                    text = self._clean_text(text)
                text_parts.append(text)
            
            combined_text = ' '.join(text_parts).strip()
            combined_texts.append(combined_text if combined_text else '')
        
        return combined_texts
    
    def _clean_text(self, text: str) -> str:
        """Clean text by removing unwanted characters and normalizing."""
        if not text or text == 'nan':
            return ''
        
        # Convert to lowercase
        text = text.lower()
        
        # Remove URLs
        text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
        
        # Remove email addresses
        text = re.sub(r'\S+@\S+', '', text)
        
        # Remove phone numbers (simple pattern)
        text = re.sub(r'\b\d{10,}\b', '', text)
        
        # Remove extra whitespace and punctuation
        text = re.sub(r'[^\w\s]', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        
        # Remove digits (often not meaningful in property descriptions)
        text = re.sub(r'\b\d+\b', '', text)
        
        return text.strip()
    
    def _fit_tfidf(self, texts: List[str]):
        """Fit TF-IDF vectorizer on combined texts."""
        # Initialize with custom stop words for real estate domain
        custom_stop_words = self._get_custom_stop_words()
        
        self.tfidf_vectorizer = TfidfVectorizer(
            max_features=self.max_features,
            min_df=self.min_df,
            max_df=self.max_df,
            ngram_range=self.ngram_range,
            stop_words=custom_stop_words,
            lowercase=True,
            strip_accents='unicode',
            token_pattern=r'\b[a-zA-Z][a-zA-Z]+\b'  # Only alphabetic tokens
        )
        
        self.tfidf_vectorizer.fit(texts)
        
        logger.info(f"TF-IDF vectorizer fitted with {len(self.tfidf_vectorizer.vocabulary_)} features")
    
    def _get_custom_stop_words(self) -> List[str]:
        """Get custom stop words for real estate domain."""
        # Try to use NLTK stop words if available
        try:
            import nltk
            try:
                from nltk.corpus import stopwords
                english_stops = stopwords.words('english')
            except LookupError:
                logger.warning("NLTK stopwords not found. Downloading...")
                nltk.download('stopwords')
                from nltk.corpus import stopwords
                english_stops = stopwords.words('english')
        except ImportError:
            logger.warning("NLTK not available. Using basic stop words.")
            english_stops = ['the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by']
        
        # Add domain-specific stop words
        real_estate_stops = [
            'property', 'house', 'flat', 'apartment', 'home', 'room', 'bedroom', 'bathroom',
            'kitchen', 'hall', 'balcony', 'parking', 'area', 'sqft', 'sq', 'ft',
            'available', 'sale', 'rent', 'buy', 'sell', 'price', 'cost', 'rs', 'rupees',
            'located', 'near', 'close', 'distance', 'mins', 'minutes', 'km', 'meter',
            'new', 'old', 'good', 'excellent', 'best', 'nice', 'beautiful', 'spacious',
            'contact', 'call', 'phone', 'mobile', 'number', 'details', 'info', 'information'
        ]
        
        return english_stops + real_estate_stops
    
    def _setup_ner_features(self):
        """Set up NER feature names."""
        # Common entity types for real estate
        entity_types = ['GPE', 'ORG', 'PERSON', 'LOC', 'FACILITY', 'EVENT']
        self.ner_feature_names = [f'ner_{entity_type.lower()}_count' for entity_type in entity_types]
        
        logger.info(f"NER features: {self.ner_feature_names}")
    
    def _extract_ner_features(self, X: pd.DataFrame) -> np.ndarray:
        """Extract NER features using spaCy."""
        if not self.use_ner or self.nlp is None:
            return np.zeros((len(X), len(self.ner_feature_names)))
        
        ner_features = []
        
        for _, row in X.iterrows():
            # Combine text from all columns
            combined_text = ' '.join([str(row[col]) for col in self.feature_names if pd.notna(row[col])])
            
            if not combined_text or combined_text == 'nan':
                # Empty text - all zeros
                ner_features.append([0] * len(self.ner_feature_names))
                continue
            
            # Process with spaCy
            doc = self.nlp(combined_text)
            
            # Count entities by type
            entity_counts = {
                'gpe': 0,    # Geopolitical entity (cities, countries)
                'org': 0,    # Organizations
                'person': 0, # Person names
                'loc': 0,    # Locations
                'facility': 0, # Buildings, airports, etc.
                'event': 0   # Events
            }
            
            for ent in doc.ents:
                ent_label = ent.label_.lower()
                if ent_label in entity_counts:
                    entity_counts[ent_label] += 1
            
            # Convert to feature vector
            feature_vector = [entity_counts[entity_type.split('_')[1]] 
                            for entity_type in self.ner_feature_names]
            ner_features.append(feature_vector)
        
        return np.array(ner_features)
    
    def get_feature_names_out(self, input_features=None) -> List[str]:
        """Get output feature names."""
        tfidf_names = self.tfidf_vectorizer.get_feature_names_out().tolist()
        
        if self.use_ner:
            return tfidf_names + self.ner_feature_names
        else:
            return tfidf_names


def create_text_pipeline(
    max_features: int = 5000,
    use_ner: bool = True,
    clean_text: bool = True
) -> Pipeline:
    """
    Create a scikit-learn pipeline for text preprocessing.
    
    Args:
        max_features: Maximum TF-IDF features
        use_ner: Whether to include NER features
        clean_text: Whether to apply text cleaning
        
    Returns:
        sklearn Pipeline object
    """
    preprocessor = TextPreprocessor(
        max_features=max_features,
        use_ner=use_ner,
        clean_text=clean_text
    )
    
    pipeline = Pipeline([
        ('text_preprocessor', preprocessor)
    ])
    
    return pipeline


def analyze_text_features(df: pd.DataFrame, features: List[str]) -> Dict:
    """
    Analyze text features for preprocessing insights.
    
    Args:
        df: Input DataFrame
        features: List of text feature names
        
    Returns:
        Dictionary with analysis results
    """
    analysis = {
        'text_stats': {},
        'missing_values': {},
        'length_distribution': {},
        'common_words': {}
    }
    
    for feature in features:
        if feature not in df.columns:
            logger.warning(f"Feature '{feature}' not found in DataFrame")
            continue
        
        series = df[feature].astype(str)
        
        # Basic text statistics
        text_lengths = series.str.len()
        word_counts = series.str.split().str.len()
        
        analysis['text_stats'][feature] = {
            'total_texts': len(series),
            'avg_length': text_lengths.mean(),
            'max_length': text_lengths.max(),
            'min_length': text_lengths.min(),
            'avg_words': word_counts.mean(),
            'max_words': word_counts.max()
        }
        
        # Missing/empty values
        missing_count = df[feature].isnull().sum()
        empty_count = (series == '').sum() + (series == 'nan').sum()
        
        analysis['missing_values'][feature] = {
            'missing_count': missing_count,
            'empty_count': empty_count,
            'missing_percentage': missing_count / len(series) * 100,
            'empty_percentage': empty_count / len(series) * 100
        }
        
        # Length distribution
        analysis['length_distribution'][feature] = {
            'short_texts': (text_lengths < 50).sum(),  # < 50 chars
            'medium_texts': ((text_lengths >= 50) & (text_lengths < 200)).sum(),  # 50-200 chars
            'long_texts': (text_lengths >= 200).sum()  # > 200 chars
        }
        
        # Most common words (simple analysis)
        try:
            all_text = ' '.join(series.dropna().astype(str))
            words = re.findall(r'\b[a-zA-Z][a-zA-Z]+\b', all_text.lower())
            
            from collections import Counter
            word_counts = Counter(words)
            analysis['common_words'][feature] = dict(word_counts.most_common(10))
            
        except Exception as e:
            logger.warning(f"Could not analyze common words for '{feature}': {e}")
            analysis['common_words'][feature] = {}
    
    return analysis


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)
    
    # Create sample text data
    sample_texts = [
        "Beautiful 2BHK apartment in Bandra near station",
        "Spacious villa with garden in Pune",
        "Modern flat for rent in tech city",
        "Luxurious penthouse with sea view",
        "Cozy studio apartment near metro"
    ]
    
    locations = [
        "Bandra West, Mumbai",
        "Koregaon Park, Pune", 
        "Whitefield, Bangalore",
        "Marine Drive, Mumbai",
        "Connaught Place, Delhi"
    ]
    
    df = pd.DataFrame({
        'description': sample_texts * 20,  # Repeat for more data
        'location': locations * 20
    })
    
    # Analyze text features
    analysis = analyze_text_features(df, ['description', 'location'])
    print("Text analysis:")
    for feature, stats in analysis['text_stats'].items():
        print(f"{feature}: avg_length={stats['avg_length']:.1f}, avg_words={stats['avg_words']:.1f}")
    
    # Create and test preprocessor
    preprocessor = create_text_pipeline(max_features=100, use_ner=False)  # Disable NER for quick test
    X_transformed = preprocessor.fit_transform(df)
    
    print("Original shape:", df.shape)
    print("Transformed shape:", X_transformed.shape)