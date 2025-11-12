#!/usr/bin/env python3
"""
Enterprise Immutable Audit Log Backfill Script

Purpose: Migrate existing user_audit_logs to immutable_audit_logs with hash-chaining

Features:
- Reads from user_audit_logs table (if exists)
- Transforms to immutable audit format
- Calculates retroactive hash chains
- Inserts with proper sequence numbers
- Verifies hash chain integrity after backfill
- Works in both production and local environments

Usage:
    python scripts/database/backfill_immutable_audit_logs.py [--dry-run] [--batch-size 1000]

Environment Variables:
    DATABASE_URL - PostgreSQL connection string
"""

import sys
import os
import hashlib
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import argparse

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from config import DATABASE_URL


class AuditLogBackfill:
    """Handles backfilling of historical audit logs to immutable format."""

    def __init__(self, db_url: str, dry_run: bool = False, batch_size: int = 1000):
        self.db_url = db_url
        self.dry_run = dry_run
        self.batch_size = batch_size
        self.engine = create_engine(db_url)
        self.Session = sessionmaker(bind=self.engine)

    def calculate_content_hash(self, record: Dict) -> str:
        """Calculate SHA-256 hash of record content."""
        # Create consistent string representation
        content = json.dumps({
            'timestamp': record['timestamp'].isoformat() if isinstance(record['timestamp'], datetime) else str(record['timestamp']),
            'event_type': record['event_type'],
            'actor_id': record['actor_id'],
            'resource_type': record['resource_type'],
            'resource_id': record['resource_id'],
            'action': record['action'],
            'event_data': record['event_data'],
        }, sort_keys=True)

        return hashlib.sha256(content.encode()).hexdigest()

    def calculate_chain_hash(self, content_hash: str, previous_hash: Optional[str]) -> str:
        """Calculate cumulative chain hash."""
        if previous_hash:
            combined = f"{previous_hash}{content_hash}"
        else:
            combined = content_hash

        return hashlib.sha256(combined.encode()).hexdigest()

    def check_source_table_exists(self) -> bool:
        """Check if user_audit_logs table exists."""
        with self.engine.connect() as conn:
            result = conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_name = 'user_audit_logs'
                );
            """))
            return result.scalar()

    def fetch_historical_logs(self) -> List[Dict]:
        """Fetch all historical logs from user_audit_logs."""
        print("📊 Fetching historical audit logs...")

        with self.engine.connect() as conn:
            result = conn.execute(text("""
                SELECT
                    id,
                    user_id,
                    action,
                    details,
                    ip_address,
                    timestamp,
                    risk_level,
                    session_id
                FROM user_audit_logs
                ORDER BY timestamp ASC
            """))

            logs = []
            for row in result:
                logs.append({
                    'original_id': row[0],
                    'user_id': row[1],
                    'action': row[2],
                    'details': row[3] if row[3] else '{}',
                    'ip_address': row[4],
                    'timestamp': row[5],
                    'risk_level': row[6] if row[6] else 'Medium',
                    'session_id': row[7],
                })

        print(f"✅ Found {len(logs)} historical audit logs")
        return logs

    def transform_to_immutable_format(self, old_logs: List[Dict]) -> List[Dict]:
        """Transform old audit logs to immutable format with hash-chaining."""
        print("🔄 Transforming logs to immutable format with hash-chaining...")

        immutable_logs = []
        previous_hash = None

        for idx, log in enumerate(old_logs, start=1):
            # Parse details JSON
            try:
                details = json.loads(log['details']) if isinstance(log['details'], str) else log['details']
            except json.JSONDecodeError:
                details = {'raw_details': log['details']}

            # Extract event components
            event_type = self._classify_event_type(log['action'])
            resource_type, resource_id = self._extract_resource_info(log['action'], details)

            # Build immutable record
            record = {
                'sequence_number': idx,
                'timestamp': log['timestamp'],
                'source_system': 'ow-ai',
                'event_type': event_type,
                'actor_id': str(log['user_id']),
                'resource_type': resource_type,
                'resource_id': resource_id,
                'action': log['action'],
                'event_data': json.dumps(details),
                'risk_level': log['risk_level'],
                'compliance_tags': json.dumps(self._determine_compliance_tags(event_type)),
                'ip_address': log['ip_address'],
                'session_id': log['session_id'],
            }

            # Calculate hashes
            content_hash = self.calculate_content_hash(record)
            chain_hash = self.calculate_chain_hash(content_hash, previous_hash)

            record['content_hash'] = content_hash
            record['previous_hash'] = previous_hash
            record['chain_hash'] = chain_hash

            # Determine retention period
            record['retention_until'] = self._calculate_retention_date(
                log['timestamp'],
                self._determine_compliance_tags(event_type)
            )

            immutable_logs.append(record)
            previous_hash = chain_hash

            if idx % 100 == 0:
                print(f"  Processed {idx}/{len(old_logs)} logs...")

        print(f"✅ Transformed {len(immutable_logs)} logs with hash-chaining")
        return immutable_logs

    def _classify_event_type(self, action: str) -> str:
        """Classify action into event type categories."""
        action_lower = action.lower()

        if any(word in action_lower for word in ['login', 'logout', 'auth']):
            return 'authentication'
        elif any(word in action_lower for word in ['create', 'add', 'insert']):
            return 'create'
        elif any(word in action_lower for word in ['update', 'modify', 'edit', 'change']):
            return 'update'
        elif any(word in action_lower for word in ['delete', 'remove']):
            return 'delete'
        elif any(word in action_lower for word in ['view', 'read', 'access', 'fetch']):
            return 'read'
        elif any(word in action_lower for word in ['approve', 'reject', 'authorize']):
            return 'authorization'
        else:
            return 'other'

    def _extract_resource_info(self, action: str, details: Dict) -> tuple:
        """Extract resource type and ID from action and details."""
        action_lower = action.lower()

        # Try to extract from action string
        if 'user' in action_lower:
            resource_type = 'user'
        elif 'policy' in action_lower:
            resource_type = 'policy'
        elif 'alert' in action_lower:
            resource_type = 'alert'
        elif 'rule' in action_lower:
            resource_type = 'rule'
        elif 'action' in action_lower:
            resource_type = 'agent_action'
        else:
            resource_type = 'system'

        # Try to extract resource ID from details
        resource_id = details.get('resource_id') or details.get('id') or details.get('user_id') or 'unknown'

        return resource_type, str(resource_id)

    def _determine_compliance_tags(self, event_type: str) -> List[str]:
        """Determine which compliance frameworks apply to this event."""
        tags = []

        # All authentication events need SOX and HIPAA compliance
        if event_type == 'authentication':
            tags.extend(['SOX', 'HIPAA', 'PCI-DSS'])

        # Authorization and access control
        if event_type == 'authorization':
            tags.extend(['SOX', 'HIPAA', 'GDPR'])

        # Data modifications
        if event_type in ['create', 'update', 'delete']:
            tags.extend(['SOX', 'GDPR', 'CCPA'])

        # Data access
        if event_type == 'read':
            tags.extend(['HIPAA', 'GDPR', 'CCPA', 'FERPA'])

        # Always include SOX for financial compliance
        if 'SOX' not in tags:
            tags.append('SOX')

        return list(set(tags))  # Remove duplicates

    def _calculate_retention_date(self, timestamp: datetime, compliance_tags: List[str]) -> datetime:
        """Calculate retention date based on compliance requirements."""
        # SOX: 7 years
        # HIPAA: 6 years
        # PCI-DSS: 1 year
        # Default: 7 years (most stringent)

        retention_years = 7  # Default to SOX requirement

        if 'SOX' in compliance_tags:
            retention_years = max(retention_years, 7)
        if 'HIPAA' in compliance_tags:
            retention_years = max(retention_years, 6)
        if 'PCI-DSS' in compliance_tags and retention_years < 1:
            retention_years = 1

        return timestamp + timedelta(days=365 * retention_years)

    def insert_immutable_logs(self, logs: List[Dict]):
        """Insert transformed logs into immutable_audit_logs table."""
        if self.dry_run:
            print(f"🧪 DRY RUN: Would insert {len(logs)} records")
            print(f"   Sample record:")
            if logs:
                print(f"   {json.dumps(logs[0], indent=4, default=str)}")
            return

        print(f"💾 Inserting {len(logs)} immutable audit logs...")

        with self.engine.connect() as conn:
            # Begin transaction
            trans = conn.begin()

            try:
                # Batch insert
                for i in range(0, len(logs), self.batch_size):
                    batch = logs[i:i + self.batch_size]

                    for log in batch:
                        conn.execute(text("""
                            INSERT INTO immutable_audit_logs (
                                sequence_number, timestamp, source_system,
                                event_type, actor_id, resource_type, resource_id,
                                action, event_data, risk_level, compliance_tags,
                                content_hash, previous_hash, chain_hash,
                                retention_until, ip_address, session_id
                            ) VALUES (
                                :sequence_number, :timestamp, :source_system,
                                :event_type, :actor_id, :resource_type, :resource_id,
                                :action, :event_data::jsonb, :risk_level, :compliance_tags::jsonb,
                                :content_hash, :previous_hash, :chain_hash,
                                :retention_until, :ip_address, :session_id
                            )
                        """), log)

                    print(f"  Inserted batch {i // self.batch_size + 1}/{(len(logs) - 1) // self.batch_size + 1}")

                # Commit transaction
                trans.commit()
                print(f"✅ Successfully inserted {len(logs)} immutable audit logs")

            except Exception as e:
                trans.rollback()
                print(f"❌ Error inserting logs: {e}")
                raise

    def verify_hash_chain_integrity(self) -> Dict:
        """Verify hash chain integrity after backfill."""
        print("🔍 Verifying hash chain integrity...")

        with self.engine.connect() as conn:
            result = conn.execute(text("""
                SELECT
                    sequence_number,
                    content_hash,
                    previous_hash,
                    chain_hash
                FROM immutable_audit_logs
                ORDER BY sequence_number ASC
            """))

            logs = list(result)
            total_records = len(logs)
            broken_chains = []
            previous_chain_hash = None

            for row in logs:
                seq, content_hash, previous_hash, chain_hash = row

                # Verify chain hash calculation
                expected_chain_hash = self.calculate_chain_hash(content_hash, previous_hash)

                if chain_hash != expected_chain_hash:
                    broken_chains.append({
                        'sequence_number': seq,
                        'expected': expected_chain_hash,
                        'actual': chain_hash
                    })

                # Verify previous_hash matches previous record's chain_hash
                if seq > 1 and previous_hash != previous_chain_hash:
                    broken_chains.append({
                        'sequence_number': seq,
                        'issue': 'previous_hash mismatch',
                        'expected': previous_chain_hash,
                        'actual': previous_hash
                    })

                previous_chain_hash = chain_hash

        if broken_chains:
            print(f"❌ Found {len(broken_chains)} broken chain links!")
            for broken in broken_chains[:5]:  # Show first 5
                print(f"   Sequence {broken['sequence_number']}: {broken}")
        else:
            print(f"✅ Hash chain integrity verified - all {total_records} records valid")

        return {
            'total_records': total_records,
            'broken_chains': len(broken_chains),
            'status': 'VALID' if not broken_chains else 'BROKEN'
        }

    def run(self):
        """Execute the full backfill process."""
        print("="*60)
        print("🏢 ENTERPRISE IMMUTABLE AUDIT LOG BACKFILL")
        print("="*60)
        print(f"Database: {self.db_url.split('@')[1] if '@' in self.db_url else 'local'}")
        print(f"Dry Run: {self.dry_run}")
        print(f"Batch Size: {self.batch_size}")
        print("")

        # Step 1: Check if source table exists
        if not self.check_source_table_exists():
            print("⚠️  Source table 'user_audit_logs' does not exist")
            print("   This is normal for clean environments")
            print("   Skipping backfill - no historical data to migrate")
            return

        # Step 2: Fetch historical logs
        historical_logs = self.fetch_historical_logs()

        if not historical_logs:
            print("ℹ️  No historical logs found - nothing to backfill")
            return

        # Step 3: Transform to immutable format
        immutable_logs = self.transform_to_immutable_format(historical_logs)

        # Step 4: Insert into immutable_audit_logs
        self.insert_immutable_logs(immutable_logs)

        # Step 5: Verify hash chain integrity
        if not self.dry_run:
            integrity_result = self.verify_hash_chain_integrity()

            print("")
            print("="*60)
            print("📊 BACKFILL COMPLETE")
            print("="*60)
            print(f"Total Records Migrated: {len(immutable_logs)}")
            print(f"Hash Chain Status: {integrity_result['status']}")
            print(f"Broken Chains: {integrity_result['broken_chains']}")
            print("")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Backfill immutable audit logs')
    parser.add_argument('--dry-run', action='store_true', help='Perform dry run without inserting data')
    parser.add_argument('--batch-size', type=int, default=1000, help='Batch size for inserts')

    args = parser.parse_args()

    try:
        backfill = AuditLogBackfill(
            db_url=DATABASE_URL,
            dry_run=args.dry_run,
            batch_size=args.batch_size
        )
        backfill.run()

    except Exception as e:
        print(f"❌ Backfill failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
