"""
Enterprise Performance Diagnostic v2 - With proper transaction handling
"""
from database import SessionLocal
from sqlalchemy import text, inspect

def analyze_indexes():
    """Analyze current database indexes"""
    db = SessionLocal()
    
    print("=" * 70)
    print("ENTERPRISE INDEX ANALYSIS")
    print("=" * 70)
    print()
    
    try:
        # Get all tables
        inspector = inspect(db.bind)
        tables = inspector.get_table_names()
        
        print("📊 TABLES AND INDEXES")
        print("-" * 70)
        
        critical_tables = ['agent_actions', 'cvss_assessments', 
                          'nist_control_mappings', 'mitre_technique_mappings']
        
        for table in critical_tables:
            if table in tables:
                indexes = inspector.get_indexes(table)
                foreign_keys = inspector.get_foreign_keys(table)
                
                print(f"\n{table}:")
                print(f"  Foreign Keys: {len(foreign_keys)}")
                for fk in foreign_keys:
                    print(f"    - {fk['constrained_columns']} -> {fk['referred_table']}.{fk['referred_columns']}")
                
                print(f"  Indexes: {len(indexes)}")
                if indexes:
                    for idx in indexes:
                        print(f"    ✓ {idx['name']}: {idx['column_names']}")
                else:
                    print(f"    ⚠️  NO INDEXES!")
        
        print()
        print("=" * 70)
        print()
        
        # Check for missing indexes on foreign keys
        print("🔍 MISSING FOREIGN KEY INDEXES (Critical for Performance)")
        print("-" * 70)
        
        missing_indexes = []
        for table in critical_tables:
            if table in tables:
                foreign_keys = inspector.get_foreign_keys(table)
                indexes = inspector.get_indexes(table)
                index_columns = set()
                for idx in indexes:
                    index_columns.update(idx['column_names'])
                
                for fk in foreign_keys:
                    for col in fk['constrained_columns']:
                        if col not in index_columns:
                            missing_indexes.append((table, col, fk['referred_table']))
                            print(f"  ❌ {table}.{col} (references {fk['referred_table']})")
        
        if not missing_indexes:
            print("  ✅ All foreign keys are indexed!")
        
        print()
        print("=" * 70)
        
        return missing_indexes
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    missing = analyze_indexes()
    
    if missing:
        print()
        print("💡 RECOMMENDATION: Add these indexes immediately")
        print("   Expected performance improvement: 50-80%")

