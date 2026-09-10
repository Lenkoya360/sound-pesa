-- PostgreSQL initialization script for Sound Pesa Platform (Development)
-- This script sets up the database with necessary extensions and configurations

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Set timezone
SET timezone = 'UTC';

-- Create additional schemas if needed
CREATE SCHEMA IF NOT EXISTS audit;
CREATE SCHEMA IF NOT EXISTS blockchain;

-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE soundpesa TO soundpesa;
GRANT ALL PRIVILEGES ON SCHEMA public TO soundpesa;
GRANT ALL PRIVILEGES ON SCHEMA audit TO soundpesa;
GRANT ALL PRIVILEGES ON SCHEMA blockchain TO soundpesa;

-- Create simple audit table for development
CREATE TABLE IF NOT EXISTS audit.activity_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    table_name VARCHAR(255) NOT NULL,
    operation VARCHAR(10) NOT NULL,
    user_id UUID,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create blockchain status tracking table (simplified for development)
CREATE TABLE IF NOT EXISTS blockchain.node_status (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    blockchain VARCHAR(50) NOT NULL,
    is_synced BOOLEAN DEFAULT FALSE,
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(blockchain)
);

-- Insert initial blockchain status records for development
INSERT INTO blockchain.node_status (blockchain) VALUES 
    ('bitcoin'),
    ('ethereum'),
    ('cardano'),
    ('polkadot')
ON CONFLICT (blockchain) DO NOTHING;