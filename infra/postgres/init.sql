-- PostgreSQL initialization script
-- This runs automatically when the container is first created

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Create indexes will be done via Alembic migrations
-- This file is just for extensions and basic setup

-- Log successful initialization
DO $$
BEGIN
    RAISE NOTICE 'PostgreSQL initialized successfully for App-Idea Miner';
END $$;
