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
import random
import string
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
            "media": "MEDIA",
            "location": "LOCATION"
        }

    def check_prerequisites(self):
        """Check that all prerequisites are met"""

        # Check if boto3 is installed
        try:
            import boto3
        except ImportError:
            print("❌ boto3 is not installed. Please install it first.")
            sys.exit(1)

        # Check AWS credentials
        try:
            self.dynamodb_client.list_tables()
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
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                print(f"❌ DynamoDB table '{self.table_name}' not found")
                sys.exit(1)
            else:
                print(f"❌ Error accessing table: {e}")
                sys.exit(1)

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

    def debug_console(self):
        """Console log table data"""
        table = self.dynamodb.Table(self.table_name)
        from IPython import embed; embed(banner1="\nAccess dynamodb table using 'table' variable\n")

    def truncate_table(self, entity_type: Optional[str] = None, force: bool = False):
        """Truncate (delete all items) from the table"""
        try:
            table = self.dynamodb.Table(self.table_name)

            if not force:
                # Get item count for confirmation
                if entity_type:
                    count = sum(1 for _ in self.scan_table(entity_type=entity_type))
                    entity_desc = f"{entity_type} entities"
                else:
                    count = sum(1 for _ in self.scan_table())
                    entity_desc = "all entities"

                print(f"⚠️  WARNING: This will delete {count} {entity_desc} from table '{self.table_name}'")
                print("This action cannot be undone!")

                random_string = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
                confirm = input(f"Type '{random_string}' to confirm: ")
                if confirm != random_string:
                    print("❌ Truncate cancelled")
                    return

            print(f"🗑️  Truncating {entity_desc if entity_type else 'all items'} from table '{self.table_name}'...")

            # Build scan parameters for deletion
            scan_kwargs = {}
            if entity_type:
                entity_prefix = self.entity_types.get(entity_type.lower(), entity_type.upper())
                scan_kwargs['FilterExpression'] = boto3.dynamodb.conditions.Attr('PK').begins_with(f"{entity_prefix}#")

            # Delete items in batches
            deleted_count = 0
            last_evaluated_key = None

            while True:
                if last_evaluated_key:
                    scan_kwargs['ExclusiveStartKey'] = last_evaluated_key

                # Scan for items to delete
                response = table.scan(**scan_kwargs)
                items_to_delete = response.get('Items', [])

                if not items_to_delete:
                    break

                # Delete items in batch
                with table.batch_writer() as batch:
                    for item in items_to_delete:
                        batch.delete_item(
                            Key={
                                'PK': item['PK'],
                                'SK': item['SK']
                            }
                        )
                        deleted_count += 1

                print(f"• Deleted {deleted_count} items...")

                last_evaluated_key = response.get('LastEvaluatedKey')
                if not last_evaluated_key:
                    break

            print(f"✅ Successfully deleted {deleted_count} items from table '{self.table_name}'")

        except ClientError as e:
            print(f"❌ Failed to truncate table: {e}")
        except KeyboardInterrupt:
            print("\n❌ Truncate operation cancelled by user")
        except Exception as e:
            print(f"❌ Unexpected error during truncate: {e}")

    def dump_as_tree(self, output_file: str = None, limit: Optional[int] = None):
        """Dump database as hierarchical tree showing user->profile->media relationships"""
        print(f"🌳 Building hierarchical tree from table '{self.table_name}'...")

        # Collect all data organized by relationships
        users = {}
        profiles = {}
        media_items = {}

        # First pass: collect all entities
        print("• Scanning users...")
        user_count = 0
        for item in self.scan_table(entity_type="user", limit=limit):
            # Only process user metadata items, not profile references
            if item.get('SK') == 'METADATA':
                user_id = item.get('PK', '').replace('USER#', '')
                if user_id:
                    users[user_id] = {
                        'id': user_id,
                        'email': item.get('platformMetadata', {}).get('username', 'N/A'),
                        'platform': item.get('platform', 'N/A'),
                        'created_at': item.get('createdAt', 'N/A'),
                        'status': item.get('status', 'N/A')
                    }
                    user_count += 1

        print("• Scanning profiles...")
        profile_count = 0

        # First, collect all profile data
        all_profiles = {}
        for item in self.scan_table(entity_type="profile"):
            profile_id = item.get('PK', '').replace('PROFILE#', '')
            if profile_id:
                all_profiles[profile_id] = item

        # Then, scan for user-profile lookup items to establish relationships
        for item in self.scan_table():
            if item.get('SK', '').startswith('PROFILE#'):
                user_id = item.get('PK', '').replace('USER#', '')
                profile_id = item.get('profileId', '')

                if user_id and profile_id and profile_id in all_profiles:
                    profile_data = all_profiles[profile_id]
                    if user_id not in profiles:
                        profiles[user_id] = []
                    profiles[user_id].append({
                        'id': profile_id,
                        'name': profile_data.get('nickName', 'N/A'),
                        'age': profile_data.get('age', 'N/A'),
                        'location': profile_data.get('location', 'N/A'),
                        'position': profile_data.get('sexualPosition', 'N/A')
                    })
                    profile_count += 1

        print("• Scanning media...")
        media_count = 0
        for item in self.scan_table():
            if item.get('SK', '').startswith('MEDIA#'):
                profile_id = item.get('PK', '').replace('PROFILE#', '')
                media_id = item.get('SK', '').replace('MEDIA#', '')
                if profile_id and media_id:
                    if profile_id not in media_items:
                        media_items[profile_id] = []
                    media_items[profile_id].append({
                        'id': media_id,
                        'type': item.get('mediaType', 'N/A'),
                        'status': item.get('status', 'N/A'),
                        's3_key': item.get('s3Key', 'N/A'),
                        'created_at': item.get('createdAt', 'N/A')
                    })
                    media_count += 1

        print(f"✅ Collected {user_count} users, {profile_count} profiles, {media_count} media items")

        # Build tree structure
        tree_data = []
        for user_id, user_data in users.items():
            user_node = {
                'type': 'USER',
                'data': user_data,
                'profiles': []
            }

            # Add profiles for this user
            user_profiles = profiles.get(user_id, [])
            for profile_data in user_profiles:
                profile_node = {
                    'type': 'PROFILE',
                    'data': profile_data,
                    'media': []
                }

                # Add media for this profile
                profile_media = media_items.get(profile_data['id'], [])
                for media_data in profile_media:
                    media_node = {
                        'type': 'MEDIA',
                        'data': media_data
                    }
                    profile_node['media'].append(media_node)

                user_node['profiles'].append(profile_node)

            tree_data.append(user_node)

        # Output the tree
        if output_file:
            self._save_tree_to_file(tree_data, output_file)
        else:
            self._print_tree_to_console(tree_data)

    def _print_tree_to_console(self, tree_data: List[Dict[str, Any]]):
        """Print tree structure to console"""
        print(f"\n🌳 Database Tree Structure ({len(tree_data)} users):")
        print("=" * 80)

        for user_node in tree_data:
            user = user_node['data']
            print(f"⚪ USER: {user['id']} ({user['email']} @ {user['platform']}, status: {user['status']})")

            profiles = user_node.get('profiles', [])
            for i, profile_node in enumerate(profiles):
                is_last_profile = i == len(profiles) - 1
                profile = profile_node['data']
                profile_prefix = "└── " if is_last_profile else "├── "
                print(f"   {profile_prefix}𖦹 PROFILE: {profile['id']} - {profile['name']} (age: {profile['age']}, position: {profile['position']})")

                media_items = profile_node.get('media', [])
                for j, media_node in enumerate(media_items):
                    is_last_media = j == len(media_items) - 1
                    media = media_node['data']

                    if is_last_profile:
                        media_prefix = "    └── " if is_last_media else "    ├── "
                    else:
                        media_prefix = "│   └── " if is_last_media else "│   ├── "

                    print(f"   {media_prefix}🖼️  MEDIA: {media['id']} - {media['type']} - {media['status']}")

            print()  # Empty line between users

    def _save_tree_to_file(self, tree_data: List[Dict[str, Any]], output_file: str):
        """Save tree structure to JSON file"""
        try:
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(tree_data, f, indent=2, default=str)

            print(f"✅ Tree structure saved to {output_path}")
        except Exception as e:
            print(f"❌ Failed to save tree structure: {e}")

