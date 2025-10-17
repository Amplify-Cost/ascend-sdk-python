import sqlite3
import sys

try:
    conn = sqlite3.connect('database.db')  # Adjust path if needed
    cursor = conn.cursor()
    
    cursor.execute("PRAGMA table_info(agent_actions)")
    columns = cursor.fetchall()
    
    print("=== AGENT_ACTIONS TABLE SCHEMA ===")
    for col in columns:
        print(f"{col[1]:<20} {col[2]:<15} {'NOT NULL' if col[3] else 'NULLABLE':<10} DEFAULT: {col[4] or 'None'}")
    
    cursor.execute("SELECT id, status, approved, risk_level FROM agent_actions WHERE id = 2")
    result = cursor.fetchone()
    if result:
        print(f"\n=== ACTION 2 CURRENT STATE ===")
        print(f"ID: {result[0]}, Status: {result[1]}, Approved: {result[2]}, Risk Level: {result[3]}")
    
    conn.close()
except Exception as e:
    print(f"Error: {e}")
