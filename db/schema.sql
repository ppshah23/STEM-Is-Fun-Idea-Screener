-- Read-side mirror of the file-based pipeline output.
--
-- output/{ideas,levels,reviews,roadmaps,drafts,approved} (see pipeline/io.py)
-- remain the source of truth. This database is populated by db/backfill.py
-- so the results can be queried/reported on (e.g. a dashboard) -- nothing in
-- the pipeline writes to it directly, and losing this database loses no data
-- that isn't already on disk under output/.

CREATE TABLE IF NOT EXISTS ideas (
    id TEXT PRIMARY KEY,                       -- output/ideas/<id>.json filename stem
    idea_text TEXT NOT NULL,
    summary TEXT NOT NULL,
    verdict TEXT NOT NULL CHECK (
        verdict IN ('feasible', 'feasible_with_changes', 'needs_more_info', 'not_feasible')
    ),
    overall_score INTEGER NOT NULL,
    safety_override BOOLEAN NOT NULL,
    checks JSONB NOT NULL,                      -- {dimension: {score, pass, notes, weight}}
    blocking_issues JSONB NOT NULL DEFAULT '[]',
    open_questions JSONB NOT NULL DEFAULT '[]',
    suggested_changes JSONB NOT NULL DEFAULT '[]',
    suggested_parts JSONB NOT NULL DEFAULT '[]', -- [{name, url, note}]
    mock BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL,             -- parsed from the filename's UTC timestamp
    backfilled_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS levels (
    id TEXT PRIMARY KEY,                       -- output/levels/<id>.json filename stem
    idea_text TEXT NOT NULL,
    summary TEXT NOT NULL,
    level TEXT NOT NULL CHECK (level IN ('level_1', 'level_2', 'level_3')),
    level_label TEXT NOT NULL,                  -- Guided | Driven | Review
    existing_artifact_override BOOLEAN NOT NULL,
    matrix JSONB NOT NULL,                      -- per-candidate Pugh-matrix scoring detail
    signals JSONB NOT NULL,                     -- raw {dimension: {score, notes}}
    mock BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL,
    backfilled_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS reviews (
    id TEXT PRIMARY KEY,                       -- output/reviews/<id>.json filename stem
    curriculum_text TEXT NOT NULL,
    constraints TEXT,
    summary TEXT NOT NULL,
    strengths JSONB NOT NULL DEFAULT '[]',
    cut_candidates JSONB NOT NULL DEFAULT '[]',    -- [{item, reason}]
    add_candidates JSONB NOT NULL DEFAULT '[]',    -- [{item, reason}]
    adjust_candidates JSONB NOT NULL DEFAULT '[]', -- [{item, reason}]
    open_questions JSONB NOT NULL DEFAULT '[]',
    restructured_outline JSONB NOT NULL DEFAULT '[]', -- [{day, title, slides[]}]
    created_at TIMESTAMPTZ NOT NULL,
    backfilled_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS roadmaps (
    id TEXT PRIMARY KEY,                       -- output/roadmaps/<id>.json filename stem
    idea_text TEXT NOT NULL,
    title TEXT NOT NULL,
    total_sessions INTEGER NOT NULL,
    session_length_minutes INTEGER NOT NULL,
    duration_summary TEXT NOT NULL,
    days JSONB NOT NULL,                        -- [{day, title, summary, key_activities[], materials[]}]
    open_questions JSONB NOT NULL DEFAULT '[]',
    shopping_list JSONB NOT NULL DEFAULT '[]',  -- [{name, url, note}]
    created_at TIMESTAMPTZ NOT NULL,
    backfilled_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- output/drafts/<course_id>_<persona_id>.json, moved to output/approved/ on
-- approval (pipeline.io.approve_draft). course_id/persona_id are split from
-- the filename on a best-effort basis (first underscore) since the pipeline
-- doesn't persist them separately -- treat as a convenience, not a guarantee.
CREATE TABLE IF NOT EXISTS drafts (
    id TEXT PRIMARY KEY,
    course_id TEXT,
    persona_id TEXT,
    status TEXT NOT NULL DEFAULT 'draft' CHECK (status IN ('draft', 'approved')),
    analysis JSONB,
    lesson_plan JSONB,
    slide_outline JSONB,
    evaluation JSONB,
    created_at TIMESTAMPTZ,                     -- file mtime; no timestamp in the filename
    approved_at TIMESTAMPTZ,
    backfilled_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_ideas_verdict ON ideas (verdict);
CREATE INDEX IF NOT EXISTS idx_ideas_created_at ON ideas (created_at);
CREATE INDEX IF NOT EXISTS idx_levels_level ON levels (level);
CREATE INDEX IF NOT EXISTS idx_roadmaps_created_at ON roadmaps (created_at);
CREATE INDEX IF NOT EXISTS idx_drafts_status ON drafts (status);
