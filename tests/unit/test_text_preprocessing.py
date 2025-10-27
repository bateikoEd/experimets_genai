"""
Unit tests for text preprocessing functionality.
"""
import unittest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock
import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from data_processing.text_preprocessing import TextPreprocessor


class TestTextPreprocessor(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures."""
        # Sample text data
        self.sample_data = pd.DataFrame({
            'description': [
                'Beautiful 3-bedroom house with modern kitchen',
                'Cozy apartment in downtown Seattle',
                'Luxury villa with swimming pool and garden',
                'Charming cottage near the beach',
                None,  # Missing value
                ''  # Empty string
            ],
            'comments': [
                'Great location, close to schools',
                'Needs some renovation work',
                'Perfect for families',
                'Quiet neighborhood',
                'No comments available',
                'See description above'
            ],
            'numeric_col': [1, 2, 3, 4, 5, 6]  # Should be filtered out
        })
        
        self.preprocessor = TextPreprocessor()
    
    def test_init_default_params(self):
        """Test initialization with default parameters."""
        processor = TextPreprocessor()
        
        self.assertTrue(processor.extract_features)
        self.assertEqual(processor.max_features, 1000)
        self.assertTrue(processor.extract_ner)
        self.assertEqual(processor.min_df, 1)
        self.assertEqual(processor.max_df, 1.0)
    
    def test_init_custom_params(self):
        """Test initialization with custom parameters."""
        processor = TextPreprocessor(
            extract_features=False,
            max_features=500,
            extract_ner=False,
            min_df=2,
            max_df=0.8
        )
        
        self.assertFalse(processor.extract_features)
        self.assertEqual(processor.max_features, 500)
        self.assertFalse(processor.extract_ner)
        self.assertEqual(processor.min_df, 2)
        self.assertEqual(processor.max_df, 0.8)
    
    def test_identify_text_columns(self):
        """Test identification of text columns."""
        text_cols = self.preprocessor.identify_text_columns(self.sample_data)
        
        expected_cols = ['description', 'comments']
        self.assertEqual(set(text_cols), set(expected_cols))
        
        # Verify numeric column is excluded
        self.assertNotIn('numeric_col', text_cols)
    
    def test_clean_text(self):
        """Test text cleaning functionality."""
        test_text = "This is a GREAT house!!! It has 3 bedrooms and 2.5 bathrooms."
        
        cleaned = self.preprocessor._clean_text(test_text)
        
        # Check that text is cleaned
        self.assertIsInstance(cleaned, str)
        self.assertNotIn('!!!', cleaned)  # Multiple punctuation should be handled
        # Text should be converted to lowercase
        self.assertEqual(cleaned, cleaned.lower())
    
    def test_clean_text_with_none(self):
        """Test text cleaning with None input."""
        result = self.preprocessor._clean_text(None)
        self.assertEqual(result, '')
    
    def test_clean_text_with_empty_string(self):
        """Test text cleaning with empty string input."""
        result = self.preprocessor._clean_text('')
        self.assertEqual(result, '')
    
    def test_extract_basic_features(self):
        """Test basic feature extraction from text."""
        test_text = "This is a sample text with multiple words."
        
        features = self.preprocessor._extract_basic_features(test_text)
        
        self.assertIsInstance(features, dict)
        self.assertIn('length', features)
        self.assertIn('word_count', features)
        
        # Check specific values
        self.assertGreater(features['length'], 0)
        self.assertGreater(features['word_count'], 0)
    
    def test_extract_basic_features_empty_text(self):
        """Test basic feature extraction with empty text."""
        features = self.preprocessor._extract_basic_features('')
        
        self.assertIsInstance(features, dict)
        self.assertEqual(features['length'], 0)
        self.assertEqual(features['word_count'], 0)
    
    @patch('data_processing.text_preprocessing.TfidfVectorizer')
    def test_extract_tfidf_features(self, mock_tfidf):
        """Test TF-IDF feature extraction."""
        # Mock TfidfVectorizer
        mock_vectorizer = MagicMock()
        mock_tfidf.return_value = mock_vectorizer
        mock_vectorizer.fit_transform.return_value.toarray.return_value = np.array([[0.1, 0.2], [0.3, 0.4]])
        mock_vectorizer.get_feature_names_out.return_value = ['word1', 'word2']
        
        test_texts = ['sample text one', 'sample text two']
        
        processor = TextPreprocessor(extract_features=True)
        processor._init_tfidf_vectorizer(['description'])
        features = processor._extract_tfidf_features(test_texts)
        
        self.assertIsInstance(features, pd.DataFrame)
        mock_vectorizer.fit_transform.assert_called_once()
    
    def test_extract_ner_features_mock(self):
        """Test NER feature extraction with mocked spaCy."""
        with patch('data_processing.text_preprocessing.spacy') as mock_spacy:
            # Mock spaCy nlp
            mock_nlp = MagicMock()
            mock_spacy.load.return_value = mock_nlp
            
            # Mock document with entities
            mock_doc = MagicMock()
            mock_entity = MagicMock()
            mock_entity.label_ = 'PERSON'
            mock_doc.ents = [mock_entity]
            mock_nlp.return_value = mock_doc
            
            processor = TextPreprocessor(extract_ner=True)
            processor._init_ner_processor()
            
            features = processor._extract_ner_features(['John is a good person'])
            
            self.assertIsInstance(features, dict)
    
    def test_handle_missing_text_values(self):
        """Test handling of missing text values."""
        test_data = self.sample_data[['description']].copy()
        
        result = self.preprocessor._handle_missing_text_values(test_data)
        
        # Check that missing values are handled
        self.assertFalse(result.isnull().any().any())
        
        # Missing values should be replaced with empty strings or default text
        for col in result.columns:
            self.assertNotIn(None, result[col].values)
    
    def test_fit_transform(self):
        """Test fit and transform functionality."""
        test_data = self.sample_data[['description', 'comments']].copy()
        
        # Fit the preprocessor
        self.preprocessor.fit(test_data)
        
        # Transform the data
        result = self.preprocessor.transform(test_data)
        
        # Check result properties
        self.assertIsInstance(result, pd.DataFrame)
        
        # Should have some features if extract_features is True
        if self.preprocessor.extract_features:
            self.assertGreater(result.shape[1], 0)
        
        # All values should be numeric
        for col in result.columns:
            self.assertTrue(pd.api.types.is_numeric_dtype(result[col]))
    
    def test_fit_transform_no_feature_extraction(self):
        """Test fit and transform without feature extraction."""
        processor = TextPreprocessor(extract_features=False, extract_ner=False)
        test_data = self.sample_data[['description']].copy()
        
        processor.fit(test_data)
        result = processor.transform(test_data)
        
        # Should return minimal features or empty DataFrame
        self.assertIsInstance(result, pd.DataFrame)
    
    def test_fit_transform_empty_data(self):
        """Test handling of empty data."""
        empty_data = pd.DataFrame()
        
        self.preprocessor.fit(empty_data)
        result = self.preprocessor.transform(empty_data)
        
        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(len(result), 0)
    
    def test_fit_transform_no_text_columns(self):
        """Test handling of data with no text columns."""
        numeric_data = pd.DataFrame({
            'num1': [1, 2, 3, 4, 5],
            'num2': [10.1, 20.2, 30.3, 40.4, 50.5]
        })
        
        self.preprocessor.fit(numeric_data)
        result = self.preprocessor.transform(numeric_data)
        
        # Should return empty DataFrame
        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(result.shape[1], 0)
    
    def test_get_feature_names(self):
        """Test getting feature names after transformation."""
        test_data = self.sample_data[['description']].copy()
        
        self.preprocessor.fit(test_data)
        feature_names = self.preprocessor.get_feature_names()
        
        self.assertIsInstance(feature_names, list)
        
        # Should have some features if extract_features is True
        if self.preprocessor.extract_features:
            self.assertGreater(len(feature_names), 0)
    
    def test_transform_before_fit_raises_error(self):
        """Test that transform raises error if called before fit."""
        test_data = self.sample_data[['description']].copy()
        
        with self.assertRaises(ValueError):
            self.preprocessor.transform(test_data)


if __name__ == '__main__':
    unittest.main()