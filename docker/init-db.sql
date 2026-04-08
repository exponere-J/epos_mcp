-- ============================================================================
-- EPOS PostgreSQL Initialization Script
-- File: C:\Users\Jamie\workspace\epos_mcp\docker\init-db.sql
--
-- Runs automatically on first container start via docker-entrypoint-initdb.d.
-- Creates:
--   1. Separate 'n8n' database for workflow engine
--   2. EPOS schema with 7 core tables in 'epos' database
--
-- CONSTITUTIONAL AUTHORITY: EPOS Constitution v3.1
-- ============================================================================

-- ==========================================================================
-- DATABASE: n8n (separate database for workflow engine isolation)
-- ==========================================================================
CREATE DATABASE n8n;

-- ==========================================================================
-- SCHEMA: epos_core (all EPOS tables live here)
-- ==========================================================================
CREATE SCHEMA IF NOT EXISTS epos_core;

-- ==========================================================================
-- TABLE 1: LEADS (CRM)
-- Maps to: Revenue Flywheel + Sales Brain Node
-- ==========================================================================
CREATE TABLE epos_core.leads (
    lead_id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name            TEXT NOT NULL,
    email           TEXT,
    company         TEXT,
    source          TEXT,                                          -- linkedin, twitter, referral, organic, paid
    score           INTEGER DEFAULT 0 CHECK (score >= 0 AND score <= 100),
    tier            INTEGER DEFAULT 4 CHECK (tier >= 1 AND tier <= 4),  -- 1=white-glove, 4=self-service
    status          TEXT DEFAULT 'new',                            -- new, engaged, qualified, converted, lost
    touchpoint_count INTEGER DEFAULT 0,
    last_contact    TIMESTAMPTZ,
    assigned_steward TEXT,
    niche           TEXT,                                          -- agency, saas, local_service
    notes           TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_leads_score ON epos_core.leads(score DESC);
CREATE INDEX idx_leads_status ON epos_core.leads(status);
CREATE INDEX idx_leads_tier ON epos_core.leads(tier);

-- ==========================================================================
-- TABLE 2: MISSIONS
-- Maps to: Agent Zero Executor + Governance Gate
-- ==========================================================================
CREATE TABLE epos_core.missions (
    mission_id              TEXT PRIMARY KEY,
    title                   TEXT NOT NULL,
    priority                TEXT NOT NULL DEFAULT 'MEDIUM',        -- CRITICAL, HIGH, MEDIUM, LOW
    status                  TEXT NOT NULL DEFAULT 'proposed',      -- proposed, approved, executing, complete, failed
    assigned_agent          TEXT DEFAULT 'agent-zero',
    sprint                  TEXT,
    week                    TEXT,
    estimated_duration      TEXT,
    actual_duration_minutes INTEGER,
    execution_log_path      TEXT,
    constitutional_authority TEXT DEFAULT 'EPOS_CONSTITUTION_v3.1.md',
    dependencies            JSONB DEFAULT '[]'::jsonb,
    tasks                   JSONB DEFAULT '[]'::jsonb,
    created_at              TIMESTAMPTZ DEFAULT NOW(),
    completed_at            TIMESTAMPTZ
);

CREATE INDEX idx_missions_status ON epos_core.missions(status);
CREATE INDEX idx_missions_priority ON epos_core.missions(priority);

-- ==========================================================================
-- TABLE 3: CONTENT PIPELINE
-- Maps to: Content Lab + Platform Strategist Nodes
-- ==========================================================================
CREATE TABLE epos_core.content_pipeline (
    content_id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    content_type        TEXT NOT NULL,                             -- video, post, article, email, thread, carousel
    platform            TEXT NOT NULL,                             -- linkedin, twitter, youtube, tiktok, email, blog
    status              TEXT DEFAULT 'spark',                      -- spark, script, produced, validated, published
    creator_node        TEXT,                                      -- which EPOS node generated this
    brand_voice_score   NUMERIC(3,2),                             -- 0.00 to 1.00
    title               TEXT,
    body                TEXT,
    media_urls          JSONB DEFAULT '[]'::jsonb,
    engagement_metrics  JSONB DEFAULT '{}'::jsonb,                -- likes, shares, comments, impressions
    derivatives_count   INTEGER DEFAULT 0,
    source_spark_id     UUID REFERENCES epos_core.content_pipeline(content_id),
    niche_target        TEXT,                                      -- agency, saas, local_service
    published_at        TIMESTAMPTZ,
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    updated_at          TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_content_status ON epos_core.content_pipeline(status);
CREATE INDEX idx_content_platform ON epos_core.content_pipeline(platform);

-- ==========================================================================
-- TABLE 4: PROJECTS / FULFILLMENT
-- Maps to: CRM-PM Integration + Advisory Architecture
-- ==========================================================================
CREATE TABLE epos_core.projects (
    project_id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_lead_id      UUID REFERENCES epos_core.leads(lead_id),
    service_tier        TEXT NOT NULL,                             -- self-service, guided, white-glove, custom
    title               TEXT NOT NULL,
    description         TEXT,
    milestones          JSONB DEFAULT '[]'::jsonb,                -- [{name, due_date, status, deliverables}]
    status              TEXT DEFAULT 'initiated',                  -- initiated, active, review, delivered, closed
    start_date          DATE,
    delivery_date       DATE,
    deliverables_count  INTEGER DEFAULT 0,
    satisfaction_score  NUMERIC(3,2),                             -- 0.00 to 1.00
    revenue             NUMERIC(12,2) DEFAULT 0,
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    updated_at          TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_projects_status ON epos_core.projects(status);
CREATE INDEX idx_projects_client ON epos_core.projects(client_lead_id);

-- ==========================================================================
-- TABLE 5: NODE REGISTRY
-- Maps to: Microsystem Architecture + Sovereignty Suite
-- ==========================================================================
CREATE TABLE epos_core.node_registry (
    node_id             TEXT PRIMARY KEY,
    name                TEXT NOT NULL,
    node_type           TEXT NOT NULL,                             -- content, sales, governance, intelligence, platform
    port                INTEGER,
    status              TEXT DEFAULT 'registered',                 -- registered, active, degraded, offline
    health_score        INTEGER DEFAULT 100 CHECK (health_score >= 0 AND health_score <= 100),
    last_heartbeat      TIMESTAMPTZ,
    version             TEXT DEFAULT '1.0.0',
    pricing_tier        TEXT,                                      -- free, starter, pro, enterprise
    monthly_revenue     NUMERIC(10,2) DEFAULT 0,
    config              JSONB DEFAULT '{}'::jsonb,
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    updated_at          TIMESTAMPTZ DEFAULT NOW()
);

-- ==========================================================================
-- TABLE 6: ADVISORY REQUESTS
-- Maps to: Three-Tier Advisory + HITL Flow
-- ==========================================================================
CREATE TABLE epos_core.advisory_requests (
    request_id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_lead_id      UUID REFERENCES epos_core.leads(lead_id),
    tier                TEXT NOT NULL,                             -- self-service, guided, white-glove
    topic               TEXT NOT NULL,
    urgency             TEXT DEFAULT 'normal',                     -- low, normal, high, critical
    assigned_advisor     TEXT,
    status              TEXT DEFAULT 'received',                   -- received, triaged, in-progress, resolved, escalated
    resolution_notes    TEXT,
    satisfaction_score  NUMERIC(3,2),
    hitl_required       BOOLEAN DEFAULT FALSE,
    hitl_decision       TEXT,                                      -- approved, rejected, deferred
    hitl_decided_at     TIMESTAMPTZ,
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    resolved_at         TIMESTAMPTZ
);

CREATE INDEX idx_advisory_status ON epos_core.advisory_requests(status);
CREATE INDEX idx_advisory_urgency ON epos_core.advisory_requests(urgency);

-- ==========================================================================
-- TABLE 7: EXECUTION LOGS
-- Maps to: Event Bus + Shadow Logs + Soil Samples
-- ==========================================================================
CREATE TABLE epos_core.execution_logs (
    log_id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    mission_id              TEXT REFERENCES epos_core.missions(mission_id),
    agent                   TEXT NOT NULL DEFAULT 'agent-zero',
    action                  TEXT NOT NULL,
    status                  TEXT NOT NULL,                         -- success, failed, timeout, skipped
    input_hash              TEXT,                                  -- SHA256 of input for deduplication
    output_hash             TEXT,                                  -- SHA256 of output for verification
    duration_ms             INTEGER,
    error_trace             TEXT,
    constitutional_compliance BOOLEAN DEFAULT TRUE,
    shadow_data             JSONB DEFAULT '{}'::jsonb,             -- implicit value signals
    soil_sample             JSONB DEFAULT '{}'::jsonb,             -- ground-truth market signals
    created_at              TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_execlog_mission ON epos_core.execution_logs(mission_id);
CREATE INDEX idx_execlog_status ON epos_core.execution_logs(status);
CREATE INDEX idx_execlog_created ON epos_core.execution_logs(created_at DESC);

-- ==========================================================================
-- NOTIFICATION TRIGGERS — Fire events for n8n webhook consumption
-- ==========================================================================

-- Function to notify on changes (n8n listens via pg_notify or polling)
CREATE OR REPLACE FUNCTION epos_core.notify_change()
RETURNS TRIGGER AS $$
BEGIN
    PERFORM pg_notify(
        'epos_events',
        json_build_object(
            'table', TG_TABLE_NAME,
            'operation', TG_OP,
            'id', CASE
                WHEN TG_OP = 'DELETE' THEN OLD.lead_id::text
                ELSE NEW.lead_id::text
            END,
            'timestamp', NOW()
        )::text
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Lead score change trigger (fires Steward Alert for score > 85)
CREATE OR REPLACE FUNCTION epos_core.check_lead_score()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.score >= 85 AND (OLD.score IS NULL OR OLD.score < 85) THEN
        PERFORM pg_notify(
            'steward_alert',
            json_build_object(
                'type', 'hot_lead',
                'lead_id', NEW.lead_id,
                'name', NEW.name,
                'score', NEW.score,
                'tier', NEW.tier,
                'timestamp', NOW()
            )::text
        );
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_lead_score_alert
    AFTER UPDATE OF score ON epos_core.leads
    FOR EACH ROW
    EXECUTE FUNCTION epos_core.check_lead_score();

-- Mission completion trigger
CREATE OR REPLACE FUNCTION epos_core.on_mission_complete()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.status = 'complete' AND OLD.status != 'complete' THEN
        NEW.completed_at = NOW();
        PERFORM pg_notify(
            'epos_events',
            json_build_object(
                'type', 'mission.completed',
                'mission_id', NEW.mission_id,
                'title', NEW.title,
                'timestamp', NOW()
            )::text
        );
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_mission_complete
    BEFORE UPDATE OF status ON epos_core.missions
    FOR EACH ROW
    EXECUTE FUNCTION epos_core.on_mission_complete();

-- Updated_at auto-refresh for all tables with updated_at column
CREATE OR REPLACE FUNCTION epos_core.update_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_leads_updated BEFORE UPDATE ON epos_core.leads
    FOR EACH ROW EXECUTE FUNCTION epos_core.update_timestamp();
CREATE TRIGGER trg_content_updated BEFORE UPDATE ON epos_core.content_pipeline
    FOR EACH ROW EXECUTE FUNCTION epos_core.update_timestamp();
CREATE TRIGGER trg_projects_updated BEFORE UPDATE ON epos_core.projects
    FOR EACH ROW EXECUTE FUNCTION epos_core.update_timestamp();
CREATE TRIGGER trg_nodes_updated BEFORE UPDATE ON epos_core.node_registry
    FOR EACH ROW EXECUTE FUNCTION epos_core.update_timestamp();

-- ==========================================================================
-- SEED DATA: Register core EPOS nodes
-- ==========================================================================
INSERT INTO epos_core.node_registry (node_id, name, node_type, port, status, version) VALUES
    ('research-engine',     'Research Engine',          'content',      8010, 'registered', '1.0.0'),
    ('analysis-engine',     'Analysis Engine',          'content',      8011, 'registered', '1.0.0'),
    ('content-generator',   'Content Generator',        'content',      8012, 'registered', '1.0.0'),
    ('validation-engine',   'Validation Engine',        'governance',   8013, 'registered', '1.0.0'),
    ('publisher',           'Publisher Orchestrator',   'content',      8014, 'registered', '1.0.0'),
    ('market-awareness',    'Market Awareness Engine',  'intelligence', 8015, 'registered', '1.0.0'),
    ('sales-brain',         'Sales Brain',              'sales',        8016, 'registered', '1.0.0'),
    ('epos-doctor',         'EPOS Doctor',              'governance',   NULL, 'active',     '3.2.0'),
    ('governance-gate',     'Governance Gate',          'governance',   NULL, 'active',     '2.0.0'),
    ('context-vault',       'Context Vault',            'intelligence', NULL, 'active',     '1.0.0'),
    ('event-bus',           'Event Bus',                'governance',   NULL, 'active',     '1.0.0'),
    ('agent-zero',          'Agent Zero',               'intelligence', 50080,'active',     '0.9.7'),
    ('phi3-command',        'Phi-3 Command Center',     'intelligence', NULL, 'active',     '1.0.0')
ON CONFLICT (node_id) DO NOTHING;

-- ==========================================================================
-- GRANT ACCESS — NocoDB and n8n will connect as epos_admin
-- ==========================================================================
GRANT ALL ON SCHEMA epos_core TO epos_admin;
GRANT ALL ON ALL TABLES IN SCHEMA epos_core TO epos_admin;
GRANT ALL ON ALL SEQUENCES IN SCHEMA epos_core TO epos_admin;
ALTER DEFAULT PRIVILEGES IN SCHEMA epos_core GRANT ALL ON TABLES TO epos_admin;
