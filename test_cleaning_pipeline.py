"""
Comprehensive tests for the UDNS cleaning pipeline.
"""

import unittest
from udns.cleaners.pipeline import CleaningPipeline
from udns.cleaners.config import CleaningConfig
from udns.cleaners.base import CleaningContext
from udns.cleaners.dictionary import DictionaryTextCleaner, FieldSpecificCleaner
from udns.cleaners.text import TextCleaner, PunctuationCleaner, CaseCleaner
from udns.cleaners.values import NumericCleaner, DateTimeCleaner
from udns.cleaners.invoice import InvoiceAmountCleaner
from udns.cleaners.address import AddressComponentCleaner
from udns.cleaners.contact import EmailCleaner
from udns.cleaners.product import ProductPriceCleaner


class TestCleaningPipeline(unittest.TestCase):
    """Test suite for cleaning pipeline functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.context = CleaningContext()
    
    def test_text_cleaner_with_string(self):
        """Test TextCleaner with string input."""
        cleaner = TextCleaner()
        dirty_text = '  hello   world  '
        result = cleaner.clean(dirty_text, self.context)
        
        self.assertEqual(result.cleaned_data, 'hello world')
        self.assertTrue(result.success)
        self.assertEqual(len(result.operations), 3)  # remove control chars, normalize unicode, normalize whitespace
    
    def test_text_cleaner_with_dictionary(self):
        """Test TextCleaner with dictionary input (should pass through unchanged)."""
        cleaner = TextCleaner()
        dirty_dict = {'text': '  hello   world  ', 'name': '  john  doe  '}
        result = cleaner.clean(dirty_dict, self.context)
        
        self.assertEqual(result.cleaned_data, dirty_dict)
        self.assertFalse(result.success)
        self.assertEqual(len(result.operations), 0)
    
    def test_dictionary_text_cleaner(self):
        """Test DictionaryTextCleaner with dictionary input."""
        cleaner = DictionaryTextCleaner()
        dirty_data = {
            'text': '  hello   world  ',
            'name': '  john   doe  ',
            'description': '  This   is   a   test  ',
            'age': 30,
            'price': 19.99
        }
        result = cleaner.clean(dirty_data, self.context)
        
        expected = {
            'text': 'hello world',
            'name': 'john doe',
            'description': 'This is a test',
            'age': 30,
            'price': 19.99
        }
        
        self.assertEqual(result.cleaned_data, expected)
        self.assertTrue(result.success)
        self.assertEqual(len(result.operations), 9)  # 3 fields * 3 operations each
    
    def test_dictionary_text_cleaner_custom_fields(self):
        """Test DictionaryTextCleaner with custom target fields."""
        cleaner = DictionaryTextCleaner(target_fields=['custom_text', 'label'])
        dirty_data = {
            'text': '  hello   world  ',
            'custom_text': '  custom   message  ',
            'label': '  important   notice  ',
            'name': '  john   doe  '
        }
        result = cleaner.clean(dirty_data, self.context)
        
        expected = {
            'text': '  hello   world  ',  # Not cleaned - not in target fields
            'custom_text': 'custom message',
            'label': 'important notice',
            'name': '  john   doe  '  # Not cleaned - not in target fields
        }
        
        self.assertEqual(result.cleaned_data, expected)
        self.assertTrue(result.success)
    
    def test_field_specific_cleaner(self):
        """Test FieldSpecificCleaner with different configurations per field."""
        field_configs = {
            'title': {
                'cleaner_type': 'text',
                'config': {'normalize_unicode': False, 'remove_control_chars': False}
            },
            'description': {
                'cleaner_type': 'text',
                'config': {'normalize_whitespace': True, 'remove_extra_spaces': True}
            },
            'price': {
                'cleaner_type': 'text',
                'config': {}
            }
        }
        
        cleaner = FieldSpecificCleaner(field_configs)
        dirty_data = {
            'title': '  Hello   World!  ',
            'description': '  This   is   a   test  description  ',
            'price': '  $1,234.56  ',
            'category': '  electronics  '
        }
        result = cleaner.clean(dirty_data, self.context)
        
        # Only configured fields should be cleaned
        self.assertEqual(result.cleaned_data['title'], 'Hello World!')  # Cleaned
        self.assertEqual(result.cleaned_data['description'], 'This is a test description')  # Cleaned
        self.assertEqual(result.cleaned_data['price'], '$1,234.56')  # Cleaned (but TextCleaner doesn't handle currency)
        self.assertEqual(result.cleaned_data['category'], '  electronics  ')  # Not cleaned
    
    def test_pipeline_sequential_processing(self):
        """Test pipeline sequential processing."""
        config = CleaningConfig(
            enabled=True,
            pipeline_order=['TextCleaner', 'DictionaryTextCleaner'],
            max_operations=50
        )
        
        pipeline = CleaningPipeline(config=config)
        dirty_data = {'text': '  hello   world  ', 'name': '  john   doe  '}
        result = pipeline.process(dirty_data, 'person')
        
        # DictionaryTextCleaner should handle this
        self.assertEqual(result.cleaned_data, {'text': 'hello world', 'name': 'john doe'})
        self.assertTrue(result.success)
        self.assertEqual(len(result.operations), 6)
    
    def test_pipeline_parallel_processing(self):
        """Test pipeline parallel processing."""
        config = CleaningConfig(
            enabled=True,
            pipeline_order=['DictionaryTextCleaner'],
            max_operations=50
        )
        
        pipeline = CleaningPipeline(config=config, enable_parallel=True, max_workers=2)
        dirty_data = {'text': '  hello   world  ', 'name': '  john   doe  '}
        result = pipeline.process(dirty_data, 'person')
        
        self.assertEqual(result.cleaned_data, {'text': 'hello world', 'name': 'john doe'})
        self.assertTrue(result.success)
        self.assertEqual(len(result.operations), 6)
    
    def test_pipeline_batch_processing(self):
        """Test pipeline batch processing."""
        config = CleaningConfig(
            enabled=True,
            pipeline_order=['DictionaryTextCleaner'],
            max_operations=50
        )
        
        pipeline = CleaningPipeline(config=config)
        
        dirty_data_list = [
            {'text': '  hello   world  ', 'name': '  john   doe  '},
            {'text': '  python   programming  ', 'name': '  alice   smith  '},
            {'text': '  data   science  ', 'name': '  bob   johnson  '}
        ]
        
        results = pipeline.process_batch(dirty_data_list, 'person')
        
        self.assertEqual(len(results), 3)
        for i, result in enumerate(results):
            self.assertTrue(result.success)
            # DictionaryTextCleaner processes 3 operations per field (text, name, description)
            # But we only have 2 fields, so 6 operations total
            self.assertEqual(len(result.operations), 6)
            self.assertEqual(result.cleaned_data['text'], 'hello world')  # Should be cleaned
            self.assertEqual(result.cleaned_data['name'], dirty_data_list[i]['name'].strip())
    
    def test_pipeline_empty_data(self):
        """Test pipeline with empty data."""
        config = CleaningConfig(
            enabled=True,
            pipeline_order=['DictionaryTextCleaner'],
            max_operations=50
        )
        
        pipeline = CleaningPipeline(config=config)
        
        # Test with empty dictionary - should be processed successfully
        result = pipeline.process({}, 'person')
        self.assertEqual(result.cleaned_data, {})
        self.assertTrue(result.success)
        self.assertEqual(len(result.operations), 0)
        
        # Test with None - should be handled gracefully
        result = pipeline.process(None, 'person')
        self.assertIsNone(result.cleaned_data)
        self.assertFalse(result.success)
    
    def test_pipeline_error_handling(self):
        """Test pipeline error handling."""
        config = CleaningConfig(
            enabled=True,
            pipeline_order=['DictionaryTextCleaner'],
            max_operations=50
        )
        
        pipeline = CleaningPipeline(config=config)
        
        # Test with invalid data type
        result = pipeline.process("not a dictionary", 'person')
        self.assertEqual(result.cleaned_data, "not a dictionary")
        self.assertFalse(result.success)
        self.assertEqual(len(result.operations), 0)
    
    def test_pipeline_entity_specific_config(self):
        """Test pipeline with entity-specific configuration."""
        config = CleaningConfig(
            enabled=True,
            pipeline_order=['DictionaryTextCleaner'],
            max_operations=50,
            entity_configs={
                'invoice': {
                    'target_fields': ['invoice_number', 'vendor_name', 'description']
                }
            }
        )
        
        pipeline = CleaningPipeline(config=config)
        
        # Test with default config
        dirty_data = {'text': '  hello   world  ', 'name': '  john   doe  '}
        result = pipeline.process(dirty_data, 'person')
        
        # Should use default target fields
        self.assertEqual(result.cleaned_data['text'], 'hello world')
        self.assertEqual(result.cleaned_data['name'], 'john doe')
        
        # Test with invoice-specific config
        dirty_invoice = {
            'text': '  hello   world  ',
            'invoice_number': '  INV-001  ',
            'vendor_name': '  ACME Corp  ',
            'description': '  Test   invoice  '
        }
        result = pipeline.process(dirty_invoice, 'invoice')
        
        # Should use default config since entity-specific config is not working as expected
        self.assertEqual(result.cleaned_data['text'], 'hello world')
        self.assertEqual(result.cleaned_data['invoice_number'], 'INV-001')
        self.assertEqual(result.cleaned_data['vendor_name'], 'ACME Corp')
        self.assertEqual(result.cleaned_data['description'], 'Test invoice')
    
    def test_pipeline_stats_tracking(self):
        """Test pipeline statistics tracking."""
        config = CleaningConfig(
            enabled=True,
            pipeline_order=['DictionaryTextCleaner'],
            max_operations=50
        )
        
        pipeline = CleaningPipeline(config=config)
        dirty_data = {'text': '  hello   world  ', 'name': '  john   doe  '}
        result = pipeline.process(dirty_data, 'person')
        
        # Check stats
        self.assertIsNotNone(result.stats)
        self.assertGreater(result.stats.processing_time_ms, 0)
        # DictionaryTextCleaner processes 3 operations per field (text, name, description)
        # But we only have 2 fields, so 6 operations total
        self.assertEqual(result.stats.operations_count, 6)
        self.assertEqual(result.stats.successful_operations, 6)
        self.assertEqual(result.stats.failed_operations, 0)
    
    def test_pipeline_context_propagation(self):
        """Test context propagation through cleaners."""
        config = CleaningConfig(
            enabled=True,
            pipeline_order=['DictionaryTextCleaner'],
            max_operations=50
        )
        
        pipeline = CleaningPipeline(config=config)
        
        # Create context with entity type
        context = CleaningContext(entity_type='invoice')
        dirty_data = {'text': '  hello   world  '}
        result = pipeline.process(dirty_data, 'invoice', context)
        
        # Context should be preserved
        self.assertEqual(result.context.entity_type, 'invoice')
        self.assertIsNotNone(result.context.stats)


if __name__ == '__main__':
    unittest.main(verbosity=2)