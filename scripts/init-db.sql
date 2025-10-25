-- Bwenge OS Database Initialization Script
-- This script sets up the initial database schema and data

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create organizations table
CREATE TABLE IF NOT EXISTS organizations (
    org_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    plan VARCHAR(50) DEFAULT 'free',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create users table
CREATE TABLE IF NOT EXISTS users (
    user_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id UUID NOT NULL REFERENCES organizations(org_id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    role VARCHAR(50) DEFAULT 'user',
    password_hash VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create personas table
CREATE TABLE IF NOT EXISTS personas (
    persona_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id UUID NOT NULL REFERENCES organizations(org_id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    tone JSONB DEFAULT '{}',
    rules JSONB DEFAULT '{}',
    sample_prompts JSONB DEFAULT '[]',
    safety_rules JSONB DEFAULT '[]',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create knowledge_sources table
CREATE TABLE IF NOT EXISTS knowledge_sources (
    source_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id UUID NOT NULL REFERENCES organizations(org_id) ON DELETE CASCADE,
    persona_id UUID NOT NULL REFERENCES personas(persona_id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    type VARCHAR(50) NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    storage_path VARCHAR(500),
    file_size BIGINT,
    chunk_count INTEGER DEFAULT 0,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create conversations table
CREATE TABLE IF NOT EXISTS conversations (
    conv_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    persona_id UUID NOT NULL REFERENCES personas(persona_id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    session_id VARCHAR(255),
    messages JSONB DEFAULT '[]',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create analytics_events table
CREATE TABLE IF NOT EXISTS analytics_events (
    event_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id UUID NOT NULL REFERENCES organizations(org_id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(user_id) ON DELETE SET NULL,
    persona_id UUID REFERENCES personas(persona_id) ON DELETE SET NULL,
    event_type VARCHAR(100) NOT NULL,
    payload JSONB DEFAULT '{}',
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create models_3d table
CREATE TABLE IF NOT EXISTS models_3d (
    model_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    persona_id UUID NOT NULL REFERENCES personas(persona_id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    model_url VARCHAR(500) NOT NULL,
    animations JSONB DEFAULT '[]',
    scale FLOAT DEFAULT 1.0,
    bounding_box JSONB DEFAULT '{}',
    version VARCHAR(50) DEFAULT '1.0',
    mime_type VARCHAR(100) DEFAULT 'model/gltf+json',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create subscriptions table
CREATE TABLE IF NOT EXISTS subscriptions (
    subscription_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id UUID NOT NULL REFERENCES organizations(org_id) ON DELETE CASCADE,
    stripe_subscription_id VARCHAR(255) UNIQUE,
    status VARCHAR(50) NOT NULL,
    plan_name VARCHAR(100) NOT NULL,
    current_period_start TIMESTAMP WITH TIME ZONE,
    current_period_end TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create usage_quotas table
CREATE TABLE IF NOT EXISTS usage_quotas (
    quota_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id UUID NOT NULL REFERENCES organizations(org_id) ON DELETE CASCADE,
    quota_type VARCHAR(50) NOT NULL,
    limit_value INTEGER NOT NULL,
    used_value INTEGER DEFAULT 0,
    reset_period VARCHAR(20) DEFAULT 'monthly',
    last_reset TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_users_org_id ON users(org_id);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_personas_org_id ON personas(org_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_sources_org_id ON knowledge_sources(org_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_sources_persona_id ON knowledge_sources(persona_id);
CREATE INDEX IF NOT EXISTS idx_conversations_user_id ON conversations(user_id);
CREATE INDEX IF NOT EXISTS idx_conversations_persona_id ON conversations(persona_id);
CREATE INDEX IF NOT EXISTS idx_conversations_session_id ON conversations(session_id);
CREATE INDEX IF NOT EXISTS idx_analytics_events_org_id ON analytics_events(org_id);
CREATE INDEX IF NOT EXISTS idx_analytics_events_timestamp ON analytics_events(timestamp);
CREATE INDEX IF NOT EXISTS idx_analytics_events_type ON analytics_events(event_type);
CREATE INDEX IF NOT EXISTS idx_models_3d_persona_id ON models_3d(persona_id);
CREATE INDEX IF NOT EXISTS idx_subscriptions_org_id ON subscriptions(org_id);
CREATE INDEX IF NOT EXISTS idx_usage_quotas_org_id ON usage_quotas(org_id);

-- Create triggers for updated_at timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply triggers to tables with updated_at columns
CREATE TRIGGER update_organizations_updated_at BEFORE UPDATE ON organizations FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_personas_updated_at BEFORE UPDATE ON personas FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_knowledge_sources_updated_at BEFORE UPDATE ON knowledge_sources FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_conversations_updated_at BEFORE UPDATE ON conversations FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_models_3d_updated_at BEFORE UPDATE ON models_3d FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_subscriptions_updated_at BEFORE UPDATE ON subscriptions FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_usage_quotas_updated_at BEFORE UPDATE ON usage_quotas FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert default organization for development
INSERT INTO organizations (name, plan) 
VALUES ('Default Organization', 'free') 
ON CONFLICT DO NOTHING;

-- Create default admin user (password: admin123)
-- Note: In production, this should be removed or changed
INSERT INTO users (org_id, name, email, password_hash, role)
SELECT 
    org_id,
    'Admin User',
    'admin@bwenge.com',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj3bp.Gm.F5e', -- admin123
    'admin'
FROM organizations 
WHERE name = 'Default Organization'
ON CONFLICT (email) DO NOTHING;

-- Create sample persona
INSERT INTO personas (org_id, name, description, tone, rules, sample_prompts, safety_rules)
SELECT 
    org_id,
    'Gabriel - Math Tutor',
    'A friendly AI tutor specialized in mathematics education',
    '{"style": "friendly", "formality": "casual", "enthusiasm": "high"}',
    '{"guidelines": ["Be encouraging and patient", "Break down complex problems", "Use examples and analogies"]}',
    '["Hello! I''m Gabriel, your math tutor. What would you like to learn today?", "Let''s solve this step by step!", "Great question! Let me explain that concept."]',
    '["Keep content appropriate for educational settings", "No inappropriate or harmful content", "Focus on mathematical concepts and learning"]'
FROM organizations 
WHERE name = 'Default Organization'
ON CONFLICT DO NOTHING;

-- Create default usage quotas for the default organization
INSERT INTO usage_quotas (org_id, quota_type, limit_value, used_value)
SELECT 
    org_id,
    'messages',
    100,
    0
FROM organizations 
WHERE name = 'Default Organization'
ON CONFLICT DO NOTHING;

INSERT INTO usage_quotas (org_id, quota_type, limit_value, used_value)
SELECT 
    org_id,
    'storage',
    104857600, -- 100MB in bytes
    0
FROM organizations 
WHERE name = 'Default Organization'
ON CONFLICT DO NOTHING;

INSERT INTO usage_quotas (org_id, quota_type, limit_value, used_value)
SELECT 
    org_id,
    'users',
    5,
    1 -- Admin user already created
FROM organizations 
WHERE name = 'Default Organization'
ON CONFLICT DO NOTHING;

-- Grant necessary permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO bwenge;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO bwenge;

-- Print completion message
DO $$
BEGIN
    RAISE NOTICE 'Bwenge OS database initialization completed successfully!';
    RAISE NOTICE 'Default admin user: admin@bwenge.com / admin123';
    RAISE NOTICE 'Default organization: Default Organization';
END $$;