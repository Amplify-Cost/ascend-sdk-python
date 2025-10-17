#!/usr/bin/env python3
"""
Core Database Schema Creation Script
Creates essential tables for Authorization Center functionality
"""

import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def create_core_tables():
    """Create core database tables using SQL DDL"""
    print("🚀 Starting core schema creation...")
    
    # Get database URL
    database_url = os.getenv('DATABASE_URL', 'postgresql://localhost:5432/owkai_pilot')
    print(f"📊 Using database: {database_url}")
    
    # Create engine
    engine = create_engine(database_url)
    
    # Core SQL DDL for essential tables
    core_schema_sql = """
    -- Users table (core authentication)
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        email VARCHAR(255) UNIQUE NOT NULL,
        password VARCHAR(255) NOT NULL,
        role VARCHAR(50) DEFAULT 'user',
        is_active BOOLEAN DEFAULT TRUE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_login TIMESTAMP,
        approval_level INTEGER DEFAULT 1,
        is_emergency_approver BOOLEAN DEFAULT FALSE,
        max_risk_approval INTEGER DEFAULT 50
    );
    
    -- Alerts table
    CREATE TABLE IF NOT EXISTS alerts (
        id SERIAL PRIMARY KEY,
        title VARCHAR(255) NOT NULL,
        message TEXT,
        severity VARCHAR(50) NOT NULL,
        status VARCHAR(50) DEFAULT 'open',
        source VARCHAR(100),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        resolved_at TIMESTAMP,
        extra_data JSONB,
        pending_action_id INTEGER,
        created_by INTEGER REFERENCES users(id)
    );
    
    -- Logs table
    CREATE TABLE IF NOT EXISTS logs (
        id SERIAL PRIMARY KEY,
        action VARCHAR(100) NOT NULL,
        details TEXT,
        user_id INTEGER REFERENCES users(id),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        ip_address VARCHAR(45),
        user_agent TEXT
    );
    
    -- Agent Actions table (essential for authorization)
    CREATE TABLE IF NOT EXISTS agent_actions (
        id SERIAL PRIMARY KEY,
        agent_id VARCHAR(255) NOT NULL,
        action_type VARCHAR(100) NOT NULL,
        description TEXT,
        risk_level VARCHAR(20),
        risk_score FLOAT,
        status VARCHAR(20) DEFAULT 'pending',
        approved BOOLEAN DEFAULT FALSE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        user_id INTEGER REFERENCES users(id),
        summary TEXT,
        parameters JSONB DEFAULT '{}',
        requires_approval BOOLEAN DEFAULT FALSE,
        approval_reason TEXT,
        approved_by INTEGER REFERENCES users(id),
        approved_at TIMESTAMP
    );
    
    -- MCP Servers table 
    CREATE TABLE IF NOT EXISTS mcp_servers (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        name VARCHAR(200) NOT NULL,
        version VARCHAR(50),
        transport_type VARCHAR(50) DEFAULT 'stdio',
        capabilities JSONB DEFAULT '{}',
        status VARCHAR(50) DEFAULT 'active',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    
    -- MCP Server Actions table (simplified)
    CREATE TABLE IF NOT EXISTS mcp_server_actions (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        mcp_server_id UUID REFERENCES mcp_servers(id),
        mcp_server_name VARCHAR(200) NOT NULL,
        namespace VARCHAR(100) NOT NULL,
        verb VARCHAR(100) NOT NULL,
        resource VARCHAR(500) NOT NULL,
        request_id VARCHAR(100) NOT NULL,
        session_id VARCHAR(100) NOT NULL,
        client_id VARCHAR(100) NOT NULL,
        risk_score INTEGER DEFAULT 0,
        risk_level VARCHAR(20) DEFAULT 'LOW',
        status VARCHAR(50) DEFAULT 'pending',
        requires_approval BOOLEAN DEFAULT FALSE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        user_id INTEGER REFERENCES users(id),
        parameters JSONB DEFAULT '{}'
    );
    
    -- Create essential indexes
    CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
    CREATE INDEX IF NOT EXISTS idx_agent_actions_status ON agent_actions(status);
    CREATE INDEX IF NOT EXISTS idx_agent_actions_user ON agent_actions(user_id);
    CREATE INDEX IF NOT EXISTS idx_alerts_status ON alerts(status);
    CREATE INDEX IF NOT EXISTS idx_mcp_actions_status ON mcp_server_actions(status);
    CREATE INDEX IF NOT EXISTS idx_mcp_actions_server ON mcp_server_actions(mcp_server_id);
    """
    
    try:
        # Execute schema creation
        with engine.connect() as conn:
            conn.execute(text(core_schema_sql))
            conn.commit()
            print("✅ Core schema created successfully")
        
        # Verify tables
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT table_name FROM information_schema.tables 
                WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
                ORDER BY table_name
            """))
            tables = [row[0] for row in result]
            
            print(f"✅ Created {len(tables)} tables:")
            for table in tables:
                print(f"   - {table}")
        
        return engine
        
    except Exception as e:
        print(f"❌ Schema creation failed: {e}")
        raise

def populate_test_data(engine):
    """Populate test data for validation"""
    print("\n📝 Populating test data...")
    
    test_data_sql = """
    -- Insert admin user (if not exists)
    INSERT INTO users (email, password, role, approval_level, is_emergency_approver, max_risk_approval)
    VALUES ('admin@owkai.app', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj2yK9S7atr6', 'admin', 5, TRUE, 100)
    ON CONFLICT (email) DO NOTHING;
    
    -- Insert test user (if not exists)
    INSERT INTO users (email, password, role, approval_level, max_risk_approval)
    VALUES ('test@owkai.app', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj2yK9S7atr6', 'user', 2, 30)
    ON CONFLICT (email) DO NOTHING;
    
    -- Insert sample agent actions for testing
    INSERT INTO agent_actions (agent_id, action_type, description, risk_level, risk_score, status, requires_approval)
    VALUES 
        ('claude-desktop', 'file_read', 'Read configuration file', 'LOW', 25, 'approved', TRUE),
        ('claude-desktop', 'database_query', 'Query user data', 'MEDIUM', 60, 'pending', TRUE),
        ('mcp-server-1', 'system_command', 'Execute system command', 'HIGH', 85, 'pending', TRUE)
    ON CONFLICT DO NOTHING;
    
    -- Insert sample MCP server
    INSERT INTO mcp_servers (name, version, status, capabilities)
    VALUES 
        ('Claude Desktop MCP', '1.0.0', 'active', '{"filesystem": true, "database": true}'),
        ('VS Code MCP', '0.9.5', 'active', '{"code_editing": true, "git": true}')
    ON CONFLICT DO NOTHING;
    """
    
    try:
        with engine.connect() as conn:
            conn.execute(text(test_data_sql))
            conn.commit()
            print("✅ Test data populated successfully")
    except Exception as e:
        print(f"⚠️  Test data population warning: {e}")

def test_database_connection(engine):
    """Test database connection with actual queries"""
    print("\n🔍 Testing database connectivity...")
    
    try:
        with engine.connect() as conn:
            # Test users table
            result = conn.execute(text("SELECT COUNT(*) as user_count FROM users"))
            user_count = result.fetchone()[0]
            
            # Test agent actions table
            result = conn.execute(text("SELECT COUNT(*) as action_count FROM agent_actions"))
            action_count = result.fetchone()[0]
            
            # Test authorization-specific query
            result = conn.execute(text("""
                SELECT COUNT(*) as pending_approvals 
                FROM agent_actions 
                WHERE requires_approval = TRUE AND status = 'pending'
            """))
            pending_count = result.fetchone()[0]
            
            print(f"✅ Database connection successful!")
            print(f"   - Users: {user_count}")
            print(f"   - Agent Actions: {action_count}")
            print(f"   - Pending Approvals: {pending_count}")
            
            return True
            
    except Exception as e:
        print(f"❌ Database connection test failed: {e}")
        return False

if __name__ == "__main__":
    try:
        # Create schema
        engine = create_core_tables()
        
        # Populate test data
        populate_test_data(engine)
        
        # Test connectivity
        test_database_connection(engine)
        
        print("\n🎉 Database setup completed successfully!")
        print("   Ready for Authorization Center API testing!")
        
    except Exception as e:
        print(f"\n❌ Database setup failed: {e}")
        exit(1)