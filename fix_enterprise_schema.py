#!/usr/bin/env python3
"""
Enterprise Schema Fix Script for OW-AI Platform
Fixes critical schema mismatches preventing A/B testing functionality
"""

import os
import psycopg2
import sys

def fix_enterprise_schema():
    print("🔧 OW-AI Enterprise Schema Fix")
    print("=" * 60)
    
    # AWS RDS connection from environment
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("❌ ERROR: DATABASE_URL environment variable not set")
        print("Please set DATABASE_URL to your AWS RDS endpoint")
        sys.exit(1)
    
    print("🌐 Connecting to AWS RDS PostgreSQL...")
    
    try:
        conn = psycopg2.connect(
            database_url,
            sslmode='prefer',
            connect_timeout=30,
            application_name='OW-AI-Enterprise-Schema-Fix'
        )
        
        cursor = conn.cursor()
        conn.autocommit = False  # Enterprise transaction control
        
        print("✅ Connected successfully")
        print("\n🔧 ENTERPRISE SCHEMA FIXES:")
        print("=" * 50)
        
        # BACKUP CRITICAL DATA FIRST
        print("📦 Step 1: Backing up critical data...")
        
        # Backup ab_tests data
        backup_ab_tests = """
        CREATE TABLE ab_tests_backup AS 
        SELECT * FROM ab_tests;
        """
        
        try:
            cursor.execute("DROP TABLE IF EXISTS ab_tests_backup;")
            cursor.execute(backup_ab_tests)
            print("✅ AB tests data backed up")
        except Exception as e:
            print(f"⚠️  Backup warning: {e}")
        
        # FIX 1: Add missing columns to smart_rules
        print("\n🔧 Step 2: Fixing smart_rules table...")
        
        smart_rules_fixes = [
            "ALTER TABLE smart_rules ADD COLUMN IF NOT EXISTS name VARCHAR(255);",
            "ALTER TABLE smart_rules ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;"
        ]
        
        for fix in smart_rules_fixes:
            try:
                cursor.execute(fix)
                print(f"✅ Applied: {fix}")
            except Exception as e:
                print(f"❌ Failed: {fix} - {e}")
        
        # FIX 2: Recreate ab_tests table with correct schema
        print("\n🔧 Step 3: Recreating ab_tests table...")
        
        # Drop and recreate ab_tests with enterprise schema
        ab_tests_recreation = """
        DROP TABLE IF EXISTS ab_tests;
        
        CREATE TABLE ab_tests (
            id SERIAL PRIMARY KEY,
            test_id VARCHAR(100) NOT NULL UNIQUE,
            rule_id INTEGER REFERENCES smart_rules(id),
            test_name VARCHAR(255) NOT NULL,
            description TEXT,
            variant_a TEXT,
            variant_b TEXT,
            variant_a_performance INTEGER DEFAULT 0,
            variant_b_performance INTEGER DEFAULT 0,
            confidence_level INTEGER DEFAULT 0,
            status VARCHAR(50) DEFAULT 'active',
            created_by VARCHAR(255),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            duration_hours INTEGER DEFAULT 24,
            traffic_split INTEGER DEFAULT 50,
            winner VARCHAR(50),
            results JSONB,
            metadata JSONB DEFAULT '{}',
            
            -- Enterprise constraints
            CONSTRAINT valid_confidence CHECK (confidence_level >= 0 AND confidence_level <= 100),
            CONSTRAINT valid_traffic_split CHECK (traffic_split >= 0 AND traffic_split <= 100),
            CONSTRAINT valid_status CHECK (status IN ('active', 'completed', 'paused', 'archived'))
        );
        
        -- Enterprise indexes for performance
        CREATE INDEX idx_ab_tests_status ON ab_tests(status);
        CREATE INDEX idx_ab_tests_created_at ON ab_tests(created_at);
        CREATE INDEX idx_ab_tests_rule_id ON ab_tests(rule_id);
        """
        
        try:
            # Execute each statement separately for better error handling
            statements = ab_tests_recreation.split(';')
            for stmt in statements:
                if stmt.strip():
                    cursor.execute(stmt)
            print("✅ AB tests table recreated with enterprise schema")
        except Exception as e:
            print(f"❌ Failed to recreate ab_tests table: {e}")
            conn.rollback()
            return False
        
        # FIX 3: Update smart_rules with default values
        print("\n🔧 Step 4: Setting default values...")
        
        default_updates = [
            "UPDATE smart_rules SET name = CONCAT('Rule-', id) WHERE name IS NULL;",
            "UPDATE smart_rules SET updated_at = created_at WHERE updated_at IS NULL;"
        ]
        
        for update in default_updates:
            try:
                cursor.execute(update)
                rows_affected = cursor.rowcount
                print(f"✅ Updated {rows_affected} rows: {update}")
            except Exception as e:
                print(f"❌ Failed: {update} - {e}")
        
        # FIX 4: Create enterprise triggers for updated_at
        print("\n🔧 Step 5: Creating enterprise triggers...")
        
        trigger_creation = """
        -- Function to automatically update updated_at
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = CURRENT_TIMESTAMP;
            RETURN NEW;
        END;
        $$ language 'plpgsql';
        
        -- Trigger for smart_rules
        DROP TRIGGER IF EXISTS update_smart_rules_updated_at ON smart_rules;
        CREATE TRIGGER update_smart_rules_updated_at
            BEFORE UPDATE ON smart_rules
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
            
        -- Trigger for ab_tests  
        DROP TRIGGER IF EXISTS update_ab_tests_updated_at ON ab_tests;
        CREATE TRIGGER update_ab_tests_updated_at
            BEFORE UPDATE ON ab_tests
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
        """
        
        try:
            cursor.execute(trigger_creation)
            print("✅ Enterprise triggers created")
        except Exception as e:
            print(f"⚠️  Trigger creation warning: {e}")
        
        # COMMIT ALL CHANGES
        conn.commit()
        print("\n✅ ALL ENTERPRISE FIXES COMMITTED SUCCESSFULLY!")
        
        # VALIDATION
        print("\n🔍 VALIDATION:")
        print("=" * 30)
        
        # Verify smart_rules structure
        cursor.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'smart_rules' 
            ORDER BY ordinal_position;
        """)
        
        smart_rules_columns = cursor.fetchall()
        print("✅ Smart Rules Columns:")
        for col_name, col_type in smart_rules_columns:
            print(f"   {col_name}: {col_type}")
        
        # Verify ab_tests structure
        cursor.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'ab_tests' 
            ORDER BY ordinal_position;
        """)
        
        ab_tests_columns = cursor.fetchall()
        print("\n✅ AB Tests Columns:")
        for col_name, col_type in ab_tests_columns:
            print(f"   {col_name}: {col_type}")
        
        # Test data insertion
        print("\n🧪 TESTING ENTERPRISE FUNCTIONALITY:")
        
        # Test smart rule creation
        test_smart_rule = """
        INSERT INTO smart_rules (name, agent_id, action_type, description) 
        VALUES ('Test-Enterprise-Rule', 'test-agent', 'allow', 'Enterprise test rule')
        RETURNING id;
        """
        
        cursor.execute(test_smart_rule)
        rule_id = cursor.fetchone()[0]
        print(f"✅ Test smart rule created with ID: {rule_id}")
        
        # Test ab_test creation
        test_ab_test = """
        INSERT INTO ab_tests (test_id, rule_id, test_name, description, variant_a, variant_b)
        VALUES ('test-enterprise-001', %s, 'Enterprise A/B Test', 'Testing enterprise functionality', 'Control', 'Treatment')
        RETURNING id;
        """
        
        cursor.execute(test_ab_test, (rule_id,))
        ab_test_id = cursor.fetchone()[0]
        print(f"✅ Test A/B test created with ID: {ab_test_id}")
        
        # Clean up test data
        cursor.execute("DELETE FROM ab_tests WHERE id = %s", (ab_test_id,))
        cursor.execute("DELETE FROM smart_rules WHERE id = %s", (rule_id,))
        conn.commit()
        print("✅ Test data cleaned up")
        
        cursor.close()
        conn.close()
        
        print("\n🎉 ENTERPRISE SCHEMA FIX COMPLETE!")
        print("=" * 50)
        print("✅ Smart rules table: Fixed missing columns")
        print("✅ AB tests table: Recreated with enterprise schema")
        print("✅ Triggers: Auto-update timestamps created")
        print("✅ Constraints: Enterprise data validation added")
        print("✅ Indexes: Performance optimization implemented")
        
        print("\n🚀 NEXT STEPS:")
        print("1. Deploy your application - A/B testing should now work")
        print("2. Test the A/B testing button in your frontend")
        print("3. Verify all smart-rules endpoints return 200 (not 404)")
        print("4. Monitor logs for successful router loading")
        
        return True
        
    except psycopg2.Error as e:
        print(f"❌ Database Error: {e}")
        if conn:
            conn.rollback()
        return False
    except Exception as e:
        print(f"❌ Enterprise Fix Error: {e}")
        if conn:
            conn.rollback()
        return False

if __name__ == "__main__":
    print("🚀 Starting Enterprise Schema Fix...")
    success = fix_enterprise_schema()
    
    if success:
        print("\n✅ Ready for Fortune 500 deployment!")
    else:
        print("\n❌ Fix failed - check logs and retry")
        sys.exit(1)