"""
Database migration to create missing tables
"""
import asyncio
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, Float, DateTime, Text, Boolean, ForeignKey
from sqlalchemy.sql import func
from app.database import DATABASE_URL

async def create_missing_tables():
    """Create the 3 missing tables"""
    
    engine = create_engine(DATABASE_URL.replace('+asyncpg', ''))
    metadata = MetaData()
    
    print("🗄️  Creating missing database tables...")
    print("")
    
    # Table 1: mcp_policies
    print("1️⃣  Creating mcp_policies table...")
    mcp_policies = Table(
        'mcp_policies',
        metadata,
        Column('id', Integer, primary_key=True, autoincrement=True),
        Column('name', String(255), nullable=False),
        Column('description', Text),
        Column('policy_type', String(50), nullable=False),
        Column('conditions', Text, nullable=False),
        Column('actions', Text, nullable=False),
        Column('risk_level', String(20), default='medium'),
        Column('approval_required', Boolean, default=False),
        Column('approval_levels', Integer, default=1),
        Column('created_by', Integer, ForeignKey('users.id')),
        Column('created_at', DateTime(timezone=True), server_default=func.now()),
        Column('updated_at', DateTime(timezone=True), onupdate=func.now()),
        Column('is_active', Boolean, default=True)
    )
    
    # Table 2: analytics_metrics
    print("2️⃣  Creating analytics_metrics table...")
    analytics_metrics = Table(
        'analytics_metrics',
        metadata,
        Column('id', Integer, primary_key=True, autoincrement=True),
        Column('metric_name', String(100), nullable=False),
        Column('metric_value', Float, nullable=False),
        Column('metric_type', String(50), nullable=False),
        Column('category', String(50)),
        Column('tags', Text),
        Column('timestamp', DateTime(timezone=True), server_default=func.now()),
        Column('metadata', Text)
    )
    
    # Table 3: rule_optimizations
    print("3️⃣  Creating rule_optimizations table...")
    rule_optimizations = Table(
        'rule_optimizations',
        metadata,
        Column('id', Integer, primary_key=True, autoincrement=True),
        Column('rule_id', Integer, ForeignKey('smart_rules.id'), nullable=False),
        Column('optimization_type', String(50), nullable=False),
        Column('original_condition', Text),
        Column('optimized_condition', Text),
        Column('performance_gain', Float),
        Column('confidence_score', Float),
        Column('applied', Boolean, default=False),
        Column('created_at', DateTime(timezone=True), server_default=func.now()),
        Column('applied_at', DateTime(timezone=True)),
        Column('applied_by', Integer, ForeignKey('users.id'))
    )
    
    # Create all tables
    try:
        metadata.create_all(engine)
        print("")
        print("✅ All tables created successfully!")
        print("")
        print("📊 Tables created:")
        print("   ✅ mcp_policies")
        print("   ✅ analytics_metrics")
        print("   ✅ rule_optimizations")
        print("")
        return True
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(create_missing_tables())
