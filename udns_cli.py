#!/usr/bin/env python3
"""
Command-line interface for UDNS (Universal Data Normalization Specification).
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Optional, Dict, Any
from udns import UDNSProcessor, EntityType


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
    quiet: bool = False
) -> Dict[str, Any]:
    """Process a single text input."""
    if not quiet and verbose:
        log_message(f"Processing: {text[:50]}{'...' if len(text) > 50 else ''}")
        if entity_type:
            log_message(f"Using entity type: {entity_type.value}")
        else:
            log_message("Auto-detecting entity type")
    
    result = processor.process(text, entity_type)
    
    if not quiet and verbose:
        log_message(f"Detected type: {result.entity_type.value}")
        log_message(f"Confidence: {result.metadata.confidence:.2f}")
        log_message(f"Attributes: {len(result.attributes)} fields")
    
    return result.to_dict()


def process_file(
    processor: UDNSProcessor,
    file_path: Path,
    batch: bool = False,
    entity_type: Optional[EntityType] = None,
    verbose: bool = False,
    quiet: bool = False
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
            
            results = processor.process_batch(inputs)
            return {"batch_results": results}
            
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in batch file: {e}")
    
    else:
        # Process as single text
        lines = [line.strip() for line in content.split('\n') if line.strip()]
        
        if len(lines) == 1:
            return process_single_text(processor, lines[0], entity_type, verbose, quiet)
        else:
            # Process multiple lines as separate inputs
            results = []
            for i, line in enumerate(lines):
                if not quiet and verbose:
                    log_message(f"Processing line {i+1}/{len(lines)}")
                
                try:
                    result = process_single_text(processor, line, entity_type, verbose, quiet)
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
    
    if args.validate_examples:
        processor = UDNSProcessor(enable_validation=not args.no_validation)
        success = validate_examples(processor, args.quiet)
        return 0 if success else 1
    
    # Initialize processor
    try:
        processor = UDNSProcessor(enable_validation=not args.no_validation)
        
        if args.confidence_threshold > 0:
            processor.set_confidence_threshold(args.confidence_threshold)
    
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
                processor, args.text, entity_type, args.verbose, args.quiet
            )
        elif args.file:
            result = process_file(
                processor, args.file, args.batch, entity_type, args.verbose, args.quiet
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