def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description="DynamoDB Management Script for Vibe Dating App",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Dump entire table to JSON file
  python scripts/dynamodb_mgmt.py dump --output data/table_dump.json

  # Dump only user entities to CSV
  python scripts/dynamodb_mgmt.py dump --entity-type user --format csv --output data/users.csv

  # Dump specific user by ID
  python scripts/dynamodb_mgmt.py dump --entity-type user --entity-id "user123" --output data/user123.json

  # List entity counts
  python scripts/dynamodb_mgmt.py counts

  # Export table schema
  python scripts/dynamodb_mgmt.py schema --output data/schema.json

  # Get table info
  python scripts/dynamodb_mgmt.py info

  # Start interactive debug console
  python scripts/dynamodb_mgmt.py debug

  # Truncate all data (with confirmation)
  python scripts/dynamodb_mgmt.py truncate

  # Truncate only user entities
  python scripts/dynamodb_mgmt.py truncate --entity-type user

  # Truncate without confirmation (dangerous!)
  python scripts/dynamodb_mgmt.py truncate --force

  # Dump database as hierarchical tree
  python scripts/dynamodb_mgmt.py dump-as-tree

  # Dump tree structure to file (limited to 10 users)
  python scripts/dynamodb_mgmt.py dump-as-tree --limit 10 --output data/tree.json
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Dump command
    dump_parser = subparsers.add_parser('dump', help='Dump table data')
    dump_parser.add_argument('--entity-type', choices=['user', 'profile', 'media', 'location'], help='Filter by entity type')
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

    # Debug command
    subparsers.add_parser('debug', help='Start interactive debug console')

    # Tree command
    tree_parser = subparsers.add_parser('dump-as-tree', help='Dump database as hierarchical tree (user->profile->media)')
    tree_parser.add_argument('--limit', type=int, help='Limit number of users to process')
    tree_parser.add_argument('--output', help='Output file path')

    # Truncate command
    truncate_parser = subparsers.add_parser('truncate', help='Delete all items from table (use with caution!)')
    truncate_parser.add_argument('--entity-type', choices=['user', 'profile', 'media', 'location'], help='Delete only specific entity type')
    truncate_parser.add_argument('--force', action='store_true', help='Skip confirmation prompt (use with extreme caution!)')

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

    elif args.command == 'info' or args.command == 'debug':
        info = dumper.get_table_info()
        if info:
            print("-" * 40)
            for key, value in info.items():
                if key == "table_size_bytes":
                    size_mb = value / (1024 * 1024)
                    print(f"{key:<20}: {size_mb:.2f} MB")
                else:
                    print(f"{key:<20}: {value}")
            print("-" * 40)

        if args.command == 'debug':
            dumper.debug_console()

    elif args.command == 'dump-as-tree':
        dumper.dump_as_tree(args.output, args.limit)

    elif args.command == 'truncate':
        dumper.truncate_table(args.entity_type, args.force)

if __name__ == "__main__":
    main()
