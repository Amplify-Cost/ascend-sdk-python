-- Drop all existing tables
DROP TABLE IF EXISTS sessions CASCADE;
DROP TABLE IF EXISTS audit CASCADE; 
DROP TABLE IF EXISTS roles CASCADE;
DROP TABLE IF EXISTS users CASCADE;
DROP TABLE IF EXISTS alembic_version CASCADE;

-- Alembic will recreate everything from migrations
