#!/usr/bin/env python3
"""
Enterprise Database Schema Analyzer for OW-AI Platform
Fixed version with correct external Railway connection
"""

import psycopg2
import sys

def analyze_enterprise_schema():
    print("🔍 OW-AI Enterprise Database Schema Analysis")
    print("=" * 60)
    
    # Use the EXTERNAL Railway connection string (from your Railway variables)
    database_url = "postgresql://postgres:juVnTTAwjcgEAkNPMTXoYVhcdqljgyHr@hopper.proxy.rlwy.net:13171/railway"
    
    print(f"🌐 Connecting to Railway PostgreSQL (External)...")
    print(f"   Host: hopper.proxy.rlwy.net:13171")
    
    try:
        # Enterprise connection with SSL
        conn = psycopg2.connect(
            database_url,
            sslmode='prefer',  # Changed from 'require' for Railway compatibility
            connect_timeout=30,
            application_name='OW-AI-Enterprise-Analyzer'
        )
        
        cursor = conn.cursor()
        
        # Get all table structures - simplified query for better compatibility
        schema_query = """
        SELECT 
            t.table_name,
            c.column_name,
            c.data_type,
            c.is_nullable,
            c.column_default,
            c.character_maximum_length
        FROM information_schema.tables t
        LEFT JOIN information_schema.columns c 
            ON t.table_name = c.table_name
        WHERE t.table_schema = 'public' 
            AND t.table_type = 'BASE TABLE'
            AND c.column_name IS NOT NULL
        ORDER BY t.table_name, c.ordinal_position;
        """
        
        print("📡 Executing enterprise schema analysis...")
        cursor.execute(schema_query)
        results = cursor.fetchall()
        
        if not results:
            print("⚠️  No tables found in public schema")
            return
        
        # Organize by table
        tables = {}
        for row in results:
            table_name, column_name, data_type, is_nullable, default_val, max_length = row
            
            if table_name not in tables:
                tables[table_name] = []
            
            # Format type info
            type_info = data_type
            if max_length:
                type_info += f"({max_length})"
            
            tables[table_name].append({
                'column': column_name,
                'type': type_info,
                'nullable': is_nullable == 'YES',
                'default': default_val
            })
        
        # Enterprise analysis output
        print(f"\n📊 ENTERPRISE SCHEMA ANALYSIS")
        print(f"Found {len(tables)} tables in production database")
        print("=" * 60)
        
        # Show critical tables first
        critical_tables = ['smart_rules', 'users', 'ab_tests', 'audit_logs', 'rules']
        
        print(f"\n🔴 CRITICAL TABLES ANALYSIS:")
        print("=" * 50)
        
        for table_name in critical_tables:
            if table_name in tables:
                print(f"\n✅ FOUND: {table_name}")
                print("-" * 30)
                for col in tables[table_name]:
                    nullable = "NULL" if col['nullable'] else "NOT NULL"
                    default = f" DEFAULT {col['default']}" if col['default'] else ""
                    print(f"   {col['column']:<25} {col['type']:<20} {nullable}{default}")
            else:
                print(f"\n❌ MISSING: {table_name}")
        
        # Show all other tables
        print(f"\n📋 ALL OTHER TABLES:")
        print("=" * 50)
        
        other_tables = [t for t in sorted(tables.keys()) if t not in critical_tables]
        for table_name in other_tables:
            print(f"\n📋 TABLE: {table_name}")
            print("-" * 30)
            for col in tables[table_name][:5]:  # Show first 5 columns only
                nullable = "NULL" if col['nullable'] else "NOT NULL"
                print(f"   {col['column']:<25} {col['type']:<20} {nullable}")
            if len(tables[table_name]) > 5:
                print(f"   ... and {len(tables[table_name]) - 5} more columns")
        
        # Critical enterprise checks
        print(f"\n🏢 ENTERPRISE COMPLIANCE ANALYSIS")
        print("=" * 60)
        
        enterprise_issues = []
        
        # Check for critical tables
        for critical_table in critical_tables:
            if critical_table not in tables:
                enterprise_issues.append(f"❌ Missing critical table: {critical_table}")
            else:
                print(f"✅ Critical table found: {critical_table}")
        
        # Detailed smart_rules analysis (A/B testing dependency)
        if 'smart_rules' in tables:
            smart_rules_cols = [col['column'] for col in tables['smart_rules']]
            required_cols = ['id', 'name', 'description', 'created_at', 'updated_at']
            
            print(f"\n🔍 SMART_RULES TABLE DETAILED ANALYSIS:")
            print(f"   Total columns: {len(smart_rules_cols)}")
            print(f"   Columns found: {smart_rules_cols}")
            
            missing_cols = []
            for req_col in required_cols:
                if req_col not in smart_rules_cols:
                    missing_cols.append(req_col)
                    enterprise_issues.append(f"❌ smart_rules missing column: {req_col}")
                else:
                    print(f"✅ smart_rules has required column: {req_col}")
            
            if missing_cols:
                print(f"❌ Missing required columns: {missing_cols}")
        else:
            enterprise_issues.append("❌ smart_rules table completely missing")
        
        # Check ab_tests table for A/B testing functionality
        if 'ab_tests' in tables:
            ab_test_cols = [col['column'] for col in tables['ab_tests']]
            print(f"\n🧪 AB_TESTS TABLE ANALYSIS:")
            print(f"   Columns found: {ab_test_cols}")
            print("✅ A/B testing table exists")
        else:
            enterprise_issues.append("❌ Missing ab_tests table - explains A/B testing failures")
            print("❌ ab_tests table missing - this explains A/B testing failures")
        
        # Check if 'rules' table exists (alternative to smart_rules)
        if 'rules' in tables:
            rules_cols = [col['column'] for col in tables['rules']]
            print(f"\n📋 RULES TABLE ANALYSIS:")
            print(f"   Columns found: {rules_cols}")
            print("💡 Found 'rules' table - might be used instead of 'smart_rules'")
        
        # Check audit logging capability
        if 'audit_logs' in tables:
            print("✅ Enterprise audit logging table exists")
        else:
            enterprise_issues.append("❌ Missing audit_logs table for compliance")
        
        # Summary and diagnosis
        print(f"\n📈 ENTERPRISE READINESS SUMMARY")
        print("=" * 60)
        
        if enterprise_issues:
            print("🚨 ENTERPRISE ISSUES FOUND:")
            for issue in enterprise_issues:
                print(f"   {issue}")
            print(f"\n❌ Database schema has issues preventing enterprise deployment")
        else:
            print("✅ Database schema passes enterprise compliance checks")
        
        print(f"\n📋 Total Tables: {len(tables)}")
        print(f"🔴 Critical Tables Found: {len([t for t in critical_tables if t in tables])}/{len(critical_tables)}")
        print(f"⚠️  Issues Found: {len(enterprise_issues)}")
        
        # Special A/B testing diagnosis
        print(f"\n🎯 A/B TESTING FAILURE DIAGNOSIS:")
        print("=" * 50)
        
        if 'smart_rules' not in tables and 'ab_tests' not in tables:
            print("❌ BOTH smart_rules AND ab_tests tables missing")
            print("   ROOT CAUSE: No tables for smart rules or A/B testing functionality")
            print("   FIX NEEDED: Create both tables with proper schema")
        elif 'smart_rules' not in tables:
            print("❌ smart_rules table missing")
            print("   ROOT CAUSE: FastAPI can't load SmartRule model")
            print("   FIX NEEDED: Create smart_rules table or update model to use existing table")
        elif 'ab_tests' not in tables:
            print("❌ ab_tests table missing")
            print("   ROOT CAUSE: A/B testing endpoints can't store test data")
            print("   FIX NEEDED: Create ab_tests table")
        else:
            print("✅ Both smart_rules and ab_tests tables exist")
            print("   ISSUE: Likely column name/type mismatches in model definitions")
            print("   FIX NEEDED: Align SQLAlchemy models with actual database schema")
        
        # Provide next steps
        print(f"\n🔧 ENTERPRISE NEXT STEPS:")
        print("=" * 50)
        if enterprise_issues:
            print("1. Create missing tables using SQLAlchemy models")
            print("2. Run database migrations to align schema")
            print("3. Update model definitions to match existing schema")
            print("4. Test all endpoints after schema fixes")
        else:
            print("1. Schema is compliant - focus on application logic")
            print("2. Verify router loading and model imports")
            print("3. Test endpoint functionality")
        
        cursor.close()
        conn.close()
        
        print(f"\n✅ Enterprise analysis complete!")
        
    except psycopg2.Error as e:
        print(f"❌ Enterprise Database Connection Error: {e}")
        print("💡 Check Railway service status and connection string")
    except Exception as e:
        print(f"❌ Enterprise Analysis Error: {e}")
        print(f"💡 Error details: {str(e)}")

if __name__ == "__main__":
    print("🚀 Starting OW-AI Enterprise Database Analysis...")
    analyze_enterprise_schema()