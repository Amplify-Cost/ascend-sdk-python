"""
Enterprise Performance Diagnostic Tool
Analyzes current database performance and identifies bottlenecks
"""
import sys
import time
from database import SessionLocal, engine
from sqlalchemy import text, inspect

def analyze_database_performance():
    """Comprehensive performance analysis"""
    
    print("=" * 70)
    print("ENTERPRISE PERFORMANCE DIAGNOSTIC REPORT")
    print("=" * 70)
    print()
    
    db = SessionLocal()
    
    try:
        # 1. Database Size Analysis
        print("📊 DATABASE SIZE ANALYSIS")
        print("-" * 70)
        
        result = db.execute(text("""
            SELECT 
                schemaname,
                tablename,
                pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size,
                pg_total_relation_size(schemaname||'.'||tablename) AS size_bytes
            FROM pg_tables
            WHERE schemaname = 'public'
            ORDER BY size_bytes DESC
            LIMIT 10
        """)).fetchall()
        
        for row in result:
            print(f"  {row[1]:30s} {row[2]:>15s}")
        print()
        
        # 2. Record Counts
        print("📈 RECORD COUNTS")
        print("-" * 70)
        
        tables = ['agent_actions', 'cvss_assessments', 'nist_control_mappings', 
                  'mitre_technique_mappings', 'enriched_actions']
        
        counts = {}
        for table in tables:
            try:
                count = db.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
                counts[table] = count
                print(f"  {table:30s} {count:>10,d} records")
            except Exception as e:
                print(f"  {table:30s} [Table not found]")
        print()
        
        # 3. Index Analysis
        print("🔍 INDEX ANALYSIS")
        print("-" * 70)
        
        result = db.execute(text("""
            SELECT 
                tablename,
                indexname,
                indexdef
            FROM pg_indexes
            WHERE schemaname = 'public'
            AND tablename IN ('agent_actions', 'cvss_assessments', 'nist_control_mappings', 'mitre_technique_mappings')
            ORDER BY tablename, indexname
        """)).fetchall()
        
        if result:
            current_table = None
            for row in result:
                if row[0] != current_table:
                    print(f"\n  Table: {row[0]}")
                    current_table = row[0]
                print(f"    ✓ {row[1]}")
        else:
            print("  ⚠️  NO INDEXES FOUND (This is the performance problem!)")
        print()
        
        # 4. Missing Indexes Detection
        print("⚠️  MISSING CRITICAL INDEXES")
        print("-" * 70)
        
        critical_indexes = [
            ('cvss_assessments', 'agent_action_id', 'Foreign key lookups'),
            ('nist_control_mappings', 'agent_action_id', 'Foreign key lookups'),
            ('mitre_technique_mappings', 'agent_action_id', 'Foreign key lookups'),
            ('agent_actions', 'status', 'Pending action queries'),
            ('agent_actions', 'timestamp', 'Recent action queries'),
        ]
        
        for table, column, reason in critical_indexes:
            result = db.execute(text(f"""
                SELECT 1 FROM pg_indexes 
                WHERE tablename = '{table}' 
                AND indexdef LIKE '%{column}%'
            """)).first()
            
            if not result:
                print(f"  ❌ Missing: {table}.{column} - {reason}")
        print()
        
        # 5. Query Performance Test
        print("⚡ QUERY PERFORMANCE TEST")
        print("-" * 70)
        
        # Test 1: Pending actions query
        start = time.time()
        result = db.execute(text("""
            SELECT COUNT(*) FROM agent_actions 
            WHERE status IN ('pending', 'pending_approval')
        """)).scalar()
        elapsed = time.time() - start
        print(f"  Pending actions query: {elapsed*1000:.2f}ms ({result} records)")
        
        # Test 2: Assessment lookup
        start = time.time()
        result = db.execute(text("""
            SELECT COUNT(*) 
            FROM agent_actions a
            LEFT JOIN cvss_assessments c ON a.id = c.agent_action_id
            WHERE a.status IN ('pending', 'pending_approval')
        """)).scalar()
        elapsed = time.time() - start
        print(f"  Assessment join query: {elapsed*1000:.2f}ms")
        
        if elapsed > 0.1:
            print(f"    ⚠️  SLOW! Should be <50ms with proper indexes")
        else:
            print(f"    ✓ Good performance")
        print()
        
        # 6. Assessment Coverage Analysis
        print("📋 ASSESSMENT COVERAGE")
        print("-" * 70)
        
        if 'agent_actions' in counts:
            total = counts.get('agent_actions', 0)
            cvss = counts.get('cvss_assessments', 0)
            nist = counts.get('nist_control_mappings', 0)
            mitre = counts.get('mitre_technique_mappings', 0)
            
            print(f"  Total Actions:        {total:>10,d}")
            print(f"  CVSS Assessments:     {cvss:>10,d} ({cvss/total*100 if total else 0:.1f}%)")
            print(f"  NIST Mappings:        {nist:>10,d} ({nist/total*100 if total else 0:.1f}%)")
            print(f"  MITRE Mappings:       {mitre:>10,d} ({mitre/total*100 if total else 0:.1f}%)")
            print()
            
            uncovered = total - cvss
            if uncovered > 0:
                print(f"  ⚠️  {uncovered} actions without CVSS assessment")
                print(f"     These will trigger auto-assessment on next dashboard load")
        print()
        
        # 7. Recommendations
        print("💡 ENTERPRISE RECOMMENDATIONS")
        print("-" * 70)
        
        result = db.execute(text("""
            SELECT 1 FROM pg_indexes 
            WHERE tablename = 'cvss_assessments' 
            AND indexname LIKE '%agent_action%'
        """)).first()
        
        if not result:
            print("  1. ⚡ CRITICAL: Add foreign key indexes (50-70% improvement)")
            print("     - Will dramatically speed up JOIN queries")
            print("     - Zero code changes required")
            print()
        
        if counts.get('agent_actions', 0) - counts.get('cvss_assessments', 0) > 10:
            print("  2. 🔥 HIGH: Implement batch assessment processing")
            print("     - Process multiple actions in single transaction")
            print("     - Reduce database round-trips by 80%")
            print()
        
        print("  3. 📊 MEDIUM: Add query result caching")
        print("     - Cache assessment results in memory")
        print("     - Reduce repeated database queries")
        print()
        
        print("  4. 🎯 OPTIONAL: Async background processing")
        print("     - Move auto-assessment to background queue")
        print("     - For handling bulk operations at scale")
        print()
        
    except Exception as e:
        print(f"Error during diagnostics: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()
    
    print("=" * 70)
    print("DIAGNOSTIC COMPLETE")
    print("=" * 70)

if __name__ == "__main__":
    analyze_database_performance()
