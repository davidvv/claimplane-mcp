-- Initial database setup script for PostgreSQL
-- This script runs automatically when the PostgreSQL container starts

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Create database if it doesn't exist (for development)
-- Note: This is handled by docker-compose environment variables, but included for reference

-- Create a test user for development
-- This user will be created automatically by the application, but we can add it here for testing
-- INSERT INTO users (email, booking_reference, is_admin) 
-- VALUES ('test@example.com', 'ABC123', false)
-- ON CONFLICT (email) DO NOTHING;

-- Add any initial data or configurations here
-- For example, you could add sample airports, airlines, etc.

-- Create indexes for better performance (these are also created by Alembic migrations)
-- This is just for reference and will be created by the migration system

-- Sample data for testing (optional)
-- You can uncomment and modify these as needed for development

-- Sample users
-- INSERT INTO users (email, booking_reference, is_admin) VALUES
-- ('admin@flightclaim.com', 'ADMIN001', true),
-- ('user1@example.com', 'USER001', false),
-- ('user2@example.com', 'USER002', false)
-- ON CONFLICT (email) DO NOTHING;

-- Sample claims
-- INSERT INTO claims (claim_id, user_id, full_name, email, booking_reference, 
--                   flight_number, planned_departure_date, status) VALUES
-- ('CL000001', 1, 'Test User', 'test@example.com', 'ABC123', 
--  'LH1234', '2024-01-15', 'submitted'),
-- ('CL000002', 2, 'John Doe', 'user1@example.com', 'USER001', 
--  'BA4567', '2024-01-16', 'under_review')
-- ON CONFLICT (claim_id) DO NOTHING;

-- Grant permissions (handled by docker-compose environment)
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO easy_air_claim_user;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO easy_air_claim_user;

-- Add any custom functions or procedures here
-- For example, a function to generate claim IDs:
/*
CREATE OR REPLACE FUNCTION generate_claim_id() RETURNS VARCHAR(20) AS $$
BEGIN
    RETURN 'CL' || TO_CHAR(EXTRACT(EPOCH FROM NOW())::BIGINT, 'FM000000');
END;
$$ LANGUAGE plpgsql;
*/

-- Add triggers for updated_at timestamps (handled by SQLAlchemy)
/*
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_claims_updated_at BEFORE UPDATE ON claims
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
*/