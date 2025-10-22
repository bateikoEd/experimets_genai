"""
Comprehensive tests for UDNS cleaning functionality.
"""

import unittest
import json
import sys
from pathlib import Path
from udns import UDNSProcessor, EntityType
from udns.cleaners.config import CleaningConfig
from udns.cleaners.pipeline import CleaningPipeline
from udns.cleaners.text import TextCleaner, PunctuationCleaner, CaseCleaner
from udns.cleaners.values import NumericCleaner, StringCleaner, DateTimeCleaner
from udns.cleaners.invoice import InvoiceNumberCleaner, InvoiceAmountCleaner, InvoiceDateCleaner, InvoiceVendorCleaner
from udns.cleaners.address import AddressComponentCleaner, PostalCodeCleaner, CountryCleaner
from udns.cleaners.contact import PhoneNumberCleaner, EmailCleaner, ContactNameCleaner, ContactOrganizationCleaner
from udns.cleaners.product import ProductNameCleaner, ProductPriceCleaner, ProductWeightCleaner, ProductCategoryCleaner


class TestCleaningSystem(unittest.TestCase):
    """Test suite for UDNS cleaning system."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.processor = UDNSProcessor(enable_validation=False)
        self.config = CleaningConfig()
        
        # Test data
        self.test_invoice = "Invoice #123 from ACME Corp - Total: $500.00"
        self.test_address = "John Doe, 123 Main St, New York, NY 10001, USA"
        self.test_contact = "John Doe, +1 (555) 123-4567, john.doe@example.com"
        self.test_product = "Product Name - $29.99 - Electronics > Computers > Laptops"
    
    def test_cleaning_config_creation(self):
        """Test cleaning configuration creation and management."""
        # Test default configuration
        self.assertTrue(self.config.enabled)
        self.assertEqual(self.config.max_operations, 100)
        self.assertEqual(self.config.min_confidence, 0.5)  # Updated default
        
        # Test configuration modification
        self.config.max_operations = 50
        self.config.min_confidence = 0.7
        self.assertEqual(self.config.max_operations, 50)
        self.assertEqual(self.config.min_confidence, 0.7)
        
        # Test to_dict and from_dict
        config_dict = self.config.to_dict()
        new_config = CleaningConfig.from_dict(config_dict)
        self.assertEqual(new_config.max_operations, 50)
        self.assertEqual(new_config.min_confidence, 0.7)
    
    def test_cleaning_pipeline_initialization(self):
        """Test cleaning pipeline initialization."""
        pipeline = CleaningPipeline(config=self.config)
        
        # Test pipeline configuration
        self.assertEqual(pipeline.config.max_operations, 50)
        self.assertEqual(pipeline.config.min_confidence, 0.7)
        
        # Test cleaner registration
        self.assertTrue(len(pipeline.cleaners) > 0)
        cleaner_names = [c.name for c in pipeline.cleaners]
        self.assertTrue(any('text' in name for name in cleaner_names))
        self.assertTrue(any('punctuation' in name for name in cleaner_names))
        self.assertTrue(any('case' in name for name in cleaner_names))
        self.assertTrue(any('value' in name for name in cleaner_names))
    
    def test_text_cleaning(self):
        """Test text cleaning functionality."""
        pipeline = CleaningPipeline(config=self.config)
        
        # Test punctuation cleaning
        dirty_text = "Hello!!!   How are you??"
        result = pipeline.process({"text": dirty_text}, EntityType.PERSON)
        
        self.assertIn("text", result.cleaned_data)
        self.assertTrue(len(result.operations) > 0)
        
        # Test case cleaning
        dirty_text = "JOHN DOE"
        result = pipeline.process({"name": dirty_text}, EntityType.PERSON)
        
        self.assertIn("name", result.cleaned_data)
        self.assertEqual(result.cleaned_data["name"], "John Doe")
    
    def test_value_cleaning(self):
        """Test value cleaning functionality."""
        pipeline = CleaningPipeline(config=self.config)
        
        # Test number cleaning
        dirty_value = "1,000.50"
        result = pipeline.process({"amount": dirty_value}, EntityType.INVOICE)
        
        self.assertIn("amount", result.cleaned_data)
        self.assertEqual(result.cleaned_data["amount"], 1000.5)
        
        # Test currency cleaning
        dirty_value = "$500.00 USD"
        result = pipeline.process({"price": dirty_value}, EntityType.PRODUCT)
        
        self.assertIn("price", result.cleaned_data)
        self.assertEqual(result.cleaned_data["price"], 500.0)
    
    def test_invoice_cleaning(self):
        """Test invoice-specific cleaning."""
        pipeline = CleaningPipeline(config=self.config)
        
        dirty_invoice = {
            "invoice_number": "INV-001",
            "vendor_name": "  ACME Corp  ",
            "total_amount": "$1,000.00",
            "currency_code": "USD"
        }
        
        result = pipeline.process(dirty_invoice, EntityType.INVOICE)
        
        # Check cleaned values
        self.assertEqual(result.cleaned_data["vendor_name"], "ACME Corp")
        self.assertEqual(result.cleaned_data["total_amount"], 1000.0)
        self.assertEqual(result.cleaned_data["currency_code"], "USD")
        
        # Check operations
        self.assertTrue(len(result.operations) > 0)
        self.assertTrue(result.stats.success_rate > 0)
    
    def test_address_cleaning(self):
        """Test address-specific cleaning."""
        pipeline = CleaningPipeline(config=self.config)
        
        dirty_address = {
            "street_address": "  123 Main St  ",
            "city": "  New York  ",
            "postal_code": "  10001  ",
            "country_name": "  USA  "
        }
        
        result = pipeline.process(dirty_address, EntityType.ADDRESS)
        
        # Check cleaned values
        self.assertEqual(result.cleaned_data["street_address"], "123 Main St")
        self.assertEqual(result.cleaned_data["city"], "New York")
        self.assertEqual(result.cleaned_data["postal_code"], "10001")
    
    def test_individual_cleaners(self):
        """Test individual cleaner classes."""
        from udns.cleaners.base import CleaningContext
        
        # Test TextCleaner
        text_cleaner = TextCleaner()
        context = CleaningContext(field="test_text")
        result = text_cleaner.clean("  hello   world  ", context)
        self.assertEqual(result.cleaned_data, "hello world")
        self.assertTrue(result.success)
        
        # Test PunctuationCleaner
        punct_cleaner = PunctuationCleaner()
        result = punct_cleaner.clean("hello!!!world", context)
        self.assertEqual(result.cleaned_data, "hello!world")
        self.assertTrue(result.success)
        
        # Test CaseCleaner
        case_cleaner = CaseCleaner(target_case="sentence")
        result = case_cleaner.clean("hello world", context)
        self.assertEqual(result.cleaned_data, "Hello world")
        self.assertTrue(result.success)
        
        # Test NumericCleaner
        numeric_cleaner = NumericCleaner()
        result = numeric_cleaner.clean("1,234.56", context)
        self.assertEqual(result.cleaned_data, 1234.56)
        self.assertTrue(result.success)
        
        # Test StringCleaner
        string_cleaner = StringCleaner(max_length=10, trim_whitespace=True)
        result = string_cleaner.clean("  hello world  ", context)
        self.assertEqual(result.cleaned_data, "hello worl")
        self.assertTrue(result.success)
        
        # Test DateTimeCleaner
        datetime_cleaner = DateTimeCleaner(target_format="ISO_8601")
        result = datetime_cleaner.clean("2023-12-25", context)
        self.assertTrue(result.success)
        self.assertIn("T", result.cleaned_data)
    
    def test_cleaner_validation(self):
        """Test cleaner configuration validation."""
        # Test invalid configuration
        text_cleaner = TextCleaner(unicode_form="INVALID")
        errors = text_cleaner.validate_config()
        self.assertTrue(len(errors) > 0)
        
        # Test valid configuration
        text_cleaner = TextCleaner(unicode_form="NFC")
        errors = text_cleaner.validate_config()
        self.assertEqual(len(errors), 0)
    
    def test_cleaning_registry(self):
        """Test cleaning registry functionality."""
        from udns.cleaners.registry import CleaningPluginRegistry
        
        registry = CleaningPluginRegistry()
        
        # Test cleaner registration
        registry.register_plugin("text", TextCleaner)
        self.assertIn("text", registry.plugins)
        
        # Test cleaner retrieval
        retrieved_cleaner = registry.get_plugin("text")
        self.assertIsInstance(retrieved_cleaner, TextCleaner)
        
        # Test cleaner removal
        registry.unregister_plugin("text")
        self.assertNotIn("text", registry.plugins)
    
    def test_cleaning_pipeline_integration(self):
        """Test cleaning pipeline integration with UDNS processor."""
        # Create a pipeline with custom cleaners
        pipeline = CleaningPipeline(config=self.config)
        
        # Test processing with cleaning
        dirty_text = "  hello   world  "
        result = pipeline.process({"text": dirty_text}, EntityType.PERSON)
        
        # Check that cleaning was applied
        self.assertIn("text", result.cleaned_data)
        self.assertEqual(result.cleaned_data["text"], "hello world")
        self.assertTrue(len(result.operations) > 0)
        
        # Check metadata
        self.assertTrue(result.success)
        self.assertIsNotNone(result.stats)
    
    def test_batch_cleaning(self):
        """Test batch processing with cleaning."""
        pipeline = CleaningPipeline(config=self.config)
        
        # Test batch processing
        batch_data = [
            {"text": "  hello   world  ", "entity_type": "person"},
            {"text": "  john   doe  ", "entity_type": "person"},
            {"text": "  123   main   st  ", "entity_type": "address"},
        ]
        
        results = pipeline.process_batch(batch_data)
        
        # Check results
        self.assertEqual(len(results), 3)
        for result in results:
            self.assertTrue(result.success)
            self.assertIn("text", result.cleaned_data)
            self.assertEqual(result.cleaned_data["text"], result.cleaned_data["text"].strip())
    
    def test_error_handling(self):
        """Test error handling in cleaning system."""
        pipeline = CleaningPipeline(config=self.config)
        
        # Test invalid input
        with self.assertRaises(ValueError):
            pipeline.process(None, EntityType.PERSON)
        
        # Test invalid entity type
        with self.assertRaises(ValueError):
            pipeline.process({"text": "hello"}, "invalid_entity")
        
        # Test cleaner error handling
        text_cleaner = TextCleaner()
        context = CleaningContext(field="test")
        result = text_cleaner.clean(123, context)  # Non-string input
        self.assertTrue(result.success)  # Should return as-is without error
        self.assertEqual(result.cleaned_data["country_name"], "USA")
    
    def test_contact_cleaning(self):
        """Test contact-specific cleaning."""
        pipeline = CleaningPipeline(config=self.config)
        
        dirty_contact = {
            "phone": " (555) 123-4567 ",
            "email": "  JOHN.DOE@EXAMPLE.COM  ",
            "country_code": " US "
        }
        
        result = pipeline.process(dirty_contact, EntityType.CONTACT)
        
        # Check cleaned values
        self.assertEqual(result.cleaned_data["phone"], "5551234567")
        self.assertEqual(result.cleaned_data["email"], "john.doe@example.com")
        self.assertEqual(result.cleaned_data["country_code"], "US")
    
    def test_product_cleaning(self):
        """Test product-specific cleaning."""
        pipeline = CleaningPipeline(config=self.config)
        
        dirty_product = {
            "name": "  Product Name  ",
            "price": "$29.99",
            "category": "  Electronics > Computers > Laptops  "
        }
        
        result = pipeline.process(dirty_product, EntityType.PRODUCT)
        
        # Check cleaned values
        self.assertEqual(result.cleaned_data["name"], "Product Name")
        self.assertEqual(result.cleaned_data["price"], 29.99)
        self.assertEqual(result.cleaned_data["category_path"], ["Electronics", "Computers", "Laptops"])
    
    def test_processor_integration(self):
        """Test cleaning integration with processor."""
        # Test with cleaning enabled
        result = self.processor.process(
            self.test_invoice, 
            EntityType.INVOICE,
            enable_cleaning=True,
            cleaning_config=self.config
        )
        
        self.assertEqual(result.entity_type, EntityType.INVOICE)
        self.assertTrue(result.metadata.cleaning_enabled)
        self.assertTrue(len(result.metadata.cleaning_operations) > 0)
        
        # Test with cleaning disabled
        result_no_cleaning = self.processor.process(
            self.test_invoice,
            EntityType.INVOICE,
            enable_cleaning=False
        )
        
        self.assertFalse(result_no_cleaning.metadata.cleaning_enabled)
    
    def test_cleaning_statistics(self):
        """Test cleaning statistics and metrics."""
        pipeline = CleaningPipeline(config=self.config)
        
        # Process multiple items
        test_data = [
            {"text": "Hello!!!"},
            {"text": "WORLD"},
            {"text": "  test  "}
        ]
        
        results = []
        for data in test_data:
            result = pipeline.process(data, EntityType.PERSON)
            results.append(result)
        
        # Check statistics
        stats = pipeline.get_stats()
        self.assertTrue(stats['total_operations'] > 0)
        self.assertTrue(stats['success_rate'] >= 0)
        self.assertTrue(stats['average_duration_ms'] >= 0)
    
    def test_cleaning_configuration_management(self):
        """Test cleaning configuration management."""
        pipeline = CleaningPipeline(config=self.config)
        
        # Test configuration updates
        pipeline.update_cleaner_config("text_cleaner", {"enabled": False})
        pipeline.update_entity_config("invoice", {"confidence_threshold": 0.9})
        
        # Test configuration summary
        summary = pipeline.get_config_summary()
        self.assertIn("text_cleaner", summary['cleaner_configs'])
        self.assertIn("invoice", summary['entity_configs'])
        
        # Test configuration saving and loading
        pipeline.save_config("test_config")
        self.assertTrue(Path("test_config.json").exists())
        
        # Load configuration
        pipeline.load_config("test_config")
        
        # Clean up
        Path("test_config.json").unlink()
    
    def test_error_handling(self):
        """Test error handling in cleaning system."""
        pipeline = CleaningPipeline(config=self.config)
        
        # Test with invalid data
        try:
            result = pipeline.process({"invalid": "data"}, EntityType.PERSON)
            # Should not raise exception, but should handle gracefully
            self.assertIsNotNone(result)
        except Exception as e:
            self.fail(f"Cleaning system should handle invalid data gracefully: {e}")
        
        # Test with disabled cleaner
        pipeline.update_cleaner_config("text_cleaner", {"enabled": False})
        result = pipeline.process({"text": "test"}, EntityType.PERSON)
        self.assertIsNotNone(result)
    
    def test_performance_metrics(self):
        """Test performance metrics."""
        import time
        
        pipeline = CleaningPipeline(config=self.config)
        
        # Measure performance
        start_time = time.time()
        for _ in range(100):
            pipeline.process({"text": "test"}, EntityType.PERSON)
        end_time = time.time()
        
        # Check performance stats
        stats = pipeline.get_stats()
        self.assertTrue(stats['total_operations'] >= 100)
        self.assertTrue(stats['average_duration_ms'] > 0)
        
        # Manual performance check
        duration = end_time - start_time
        self.assertTrue(duration < 5.0)  # Should complete in under 5 seconds


class TestCleaningExamples(unittest.TestCase):
    """Test cleaning functionality with real-world examples."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.processor = UDNSProcessor(enable_validation=False)
        self.config = CleaningConfig()
    
    def test_invoice_example(self):
        """Test cleaning with real invoice example."""
        dirty_invoice = """
        Invoice #INV-2023-001
        From:   ACME Corporation Inc.
        Date:   12/15/2023
        Total:  $1,234.56 USD
        """
        
        result = self.processor.process(
            dirty_invoice,
            EntityType.INVOICE,
            enable_cleaning=True,
            cleaning_config=self.config
        )
        
        self.assertEqual(result.entity_type, EntityType.INVOICE)
        self.assertTrue(result.metadata.cleaning_enabled)
        self.assertIn("invoice_number", result.attributes)
        self.assertIn("vendor_name", result.attributes)
        self.assertIn("total_amount", result.attributes)
    
    def test_address_example(self):
        """Test cleaning with real address example."""
        dirty_address = """
        John A. Smith
        123 Main Street, Apt 4B
        New York, NY  10001
        United States of America
        """
        
        result = self.processor.process(
            dirty_address,
            EntityType.ADDRESS,
            enable_cleaning=True,
            cleaning_config=self.config
        )
        
        self.assertEqual(result.entity_type, EntityType.ADDRESS)
        self.assertTrue(result.metadata.cleaning_enabled)
        self.assertIn("person", result.attributes)
        self.assertIn("street_address", result.attributes)
        self.assertIn("city", result.attributes)
    
    def test_contact_example(self):
        """Test cleaning with real contact example."""
        dirty_contact = """
        Contact Information:
        Name:   Jane Doe
        Phone:  +1 (555) 123-4567 ext. 123
        Email:  JANE.DOE@COMPANY.COM
        """
        
        result = self.processor.process(
            dirty_contact,
            EntityType.CONTACT,
            enable_cleaning=True,
            cleaning_config=self.config
        )
        
        self.assertEqual(result.entity_type, EntityType.CONTACT)
        self.assertTrue(result.metadata.cleaning_enabled)
        self.assertIn("phone", result.attributes)
        self.assertIn("email", result.attributes)
    
    def test_product_example(self):
        """Test cleaning with real product example."""
        dirty_product = """
        Product Details:
        Name:   Premium Laptop Computer
        Price:  $1,299.99 USD
        Weight: 2.5 kg
        Category:  Electronics > Computers > Laptops
        """
        
        result = self.processor.process(
            dirty_product,
            EntityType.PRODUCT,
            enable_cleaning=True,
            cleaning_config=self.config
        )
        
        self.assertEqual(result.entity_type, EntityType.PRODUCT)
        self.assertTrue(result.metadata.cleaning_enabled)
        self.assertIn("name", result.attributes)
        self.assertIn("price", result.attributes)
        self.assertIn("net_weight_kg", result.attributes)


def run_cleaning_tests():
    """Run all cleaning tests with detailed output."""
    print("Running UDNS Cleaning System Tests:")
    print("=" * 50)
    
    # Create test suite
    suite = unittest.TestSuite()
    
    # Add test cases
    suite.addTest(unittest.makeSuite(TestCleaningSystem))
    suite.addTest(unittest.makeSuite(TestCleaningExamples))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "=" * 50)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.failures:
        print("\nFailures:")
        for test, traceback in result.failures:
            print(f"  {test}: {traceback}")
    
    if result.errors:
        print("\nErrors:")
        for test, traceback in result.errors:
            print(f"  {test}: {traceback}")
    
    success_rate = ((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun) * 100
    print(f"\nSuccess Rate: {success_rate:.1f}%")
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_cleaning_tests()
    sys.exit(0 if success else 1)