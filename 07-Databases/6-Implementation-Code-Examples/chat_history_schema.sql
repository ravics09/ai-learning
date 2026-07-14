-- ============================================================================
-- chat_history_schema.sql
-- Durable conversation state for an LLM assistant / agent.
--
-- WHY this exists:
--   LLMs are stateless per call. To have "memory", the application must persist
--   conversations and messages and reload the relevant turns on each request.
--   We model it relationally so we get referential integrity, cheap ordered
--   reads, and easy analytics (tokens, cost) -- while keeping the *hot* recent
--   turns in Redis for speed.
-- ============================================================================

-- gen_random_uuid() lives in pgcrypto on some installs; on PG13+ it's built in.
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- ---------------------------------------------------------------------------
-- One row per chat session.
-- WHY UUID PK: conversation ids are often exposed in URLs/clients; UUIDs avoid
--   leaking counts and are safe to generate client-side.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS conversations (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     BIGINT      NOT NULL,
    title       TEXT,                         -- often auto-summarized from turn 1
    model       TEXT,                         -- which model powered this session
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ---------------------------------------------------------------------------
-- One row per turn (message).
-- WHY role CHECK: prevents garbage roles that would break prompt assembly.
-- WHY ON DELETE CASCADE: deleting a conversation should clean up its messages
--   in one atomic operation (GDPR "delete my data" becomes a single DELETE).
-- WHY token_count/cost: lets you trim to fit the context window and attribute
--   spend per user/conversation.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS messages (
    id              BIGSERIAL PRIMARY KEY,
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    role            TEXT NOT NULL CHECK (role IN ('system','user','assistant','tool')),
    content         TEXT NOT NULL,
    token_count     INT,
    cost_usd        NUMERIC(10,6),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ---------------------------------------------------------------------------
-- THE hot-path index. The dominant query is:
--   "give me this conversation's turns in chronological order".
-- A composite (conversation_id, created_at) index serves the filter AND the
-- ordering, so no extra sort step. This is the single most important index here.
-- ---------------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_messages_convo_time
    ON messages (conversation_id, created_at);

-- Load the most recent N turns to build the next prompt (newest first, then
-- reverse in app code). LIMIT keeps us inside the model's context window.
-- SELECT role, content
-- FROM messages
-- WHERE conversation_id = $1
-- ORDER BY created_at DESC
-- LIMIT 20;

-- ---------------------------------------------------------------------------
-- OPTIONAL: agent checkpoints so long-running workflows resume after a restart
-- or deploy. Store opaque JSON state keyed by (conversation, step).
-- WHY JSONB: agent state shapes evolve fast; JSONB avoids constant migrations
--   while still being queryable/indexable if needed.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS agent_checkpoints (
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    step            INT  NOT NULL,
    state           JSONB NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (conversation_id, step)
);

-- Keep updated_at fresh whenever a new message lands (trigger example).
CREATE OR REPLACE FUNCTION touch_conversation() RETURNS trigger AS $$
BEGIN
    UPDATE conversations SET updated_at = now() WHERE id = NEW.conversation_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_touch_conversation ON messages;
CREATE TRIGGER trg_touch_conversation
    AFTER INSERT ON messages
    FOR EACH ROW EXECUTE FUNCTION touch_conversation();
