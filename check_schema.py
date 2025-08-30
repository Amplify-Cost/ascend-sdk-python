import psycopg2
import os

# Connect to database
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://owkai_admin:1YLIthN_fWt4H+&yJ<gl1b5}iDFQ4nAj@owkai-pilot-db.cpwaouykib7n.us-east-2.rds.amazonaws.com:5432/owkai_pilot')
conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()

# Get table schema
cur.execute("""
    SELECT column_name, data_type 
    FROM information_schema.columns 
    WHERE table_name = 'agent_actions' 
    ORDER BY ordinal_position;
""")

columns = cur.fetchall()
print("agent_actions table columns:")
for col_name, col_type in columns:
    print(f"  {col_name}: {col_type}")

cur.close()
conn.close()
