"""
🏢 ENTERPRISE SYSTEM AUDIT
Complete analysis of OW-KAI governance architecture
"""
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text, inspect
import json

load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))

print("=" * 80)
print("🏢 OW-KAI ENTERPRISE SYSTEM AUDIT")
print("=" * 80)
print()

# ============================================================================
# 1. DATABASE SCHEMA AUDIT
# ============================================================================
print("📊 SECTION 1: DATABASE SCHEMA")
print("-" * 80)

with engine.connect() as conn:
    # Get all tables
    result = conn.execute(text("""
        SELECT table_name, 
               (SELECT COUNT(*) FROM information_schema.columns WHERE table_name = t.table_name) as column_count,
               (SELECT COUNT(*) FROM information_schema.table_constraints 
                WHERE table_name = t.table_name AND constraint_type = 'FOREIGN KEY') as fk_count
        FROM information_schema.tables t
        WHERE table_schema = 'public'
        ORDER BY table_name
    """))
    
    tables = result.fetchall()
    
    print(f"Total Tables: {len(tables)}")
    print()
    
    # Categorize tables
    workflow_tables = [t for t in tables if 'workflow' in t[0]]
    automation_tables = [t for t in tables if 'automation' in t[0] or 'playbook' in t[0]]
    policy_tables = [t for t in tables if 'policy' in t[0] or 'policies' in t[0]]
    rule_tables = [t for t in tables if 'rule' in t[0]]
    action_tables = [t for t in tables if 'action' in t[0]]
    
    print("🔄 WORKFLOW SYSTEM:")
    for t in workflow_tables:
        count = conn.execute(text(f"SELECT COUNT(*) FROM {t[0]}")).scalar()
        print(f"  • {t[0]}: {t[1]} columns, {t[2]} foreign keys, {count} rows")
    
    print()
    print("🤖 AUTOMATION SYSTEM:")
    for t in automation_tables:
        count = conn.execute(text(f"SELECT COUNT(*) FROM {t[0]}")).scalar()
        print(f"  • {t[0]}: {t[1]} columns, {t[2]} foreign keys, {count} rows")
    
    print()
    print("📋 POLICY SYSTEM:")
    for t in policy_tables:
        count = conn.execute(text(f"SELECT COUNT(*) FROM {t[0]}")).scalar()
        print(f"  • {t[0]}: {t[1]} columns, {t[2]} foreign keys, {count} rows")
    
    print()
    print("🎯 RULE SYSTEM:")
    for t in rule_tables:
        count = conn.execute(text(f"SELECT COUNT(*) FROM {t[0]}")).scalar()
        print(f"  • {t[0]}: {t[1]} columns, {t[2]} foreign keys, {count} rows")
    
    print()
    print("⚡ ACTION SYSTEM:")
    for t in action_tables:
        count = conn.execute(text(f"SELECT COUNT(*) FROM {t[0]}")).scalar()
        print(f"  • {t[0]}: {t[1]} columns, {t[2]} foreign keys, {count} rows")

# ============================================================================
# 2. FOREIGN KEY RELATIONSHIPS
# ============================================================================
print()
print("=" * 80)
print("🔗 SECTION 2: FOREIGN KEY RELATIONSHIPS")
print("-" * 80)

with engine.connect() as conn:
    result = conn.execute(text("""
        SELECT 
            tc.table_name, 
            kcu.column_name,
            ccu.table_name AS foreign_table_name,
            ccu.column_name AS foreign_column_name
        FROM information_schema.table_constraints AS tc 
        JOIN information_schema.key_column_usage AS kcu
          ON tc.constraint_name = kcu.constraint_name
        JOIN information_schema.constraint_column_usage AS ccu
          ON ccu.constraint_name = tc.constraint_name
        WHERE tc.constraint_type = 'FOREIGN KEY'
        ORDER BY tc.table_name, kcu.column_name
    """))
    
    relationships = result.fetchall()
    
    # Group by table
    from collections import defaultdict
    table_fks = defaultdict(list)
    for rel in relationships:
        table_fks[rel[0]].append((rel[1], rel[2], rel[3]))
    
    for table, fks in sorted(table_fks.items()):
        print(f"\n{table}:")
        for col, ref_table, ref_col in fks:
            print(f"  • {col} → {ref_table}.{ref_col}")

print()
print("=" * 80)

# Save audit results
audit_data = {
    "total_tables": len(tables),
    "workflow_tables": len(workflow_tables),
    "automation_tables": len(automation_tables),
    "policy_tables": len(policy_tables),
    "rule_tables": len(rule_tables),
    "action_tables": len(action_tables),
    "foreign_keys": len(relationships)
}

with open('AUDIT_RESULTS.json', 'w') as f:
    json.dump(audit_data, f, indent=2)

print("✅ Audit data saved to AUDIT_RESULTS.json")
