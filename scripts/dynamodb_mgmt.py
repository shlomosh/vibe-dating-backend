#!/usr/bin/env python3
"""
DynamoDB Table Dump Script for Vibe Dating App

This script provides a command-line interface for dumping DynamoDB table data
for the Vibe Dating App backend services. It supports dumping entire tables,
specific entities, and various output formats.
"""

import os
import sys
import argparse
import json
import csv
import boto3
from pathlib import Path
from typing import Dict, Any, List, Optional, Generator
from datetime import datetime
from botocore.exceptions import ClientError, NoCredentialsError

# Set AWS profile
os.environ["AWS_PROFILE"] = "vibe-dev"


class DynamoDBDumper:
    """Dumps DynamoDB table data for Vibe Dating App"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.region = os.getenv("AWS_REGION", "il-central-1")
        self.environment = os.getenv("ENVIRONMENT", "dev")
        self.dynamodb = boto3.resource('dynamodb', region_name=self.region)
        self.dynamodb_client = boto3.client('dynamodb', region_name=self.region)
        
        # Table name based on environment
        self.table_name = f"vibe-dating-{self.environment}"
        
        # Entity types for filtering
        self.entity_types = {
            "user": "USER",
            "profile": "PROFILE", 
            "room": "ROOM",
            "message": "MESSAGE",
            "media": "MEDIA",
            "block": "BLOCK",
            "ban": "BAN",
            "location": "LOCATION"
        }
        
    def check_prerequisites(self):
        """Check that all prerequisites are met"""
        print("• Checking prerequisites...")
        
        # Check if boto3 is installed
        try:
            import boto3
            print("• boto3 is available")
        except ImportError:
            print("❌ boto3 is not installed. Please install it first.")
            sys.exit(1)
            
        # Check AWS credentials
        try:
            self.dynamodb_client.list_tables()
            print("• AWS credentials are configured")
        except NoCredentialsError:
            print("❌ AWS credentials not configured. Please run 'aws configure' first.")
            sys.exit(1)
        except Exception as e:
            print(f"❌ AWS credentials error: {e}")
            sys.exit(1)
            
        # Check if table exists
        try:
            table = self.dynamodb.Table(self.table_name)
            table.load()
            print(f"• DynamoDB table '{self.table_name}' exists")
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                print(f"❌ DynamoDB table '{self.table_name}' not found")
                sys.exit(1)
            else:
                print(f"❌ Error accessing table: {e}")
                sys.exit(1)
                
        print("✅ All prerequisites met")
        
    def get_table_info(self) -> Dict[str, Any]:
        """Get table information and statistics"""
        try:
            table = self.dynamodb.Table(self.table_name)
            response = self.dynamodb_client.describe_table(TableName=self.table_name)
            
            # Get table statistics
            stats = {
                "table_name": self.table_name,
                "item_count": response['Table'].get('ItemCount', 0),
                "table_size_bytes": response['Table'].get('TableSizeBytes', 0),
                "billing_mode": response['Table'].get('BillingModeSummary', {}).get('BillingMode', 'UNKNOWN'),
                "creation_date": response['Table'].get('CreationDateTime', '').isoformat() if response['Table'].get('CreationDateTime') else None,
                "status": response['Table'].get('TableStatus', 'UNKNOWN'),
                "gsis": len(response['Table'].get('GlobalSecondaryIndexes', [])),
                "region": self.region,
                "environment": self.environment
            }
            
            return stats
        except ClientError as e:
            print(f"❌ Failed to get table info: {e}")
            return {}
            
    def scan_table(self, entity_type: Optional[str] = None, limit: Optional[int] = None) -> Generator[Dict[str, Any], None, None]:
        """Scan the DynamoDB table with optional filtering"""
        try:
            table = self.dynamodb.Table(self.table_name)
            
            # Build scan parameters
            scan_kwargs = {}
            
            if entity_type:
                # Filter by entity type using PK starts with
                entity_prefix = self.entity_types.get(entity_type.lower(), entity_type.upper())
                scan_kwargs['FilterExpression'] = boto3.dynamodb.conditions.Attr('PK').begins_with(f"{entity_prefix}#")
                
            if limit:
                scan_kwargs['Limit'] = limit
                
            # Scan with pagination
            last_evaluated_key = None
            items_scanned = 0
            
            while True:
                if last_evaluated_key:
                    scan_kwargs['ExclusiveStartKey'] = last_evaluated_key
                    
                response = table.scan(**scan_kwargs)
                
                for item in response.get('Items', []):
                    items_scanned += 1
                    yield item
                    
                    if limit and items_scanned >= limit:
                        return
                        
                last_evaluated_key = response.get('LastEvaluatedKey')
                if not last_evaluated_key:
                    break
                    
        except ClientError as e:
            print(f"❌ Failed to scan table: {e}")
            return
            
    def query_by_entity(self, entity_type: str, entity_id: str) -> List[Dict[str, Any]]:
        """Query specific entity by ID"""
        try:
            table = self.dynamodb.Table(self.table_name)
            entity_prefix = self.entity_types.get(entity_type.lower(), entity_type.upper())
            
            response = table.query(
                KeyConditionExpression='PK = :pk',
                ExpressionAttributeValues={
                    ':pk': f"{entity_prefix}#{entity_id}"
                }
            )
            
            return response.get('Items', [])
            
        except ClientError as e:
            print(f"❌ Failed to query entity: {e}")
            return []
            
    def format_item_for_output(self, item: Dict[str, Any], format_type: str = "json") -> Dict[str, Any]:
        """Format item for different output formats"""
        if format_type == "json":
            return item
        elif format_type == "csv":
            # Flatten nested structures for CSV
            flattened = {}
            for key, value in item.items():
                if isinstance(value, dict):
                    for sub_key, sub_value in value.items():
                        flattened[f"{key}_{sub_key}"] = str(sub_value)
                elif isinstance(value, list):
                    flattened[key] = ", ".join(str(v) for v in value)
                else:
                    flattened[key] = str(value)
            return flattened
        else:
            return item
            
    def save_to_file(self, data: List[Dict[str, Any]], output_file: str, format_type: str = "json"):
        """Save data to file in specified format"""
        try:
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            if format_type == "json":
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, default=str)
                    
            elif format_type == "csv":
                if not data:
                    print("⚠️  No data to save")
                    return
                    
                # Get all possible fields from all items
                all_fields = set()
                for item in data:
                    flattened = self.format_item_for_output(item, "csv")
                    all_fields.update(flattened.keys())
                    
                with open(output_path, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=sorted(all_fields))
                    writer.writeheader()
                    
                    for item in data:
                        flattened = self.format_item_for_output(item, "csv")
                        writer.writerow(flattened)
                        
            print(f"✅ Data saved to {output_path}")
            
        except Exception as e:
            print(f"❌ Failed to save data: {e}")
            
    def dump_entire_table(self, output_file: str, format_type: str = "json", limit: Optional[int] = None):
        """Dump entire table"""
        print(f"📊 Dumping entire table '{self.table_name}'...")
        
        items = []
        for item in self.scan_table(limit=limit):
            formatted_item = self.format_item_for_output(item, format_type)
            items.append(formatted_item)
            
            if len(items) % 100 == 0:
                print(f"• Scanned {len(items)} items...")
                
        print(f"✅ Scanned {len(items)} items total")
        
        if output_file:
            self.save_to_file(items, output_file, format_type)
        else:
            # Print to stdout
            if format_type == "json":
                print(json.dumps(items, indent=2, default=str))
            else:
                # For CSV, print first few items as preview
                print(f"Preview of first 5 items:")
                for i, item in enumerate(items[:5]):
                    print(f"Item {i+1}: {item}")
                    
    def dump_entity_type(self, entity_type: str, output_file: str, format_type: str = "json", limit: Optional[int] = None):
        """Dump specific entity type"""
        if entity_type.lower() not in self.entity_types:
            print(f"❌ Unknown entity type: {entity_type}")
            print(f"Available types: {', '.join(self.entity_types.keys())}")
            return
            
        print(f"📊 Dumping {entity_type} entities from table '{self.table_name}'...")
        
        items = []
        for item in self.scan_table(entity_type=entity_type, limit=limit):
            formatted_item = self.format_item_for_output(item, format_type)
            items.append(formatted_item)
            
            if len(items) % 50 == 0:
                print(f"• Scanned {len(items)} {entity_type} items...")
                
        print(f"✅ Scanned {len(items)} {entity_type} items total")
        
        if output_file:
            self.save_to_file(items, output_file, format_type)
        else:
            # Print to stdout
            if format_type == "json":
                print(json.dumps(items, indent=2, default=str))
            else:
                # For CSV, print first few items as preview
                print(f"Preview of first 5 {entity_type} items:")
                for i, item in enumerate(items[:5]):
                    print(f"Item {i+1}: {item}")
                    
    def dump_specific_entity(self, entity_type: str, entity_id: str, output_file: str, format_type: str = "json"):
        """Dump specific entity by ID"""
        if entity_type.lower() not in self.entity_types:
            print(f"❌ Unknown entity type: {entity_type}")
            print(f"Available types: {', '.join(self.entity_types.keys())}")
            return
            
        print(f"📊 Dumping {entity_type} entity '{entity_id}' from table '{self.table_name}'...")
        
        items = self.query_by_entity(entity_type, entity_id)
        
        if not items:
            print(f"⚠️  No {entity_type} entity found with ID: {entity_id}")
            return
            
        formatted_items = []
        for item in items:
            formatted_item = self.format_item_for_output(item, format_type)
            formatted_items.append(formatted_item)
            
        print(f"✅ Found {len(formatted_items)} items for {entity_type} '{entity_id}'")
        
        if output_file:
            self.save_to_file(formatted_items, output_file, format_type)
        else:
            # Print to stdout
            if format_type == "json":
                print(json.dumps(formatted_items, indent=2, default=str))
            else:
                # For CSV, print items as preview
                print(f"Preview of {entity_type} items:")
                for i, item in enumerate(formatted_items):
                    print(f"Item {i+1}: {item}")
                    
    def list_entity_counts(self):
        """List count of each entity type"""
        print(f"📊 Entity counts for table '{self.table_name}':")
        print("-" * 50)
        
        total_items = 0
        for entity_name, entity_prefix in self.entity_types.items():
            count = 0
            for _ in self.scan_table(entity_type=entity_name):
                count += 1
            print(f"{entity_name.capitalize():<12}: {count:>6} items")
            total_items += count
            
        print("-" * 50)
        print(f"{'Total':<12}: {total_items:>6} items")
        
    def export_table_schema(self, output_file: str = None):
        """Export table schema information"""
        try:
            response = self.dynamodb_client.describe_table(TableName=self.table_name)
            table_info = response['Table']
            
            schema = {
                "table_name": self.table_name,
                "region": self.region,
                "environment": self.environment,
                "exported_at": datetime.now().isoformat(),
                "table_info": {
                    "billing_mode": table_info.get('BillingModeSummary', {}).get('BillingMode'),
                    "item_count": table_info.get('ItemCount'),
                    "table_size_bytes": table_info.get('TableSizeBytes'),
                    "creation_date": table_info.get('CreationDateTime', '').isoformat() if table_info.get('CreationDateTime') else None,
                    "status": table_info.get('TableStatus'),
                    "point_in_time_recovery": table_info.get('PointInTimeRecoveryDescription', {}).get('PointInTimeRecoveryStatus')
                },
                "key_schema": table_info.get('KeySchema'),
                "attribute_definitions": table_info.get('AttributeDefinitions'),
                "global_secondary_indexes": table_info.get('GlobalSecondaryIndexes', []),
                "local_secondary_indexes": table_info.get('LocalSecondaryIndexes', []),
                "sse_description": table_info.get('SSEDescription')
            }
            
            if output_file:
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(schema, f, indent=2, default=str)
                print(f"✅ Schema exported to {output_file}")
            else:
                print(json.dumps(schema, indent=2, default=str))
                
        except ClientError as e:
            print(f"❌ Failed to export schema: {e}")


def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description="DynamoDB Management Script for Vibe Dating App",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Dump entire table to JSON file
  python scripts/dynamodb_dump.py dump --output data/table_dump.json

  # Dump only user entities to CSV
  python scripts/dynamodb_dump.py dump --entity-type user --format csv --output data/users.csv

  # Dump specific user by ID
  python scripts/dynamodb_dump.py dump --entity-type user --entity-id "user123" --output data/user123.json

  # List entity counts
  python scripts/dynamodb_dump.py counts

  # Export table schema
  python scripts/dynamodb_dump.py schema --output data/schema.json

  # Get table info
  python scripts/dynamodb_dump.py info
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Dump command
    dump_parser = subparsers.add_parser('dump', help='Dump table data')
    dump_parser.add_argument('--entity-type', choices=['user', 'profile', 'room', 'message', 'media', 'block', 'ban', 'location'], 
                           help='Filter by entity type')
    dump_parser.add_argument('--entity-id', help='Specific entity ID to dump')
    dump_parser.add_argument('--output', help='Output file path')
    dump_parser.add_argument('--format', choices=['json', 'csv'], default='json', help='Output format')
    dump_parser.add_argument('--limit', type=int, help='Limit number of items to scan')
    
    # Counts command
    subparsers.add_parser('counts', help='List entity counts')
    
    # Schema command
    schema_parser = subparsers.add_parser('schema', help='Export table schema')
    schema_parser.add_argument('--output', help='Output file path')
    
    # Info command
    subparsers.add_parser('info', help='Show table information')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
        
    # Initialize dumper
    dumper = DynamoDBDumper()
    dumper.check_prerequisites()
    
    if args.command == 'dump':
        if args.entity_id and args.entity_type:
            # Dump specific entity
            dumper.dump_specific_entity(args.entity_type, args.entity_id, args.output, args.format)
        elif args.entity_type:
            # Dump entity type
            dumper.dump_entity_type(args.entity_type, args.output, args.format, args.limit)
        else:
            # Dump entire table
            dumper.dump_entire_table(args.output, args.format, args.limit)
            
    elif args.command == 'counts':
        dumper.list_entity_counts()
        
    elif args.command == 'schema':
        dumper.export_table_schema(args.output)
        
    elif args.command == 'info':
        info = dumper.get_table_info()
        if info:
            print("📊 Table Information:")
            print("-" * 40)
            for key, value in info.items():
                if key == "table_size_bytes":
                    size_mb = value / (1024 * 1024)
                    print(f"{key:<20}: {size_mb:.2f} MB")
                else:
                    print(f"{key:<20}: {value}")


if __name__ == "__main__":
    main() 