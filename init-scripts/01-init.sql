-- Living Knowledge System Database Initialization
-- This script runs when PostgreSQL container starts for the first time

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";

-- Create application schema
CREATE SCHEMA IF NOT EXISTS living;

-- Set search path
ALTER DATABASE living_system SET search_path TO living, public;

-- Grant permissions
GRANT ALL PRIVILEGES ON SCHEMA living TO living;

-- Note: Tables will be created by the application on first startup
-- This is handled by PostgreSQLDatabase._ensure_tables()

-- Create initial health check table
CREATE TABLE IF NOT EXISTS living.system_init (
    id SERIAL PRIMARY KEY,
    initialized_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    version VARCHAR(50) DEFAULT '1.0.0'
);

INSERT INTO living.system_init (version) VALUES ('1.0.0')
ON CONFLICT DO NOTHING;
