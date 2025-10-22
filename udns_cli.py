#!/usr/bin/env python3
"""
Command-line interface for UDNS (Universal Data Normalization Specification).
"""

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Optional, Dict, Any
from udns import UDNSProcessor, EntityType
from udns.cleaners.config import CleaningConfig


def create_parser() -> argparse.ArgumentParser:
    """Create command-line argument parser."""
    parser = argparse.ArgumentParser(
        description="Universal Data Normalization Specification (UDNS) CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process single text input
  python udns_cli.py -t "Invoice #123 from ACME Corp - Total: $500.00"
  
  # Process text with explicit entity type
  python udns_cli.py -t "John Doe, 123 Main St" --type address
  
  # Process file with multiple inputs
  python udns_cli.py -f inputs.txt --batch
  
  # Process and save output to file
  python udns_cli.py -t "Prof. Smith - smith@company.com" -o output.json
  
  # List supported entity types
  python udns_cli.py --list-types
  
  # Validate against examples
  python udns_cli.py --validate-examples
  
  # List available cleaners
  python udns_cli.py --list-cleaners
  
  # List cleaning configurations
  python udns_cli.py --list-cleaning-configs
  
  # Load cleaning configuration
  python udns_cli.py -t "some text" --load-cleaning-config my_config
  
  # Save cleaning configuration
  python udns_cli.py --save-cleaning-config my_config
  
  # Update cleaner configuration
  python udns_cli.py --update-cleaner-config "text_cleaner" '{"enabled": false}'
  
  # Update entity configuration
  python udns_cli.py --update-entity-config "invoice" '{"confidence_threshold": 0.9}'
        """
    )
    
    # Input options
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument(
        '-t', '--text',
        help='Input text to process'
    )
    input_group.add_argument(
        '-f', '--file',
        type=Path,
        help='Input file to process'
    )
    input_group.add_argument(
        '--list-types',
        action='store_true',
        help='List supported entity types'
    )
    input_group.add_argument(
        '--validate-examples',
        action='store_true',
        help='Validate implementation against temp.json examples'
    )
    
    # Processing options
    parser.add_argument(
        '--type',
        choices=[et.value for et in EntityType],
        help='Explicit entity type (auto-detected if not specified)'
    )
    parser.add_argument(
        '--batch',
        action='store_true',
        help='Process file as batch of JSON inputs'
    )
    parser.add_argument(
        '--no-validation',
        action='store_true',
        help='Disable schema validation'
    )
    parser.add_argument(
        '--no-cleaning',
        action='store_true',
        help='Disable data cleaning'
    )
    parser.add_argument(
        '--enable-cleaning',
        action='store_true',
        help='Enable data cleaning (overrides --no-cleaning)'
    )
    parser.add_argument(
        '--cleaning-config',
        type=Path,
        help='JSON configuration file for cleaning pipeline'
    )
    parser.add_argument(
        '--list-cleaners',
        action='store_true',
        help='List available cleaners'
    )
    parser.add_argument(
        '--list-cleaning-configs',
        action='store_true',
        help='List available cleaning configurations'
    )
    parser.add_argument(
        '--save-cleaning-config',
        type=str,
        help='Save current cleaning configuration with given name'
    )
    parser.add_argument(
        '--load-cleaning-config',
        type=str,
        help='Load cleaning configuration by name'
    )
    parser.add_argument(
        '--update-cleaner-config',
        action='append',
        nargs=2,
        metavar=('CLEANER', 'CONFIG'),
        help='Update cleaner configuration (can be used multiple times)'
    )
    parser.add_argument(
        '--update-entity-config',
        action='append',
        nargs=2,
        metavar=('ENTITY', 'CONFIG'),
        help='Update entity configuration (can be used multiple times)'
    )
    parser.add_argument(
        '--confidence-threshold',
        type=float,
        default=0.0,
        help='Minimum confidence threshold (0.0-1.0)'
    )
    
    # Output options
    parser.add_argument(
        '-o', '--output',
        type=Path,
        help='Output file (stdout if not specified)'
    )
    parser.add_argument(
        '--pretty',
        action='store_true',
        help='Pretty print JSON output'
    )
    parser.add_argument(
        '--quiet',
        action='store_true',
        help='Suppress informational messages'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Verbose output with processing details'
    )
    
    return parser


def log_message(message: str, quiet: bool = False, verbose: bool = False):
    """Log message to stderr if not quiet."""
    if not quiet:
        print(f"[UDNS] {message}", file=sys.stderr)


def list_cleaners(processor: UDNSProcessor):
    """List available cleaners."""
    if not hasattr(processor, 'cleaning_pipeline'):
        print("Cleaning pipeline not available", file=sys.stderr)
        return
    
    # Get cleaner information from pipeline
    cleaner_info = processor.cleaning_pipeline.get_cleaner_info()
    print("Available Cleaners:")
    print("=" * 30)
    for cleaner in sorted(cleaner_info, key=lambda x: x['name']):
        print(f"  {cleaner['name']} v{cleaner['version']}")
        print(f"    Enabled: {'Yes' if cleaner['enabled'] else 'No'}")
    print(f"\nTotal: {len(cleaner_info)} cleaners")


def list_cleaning_configs(processor: UDNSProcessor):
    """List available cleaning configurations."""
    if not hasattr(processor, 'cleaning_pipeline'):
        print("Cleaning pipeline not available", file=sys.stderr)
        return
    
    # Get configuration summary
    config_summary = processor.get_cleaning_config_summary()
    print("Cleaning Configuration Summary:")
    print("=" * 40)
    print(f"Enabled: {'Yes' if config_summary.get('enabled') else 'No'}")
    print(f"Pipeline Order: {', '.join(config_summary.get('pipeline_order', []))}")
    print(f"Cleaners: {config_summary.get('cleaner_count', 0)} total, {config_summary.get('enabled_cleaners', 0)} enabled")
    print(f"Entity Configs: {', '.join(config_summary.get('entity_configs', []))}")
    print(f"Max Operations: {config_summary.get('max_operations', 'unlimited')}")
    print(f"Min Confidence: {config_summary.get('min_confidence', 'none')}")


def list_entity_types(processor: UDNSProcessor):
    """List supported entity types."""
    types = processor.get_supported_entity_types()
    print("Supported Entity Types:")
    print("=" * 30)
    for entity_type in sorted(types):
        print(f"  {entity_type}")
    print(f"\nTotal: {len(types)} entity types")


def validate_examples(processor: UDNSProcessor, quiet: bool = False):
    """Validate implementation against temp.json examples."""
    examples_file = Path("data/temp.json")
    if not examples_file.exists():
        print("Error: temp.json examples file not found", file=sys.stderr)
        return False
    
    with open(examples_file) as f:
        test_data = json.load(f)
    
    if not quiet:
        print("Validating UDNS implementation against examples:")
        print("=" * 50)
    
    domain_mapping = {
        'invoices': EntityType.INVOICE,
        'addresses': EntityType.ADDRESS,
        'contacts': EntityType.CONTACT,
        'products': EntityType.PRODUCT,
        'people': EntityType.PERSON,
    }
    
    total_tests = 0
    passed_tests = 0
    
    for example in test_data['examples']:
        example_id = example['id']
        domain = example['domain']
        input_text = example['input_text']
        
        total_tests += 1
        
        entity_type = domain_mapping.get(domain)
        if not entity_type:
            if not quiet:
                print(f"{example_id}: SKIP (no parser for {domain})")
            continue
        
        try:
            result = processor.process(input_text, entity_type)
            passed_tests += 1
            
            if not quiet:
                print(f"{example_id}: PASS (confidence: {result.metadata.confidence:.2f})")
        
        except Exception as e:
            if not quiet:
                print(f"{example_id}: FAIL ({str(e)})")
    
    success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
    
    if not quiet:
        print("=" * 50)
        print(f"Results: {passed_tests}/{total_tests} passed ({success_rate:.1f}%)")
    
    return success_rate >= 80  # Consider 80%+ success rate as passing


def process_single_text(
    processor: UDNSProcessor,
    text: str,
    entity_type: Optional[EntityType] = None,
    verbose: bool = False,
    quiet: bool = False,
    enable_cleaning: Optional[bool] = None,
    cleaning_config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Process a single text input."""
    if not quiet and verbose:
        log_message(f"Processing: {text[:50]}{'...' if len(text) > 50 else ''}")
        if entity_type:
            log_message(f"Using entity type: {entity_type.value}")
        else:
            log_message("Auto-detecting entity type")
        if enable_cleaning is not None:
            log_message(f"Cleaning: {'enabled' if enable_cleaning else 'disabled'}")
    
    start_time = time.time() if verbose else None
    result = processor.process(text, entity_type, enable_cleaning=enable_cleaning, cleaning_config=cleaning_config)
    duration = time.time() - start_time if start_time else None
    
    if not quiet and verbose:
        log_message(f"Detected type: {result.entity_type.value}")
        log_message(f"Confidence: {result.metadata.confidence:.2f}")
        log_message(f"Attributes: {len(result.attributes)} fields")
        
        # Show cleaning information if available
        if hasattr(result.metadata, 'get_cleaning_summary'):
            cleaning_summary = result.metadata.get_cleaning_summary()
            if cleaning_summary['enabled']:
                log_message(f"Cleaning: {cleaning_summary['operations_count']} operations")
                if cleaning_summary['duration_ms']:
                    log_message(f"Cleaning duration: {cleaning_summary['duration_ms']:.2f}ms")
                if cleaning_summary['errors_count'] > 0:
                    log_message(f"Cleaning errors: {cleaning_summary['errors_count']}")
                if cleaning_summary.get('pipeline_version'):
                    log_message(f"Cleaning pipeline: v{cleaning_summary['pipeline_version']}")
    
    return result.to_dict()


def process_file(
    processor: UDNSProcessor,
    file_path: Path,
    batch: bool = False,
    entity_type: Optional[EntityType] = None,
    verbose: bool = False,
    quiet: bool = False,
    enable_cleaning: Optional[bool] = None,
    cleaning_config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Process a file input."""
    if not file_path.exists():
        raise FileNotFoundError(f"Input file not found: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read().strip()
    
    if batch:
        # Process as JSON batch
        try:
            inputs = json.loads(content)
            if not isinstance(inputs, list):
                raise ValueError("Batch input must be a JSON array")
            
            if not quiet:
                log_message(f"Processing batch of {len(inputs)} inputs")
            
            # Add cleaning configuration to each input
            if enable_cleaning is not None or cleaning_config:
                for input_item in inputs:
                    if enable_cleaning is not None:
                        input_item['enable_cleaning'] = enable_cleaning
                    if cleaning_config:
                        input_item['cleaning_config'] = cleaning_config
            
            results = processor.process_batch(inputs)
            return {"batch_results": results}
            
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in batch file: {e}")
    
    else:
        # Process as single text
        lines = [line.strip() for line in content.split('\n') if line.strip()]
        
        if len(lines) == 1:
            return process_single_text(
                processor, lines[0], entity_type, verbose, quiet,
                enable_cleaning, cleaning_config
            )
        else:
            # Process multiple lines as separate inputs
            results = []
            for i, line in enumerate(lines):
                if not quiet and verbose:
                    log_message(f"Processing line {i+1}/{len(lines)}")
                
                try:
                    result = process_single_text(
                        processor, line, entity_type, verbose, quiet,
                        enable_cleaning, cleaning_config
                    )
                    results.append({"success": True, "line": i+1, "result": result})
                except Exception as e:
                    results.append({"success": False, "line": i+1, "error": str(e)})
            
            return {"multi_line_results": results}


def main():
    """Main CLI function."""
    parser = create_parser()
    args = parser.parse_args()
    
    # Handle special commands
    if args.list_types:
        processor = UDNSProcessor(enable_validation=not args.no_validation)
        list_entity_types(processor)
        return 0
    
    if args.list_cleaners:
        processor = UDNSProcessor(enable_validation=not args.no_validation)
        list_cleaners(processor)
        return 0
    
    if args.list_cleaning_configs:
        processor = UDNSProcessor(enable_validation=not args.no_validation)
        list_cleaning_configs(processor)
        return 0
    
    if args.validate_examples:
        processor = UDNSProcessor(enable_validation=not args.no_validation)
        success = validate_examples(processor, args.quiet)
        return 0 if success else 1
    
    # Initialize processor
    try:
        # Determine cleaning setting
        enable_cleaning = False if args.no_cleaning else (True if args.enable_cleaning else None)
        
        # Load cleaning configuration if provided
        cleaning_config = None
        if args.cleaning_config:
            if not args.cleaning_config.exists():
                print(f"Error: Cleaning configuration file not found: {args.cleaning_config}", file=sys.stderr)
                return 1
            
            try:
                with open(args.cleaning_config, 'r', encoding='utf-8') as f:
                    config_dict = json.load(f)
                    cleaning_config = CleaningConfig.from_dict(config_dict)
            except json.JSONDecodeError as e:
                print(f"Error: Invalid JSON in cleaning configuration file: {e}", file=sys.stderr)
                return 1
        elif args.load_cleaning_config:
            # Load configuration by name
            cleaning_config = args.load_cleaning_config
        
        processor = UDNSProcessor(
            enable_validation=not args.no_validation,
            enable_cleaning=enable_cleaning,
            cleaning_config=cleaning_config
        )
        
        if args.confidence_threshold > 0:
            processor.set_confidence_threshold(args.confidence_threshold)
        
        # Handle configuration updates
        if args.update_cleaner_config:
            for cleaner_name, config_json in args.update_cleaner_config:
                try:
                    config_dict = json.loads(config_json)
                    processor.update_cleaner_config(cleaner_name, **config_dict)
                except json.JSONDecodeError:
                    print(f"Error: Invalid JSON in cleaner config for {cleaner_name}", file=sys.stderr)
                    return 1
        
        if args.update_entity_config:
            for entity_type, config_json in args.update_entity_config:
                try:
                    config_dict = json.loads(config_json)
                    processor.update_entity_config(entity_type, **config_dict)
                except json.JSONDecodeError:
                    print(f"Error: Invalid JSON in entity config for {entity_type}", file=sys.stderr)
                    return 1
        
        # Save configuration if requested
        if args.save_cleaning_config:
            try:
                if cleaning_config:
                    processor.cleaning_pipeline.save_config(args.save_cleaning_config)
                    if not args.quiet:
                        log_message(f"Cleaning configuration saved as '{args.save_cleaning_config}'")
                else:
                    print("Error: No cleaning configuration to save", file=sys.stderr)
                    return 1
            except Exception as e:
                print(f"Error saving cleaning configuration: {e}", file=sys.stderr)
                return 1
    
    except Exception as e:
        print(f"Error initializing processor: {e}", file=sys.stderr)
        return 1
    
    # Parse entity type if provided
    entity_type = None
    if args.type:
        entity_type = EntityType(args.type)
    
    
    # Process input
    try:
        if args.text:
            result = process_single_text(
                processor, args.text, entity_type, args.verbose, args.quiet,
                enable_cleaning=enable_cleaning,
                cleaning_config=cleaning_config.to_dict() if cleaning_config else None
            )
        elif args.file:
            result = process_file(
                processor, args.file, args.batch, entity_type, args.verbose, args.quiet,
                enable_cleaning=enable_cleaning,
                cleaning_config=cleaning_config.to_dict() if cleaning_config else None
            )
        else:
            parser.error("No input specified")
            return 1
        
        # Format output
        if args.pretty:
            output = json.dumps(result, indent=2, ensure_ascii=False)
        else:
            output = json.dumps(result, ensure_ascii=False)
        
        # Write output
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(output)
            
            if not args.quiet:
                log_message(f"Output saved to {args.output}")
        else:
            print(output)
        
        return 0
    
    except Exception as e:
        print(f"Error processing input: {e}", file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())