"""Initial schema: every entity of database/DATABASE_SCHEMA.md sections 4.2-4.7.

Physical naming is snake_case (spec section 4.1 allows this as an
implementation detail). Logical-to-physical name mapping:
User -> app_user and Grant -> access_grant (reserved words); all other
entities keep their names in snake_case. Enums are text columns with CHECK
constraints so that enum expansion stays additive (spec section 4.8).
Partial dates (spec section 4.1) are a date column plus a _precision column.
Vector ANN indexes are deliberately absent: section 4.7 requires one index
per ACTIVE embedding_model_version, and none is active until MVP-016.

Revision ID: 0001
Revises:
Create Date: 2026-07-03
"""

from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None

PRECISIONS = "('exact','day','month','year','approximate')"
TIERS = "('P0','P1','P2','P3')"


def base_cols(tier_default: str | None = "'P2'", with_tier: bool = True) -> str:
    """Common base fields per DATABASE_SCHEMA section 4.2."""
    if not with_tier:
        tier = ""
    else:
        default = f"DEFAULT {tier_default} " if tier_default is not None else ""
        tier = f"privacy_tier text NOT NULL {default}CHECK (privacy_tier IN {TIERS}),"
    return f"""
        id uuid PRIMARY KEY DEFAULT uuid_v7(),
        created_at timestamptz NOT NULL DEFAULT now(),
        updated_at timestamptz NOT NULL DEFAULT now(),
        deleted_at timestamptz,
        {tier}
        created_by uuid NOT NULL REFERENCES app_user(id),
        origin_type text NOT NULL DEFAULT 'manual'
            CHECK (origin_type IN ('manual','ingestion','agent','system')),
        origin_ref_type text,
        origin_ref_id uuid,
        row_version integer NOT NULL DEFAULT 1
    """


def partial_date(prefix: str) -> str:
    return f"""
        {prefix}_date date,
        {prefix}_precision text CHECK ({prefix}_precision IN {PRECISIONS}),
        CHECK (({prefix}_date IS NULL) = ({prefix}_precision IS NULL))
    """


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")

    # Time-ordered UUID v7 (spec section 4.1 'identifier'); native in future
    # Postgres versions, generated here until then.
    op.execute("""
        CREATE OR REPLACE FUNCTION uuid_v7() RETURNS uuid AS $$
        SELECT encode(
            set_bit(set_bit(
                overlay(uuid_send(gen_random_uuid())
                    placing substring(int8send((extract(epoch FROM clock_timestamp()) * 1000)::bigint) FROM 3)
                    FROM 1 FOR 6),
                52, 1), 53, 1),
            'hex')::uuid;
        $$ LANGUAGE sql VOLATILE;
    """)

    # updated_at and row_version maintenance (section 4.2).
    op.execute("""
        CREATE OR REPLACE FUNCTION touch_row() RETURNS trigger AS $$
        BEGIN
            NEW.updated_at := now();
            NEW.row_version := OLD.row_version + 1;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)

    # ------------------------------------------------------------------
    # System principals first: every table's created_by references app_user.
    # ------------------------------------------------------------------
    op.execute(f"""
        CREATE TABLE app_user (
            {base_cols(with_tier=False)},
            email text NOT NULL,
            display_name text NOT NULL,
            auth_subject text,
            user_kind text NOT NULL CHECK (user_kind IN ('human','service')),
            account_status text NOT NULL DEFAULT 'active'
                CHECK (account_status IN ('active','suspended','revoked')),
            is_owner boolean NOT NULL DEFAULT false,
            last_login_at timestamptz
        )
    """)
    op.execute(
        "CREATE UNIQUE INDEX uq_app_user_email ON app_user (lower(email)) "
        "WHERE deleted_at IS NULL"
    )
    op.execute(
        "CREATE UNIQUE INDEX uq_app_user_auth_subject ON app_user (auth_subject) "
        "WHERE auth_subject IS NOT NULL AND deleted_at IS NULL"
    )
    op.execute(
        "CREATE UNIQUE INDEX uq_app_user_single_owner ON app_user ((true)) "
        "WHERE is_owner AND deleted_at IS NULL"
    )

    op.execute(f"""
        CREATE TABLE role (
            {base_cols(with_tier=False)},
            name text NOT NULL CHECK (name IN ('owner','steward','trusted','public','service')),
            description text NOT NULL,
            max_privacy_tier text NOT NULL CHECK (max_privacy_tier IN {TIERS})
        )
    """)
    op.execute("CREATE UNIQUE INDEX uq_role_name ON role (name) WHERE deleted_at IS NULL")

    op.execute(f"""
        CREATE TABLE access_grant (
            {base_cols(with_tier=False)},
            user_id uuid NOT NULL REFERENCES app_user(id),
            role_id uuid NOT NULL REFERENCES role(id),
            scope_type text NOT NULL CHECK (scope_type IN ('global','collection','entity')),
            scope_ref_type text,
            scope_ref_id uuid,
            granted_by uuid NOT NULL REFERENCES app_user(id),
            expires_at timestamptz,
            activation_condition jsonb,
            CHECK ((scope_type = 'global') = (scope_ref_type IS NULL AND scope_ref_id IS NULL))
        )
    """)
    op.execute("""
        CREATE UNIQUE INDEX uq_access_grant_scope ON access_grant
        (user_id, role_id, scope_type,
         COALESCE(scope_ref_type, ''), COALESCE(scope_ref_id, '00000000-0000-0000-0000-000000000000'::uuid))
        WHERE deleted_at IS NULL
    """)

    # ------------------------------------------------------------------
    # Knowledge entities (section 4.3).
    # ------------------------------------------------------------------
    op.execute(f"""
        CREATE TABLE person (
            {base_cols()},
            full_name text NOT NULL,
            aliases jsonb,
            relationship_to_owner text,
            bio text,
            links jsonb
        )
    """)
    op.execute("CREATE INDEX ix_person_full_name_trgm ON person USING gin (full_name gin_trgm_ops)")

    op.execute(f"""
        CREATE TABLE organization (
            {base_cols()},
            name text NOT NULL,
            org_type text NOT NULL
                CHECK (org_type IN ('company','community','school','program','nonprofit','other')),
            description text,
            links jsonb
        )
    """)
    op.execute(
        "CREATE UNIQUE INDEX uq_organization_name ON organization (lower(name)) "
        "WHERE deleted_at IS NULL"
    )
    op.execute(
        "CREATE INDEX ix_organization_name_trgm ON organization USING gin (name gin_trgm_ops)"
    )

    op.execute(f"""
        CREATE TABLE project (
            {base_cols()},
            name text NOT NULL,
            slug text NOT NULL,
            status text NOT NULL
                CHECK (status IN ('concept','active','paused','shipped','archived')),
            summary text,
            description text,
            {partial_date("started_on")},
            {partial_date("ended_on")},
            links jsonb,
            featured boolean NOT NULL DEFAULT false
        )
    """)
    op.execute(
        "CREATE UNIQUE INDEX uq_project_slug ON project (slug) WHERE deleted_at IS NULL"
    )
    op.execute(
        "CREATE INDEX ix_project_description_fts ON project "
        "USING gin (to_tsvector('english', coalesce(description, '')))"
    )

    op.execute(f"""
        CREATE TABLE artifact (
            {base_cols()},
            title text NOT NULL,
            artifact_type text NOT NULL CHECK (artifact_type IN
                ('document','photo','video','presentation','code_snapshot','audio','dataset','other')),
            storage_ref text NOT NULL,
            mime_type text NOT NULL,
            byte_size bigint NOT NULL,
            checksum text NOT NULL,
            captured_at timestamptz,
            canonical_markdown text,
            extraction_status text NOT NULL DEFAULT 'pending' CHECK (extraction_status IN
                ('pending','extracted','partial','not_applicable','failed'))
        )
    """)
    op.execute(
        "CREATE UNIQUE INDEX uq_artifact_checksum ON artifact (checksum) WHERE deleted_at IS NULL"
    )

    op.execute(f"""
        CREATE TABLE event (
            {base_cols()},
            title text NOT NULL,
            event_type text NOT NULL CHECK (event_type IN
                ('milestone','talk_event','hackathon','launch','education','personal','community','other')),
            starts_at timestamptz NOT NULL,
            ends_at timestamptz,
            date_precision text NOT NULL CHECK (date_precision IN {PRECISIONS}),
            location text,
            description text
        )
    """)
    op.execute("CREATE INDEX ix_event_timeline ON event (starts_at, event_type)")
    op.execute("CREATE INDEX ix_event_precision ON event (date_precision)")

    op.execute(f"""
        CREATE TABLE idea (
            {base_cols()},
            title text NOT NULL,
            body text,
            status text NOT NULL DEFAULT 'spark'
                CHECK (status IN ('spark','exploring','parked','promoted','discarded')),
            promoted_project_id uuid REFERENCES project(id)
        )
    """)

    op.execute(f"""
        CREATE TABLE note (
            {base_cols()},
            title text,
            body text NOT NULL,
            note_context text
        )
    """)
    op.execute(
        "CREATE INDEX ix_note_body_fts ON note "
        "USING gin (to_tsvector('english', coalesce(body, '')))"
    )

    # JournalEntry defaults to P3 sealed (section 4.2 and 4.3).
    op.execute(f"""
        CREATE TABLE journal_entry (
            {base_cols(tier_default="'P3'")},
            entry_date date NOT NULL,
            title text,
            body text NOT NULL,
            entry_kind text NOT NULL DEFAULT 'freeform'
                CHECK (entry_kind IN ('daily','reflection','prayer','gratitude','freeform'))
        )
    """)
    op.execute(
        "CREATE INDEX ix_journal_entry_body_fts ON journal_entry "
        "USING gin (to_tsvector('english', coalesce(body, '')))"
    )

    op.execute(f"""
        CREATE TABLE conversation (
            {base_cols()},
            title text,
            channel text NOT NULL CHECK (channel IN ('twin','ask','agent','imported')),
            participant_user_id uuid REFERENCES app_user(id),
            started_at timestamptz NOT NULL,
            transcript jsonb NOT NULL,
            summary text,
            token_count integer
        )
    """)

    op.execute(f"""
        CREATE TABLE skill (
            {base_cols()},
            name text NOT NULL,
            category text NOT NULL CHECK (category IN
                ('language','framework','platform','domain','practice','leadership','other')),
            evidence_level text NOT NULL DEFAULT 'claimed'
                CHECK (evidence_level IN ('demonstrated','claimed')),
            description text
        )
    """)
    op.execute("CREATE UNIQUE INDEX uq_skill_name ON skill (lower(name)) WHERE deleted_at IS NULL")

    op.execute(f"""
        CREATE TABLE certification (
            {base_cols()},
            name text NOT NULL,
            issuer_org_id uuid REFERENCES organization(id),
            {partial_date("issued_on")},
            expires_on date,
            credential_url text,
            status text NOT NULL DEFAULT 'claimed'
                CHECK (status IN ('active','expired','in_progress','claimed'))
        )
    """)

    op.execute(f"""
        CREATE TABLE achievement (
            {base_cols()},
            title text NOT NULL,
            {partial_date("achieved_on")},
            description text,
            awarding_org_id uuid REFERENCES organization(id)
        )
    """)

    op.execute(f"""
        CREATE TABLE goal (
            {base_cols()},
            title text NOT NULL,
            description text,
            horizon text NOT NULL CHECK (horizon IN ('quarter','year','decade','lifetime')),
            status text NOT NULL DEFAULT 'active'
                CHECK (status IN ('active','achieved','revised','dropped')),
            target_date date
        )
    """)

    op.execute(f"""
        CREATE TABLE lesson (
            {base_cols()},
            title text NOT NULL,
            body text NOT NULL,
            {partial_date("learned_on")}
        )
    """)

    op.execute(f"""
        CREATE TABLE book (
            {base_cols()},
            title text NOT NULL,
            authors jsonb NOT NULL,
            isbn text,
            reading_status text NOT NULL DEFAULT 'to_read'
                CHECK (reading_status IN ('to_read','reading','finished','abandoned')),
            {partial_date("finished_on")},
            takeaways text
        )
    """)
    op.execute(
        "CREATE UNIQUE INDEX uq_book_isbn ON book (isbn) "
        "WHERE isbn IS NOT NULL AND deleted_at IS NULL"
    )

    op.execute(f"""
        CREATE TABLE talk (
            {base_cols()},
            title text NOT NULL,
            {partial_date("delivered_on")},
            venue text,
            event_id uuid REFERENCES event(id),
            slides_artifact_id uuid REFERENCES artifact(id),
            recording_url text
        )
    """)

    op.execute(f"""
        CREATE TABLE article (
            {base_cols()},
            title text NOT NULL,
            platform text NOT NULL
                CHECK (platform IN ('devto','linkedin','personal_site','other')),
            canonical_url text,
            {partial_date("published_on")},
            body_markdown text,
            publication_status text NOT NULL DEFAULT 'draft'
                CHECK (publication_status IN ('draft','published','retired'))
        )
    """)
    op.execute(
        "CREATE UNIQUE INDEX uq_article_canonical_url ON article (canonical_url) "
        "WHERE canonical_url IS NOT NULL AND deleted_at IS NULL"
    )
    op.execute(
        "CREATE INDEX ix_article_body_fts ON article "
        "USING gin (to_tsvector('english', coalesce(body_markdown, '')))"
    )

    op.execute(f"""
        CREATE TABLE tag (
            {base_cols()},
            name text NOT NULL,
            description text
        )
    """)
    op.execute("CREATE UNIQUE INDEX uq_tag_name ON tag (lower(name)) WHERE deleted_at IS NULL")
    op.execute("CREATE INDEX ix_tag_name_trgm ON tag USING gin (name gin_trgm_ops)")

    op.execute(f"""
        CREATE TABLE collection (
            {base_cols()},
            name text NOT NULL,
            description text,
            collection_type text NOT NULL CHECK (collection_type IN ('manual','smart')),
            smart_rule jsonb,
            CHECK ((collection_type = 'smart') = (smart_rule IS NOT NULL))
        )
    """)
    op.execute(
        "CREATE UNIQUE INDEX uq_collection_name ON collection (name) WHERE deleted_at IS NULL"
    )

    # ------------------------------------------------------------------
    # Provenance sub-model (section 4.4, ADR-10).
    # ------------------------------------------------------------------
    op.execute(f"""
        CREATE TABLE source (
            {base_cols()},
            source_type text NOT NULL CHECK (source_type IN
                ('url','document','artifact','testimony','system_record','external_api')),
            title text NOT NULL,
            url text,
            publisher text,
            accessed_at timestamptz,
            archived_artifact_id uuid REFERENCES artifact(id),
            reliability_note text
        )
    """)

    op.execute(f"""
        CREATE TABLE claim (
            {base_cols()},
            subject_type text NOT NULL,
            subject_id uuid NOT NULL,
            predicate text NOT NULL,
            statement text NOT NULL,
            confidence_tier text NOT NULL
                CHECK (confidence_tier IN ('verified','self_reported','flagged')),
            tier_rationale text,
            verified_at timestamptz,
            verified_by uuid REFERENCES app_user(id),
            review_due_at date,
            CHECK (confidence_tier = 'verified' OR (verified_at IS NULL AND verified_by IS NULL)),
            CHECK ((verified_at IS NULL) = (verified_by IS NULL))
        )
    """)
    op.execute("""
        CREATE UNIQUE INDEX uq_claim_statement ON claim
        (subject_type, subject_id, predicate, md5(statement))
        WHERE deleted_at IS NULL
    """)
    op.execute("CREATE INDEX ix_claim_subject ON claim (subject_type, subject_id)")
    op.execute("CREATE INDEX ix_claim_tier ON claim (confidence_tier)")
    op.execute(
        "CREATE INDEX ix_claim_statement_fts ON claim "
        "USING gin (to_tsvector('english', statement))"
    )

    op.execute(f"""
        CREATE TABLE claim_source (
            {base_cols(with_tier=False)},
            claim_id uuid NOT NULL REFERENCES claim(id),
            source_id uuid NOT NULL REFERENCES source(id),
            support_type text NOT NULL
                CHECK (support_type IN ('supports','contradicts','mentions')),
            note text
        )
    """)
    op.execute(
        "CREATE UNIQUE INDEX uq_claim_source ON claim_source (claim_id, source_id) "
        "WHERE deleted_at IS NULL"
    )
    op.execute("CREATE INDEX ix_claim_source_claim ON claim_source (claim_id)")
    op.execute("CREATE INDEX ix_claim_source_source ON claim_source (source_id)")

    # Never-auto-upgrade guard (section 4.4, normative behavior). Raising the
    # tier requires the service layer to assert an authorized owner-verified
    # path via the transaction-local setting legacy.tier_change_authorized;
    # reaching 'verified' additionally requires a human verifier and at least
    # one supporting ClaimSource. Downgrades are always permitted.
    op.execute("""
        CREATE OR REPLACE FUNCTION claim_tier_guard() RETURNS trigger AS $$
        DECLARE
            rank_old integer;
            rank_new integer;
            verifier_kind text;
        BEGIN
            rank_old := CASE OLD.confidence_tier
                WHEN 'flagged' THEN 0 WHEN 'self_reported' THEN 1 ELSE 2 END;
            rank_new := CASE NEW.confidence_tier
                WHEN 'flagged' THEN 0 WHEN 'self_reported' THEN 1 ELSE 2 END;

            IF rank_new > rank_old THEN
                IF current_setting('legacy.tier_change_authorized', true) IS DISTINCT FROM 'true' THEN
                    RAISE EXCEPTION 'confidence_tier may not be raised by this path (never-auto-upgrade rule, DATABASE_SCHEMA 4.4)';
                END IF;
                IF NEW.confidence_tier = 'verified' THEN
                    IF NEW.verified_by IS NULL OR NEW.verified_at IS NULL THEN
                        RAISE EXCEPTION 'verification requires verified_by and verified_at (DATABASE_SCHEMA 4.4)';
                    END IF;
                    SELECT user_kind INTO verifier_kind FROM app_user WHERE id = NEW.verified_by;
                    IF verifier_kind IS DISTINCT FROM 'human' THEN
                        RAISE EXCEPTION 'verified_by must be a human principal (DATABASE_SCHEMA 4.4)';
                    END IF;
                    IF NOT EXISTS (
                        SELECT 1 FROM claim_source cs
                        WHERE cs.claim_id = NEW.id
                          AND cs.support_type = 'supports'
                          AND cs.deleted_at IS NULL
                    ) THEN
                        RAISE EXCEPTION 'verification requires a supporting ClaimSource (DATABASE_SCHEMA 4.4)';
                    END IF;
                END IF;
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)
    op.execute("""
        CREATE TRIGGER trg_claim_tier_guard
        BEFORE UPDATE OF confidence_tier ON claim
        FOR EACH ROW WHEN (OLD.confidence_tier IS DISTINCT FROM NEW.confidence_tier)
        EXECUTE FUNCTION claim_tier_guard()
    """)

    # ------------------------------------------------------------------
    # Edge (section 4.5, ADR-05).
    # ------------------------------------------------------------------
    op.execute(f"""
        CREATE TABLE edge (
            {base_cols()},
            from_type text NOT NULL,
            from_id uuid NOT NULL,
            to_type text NOT NULL,
            to_id uuid NOT NULL,
            edge_type text NOT NULL,
            {partial_date("valid_from")},
            {partial_date("valid_to")},
            weight numeric,
            claim_id uuid REFERENCES claim(id),
            attributes jsonb
        )
    """)
    op.execute("""
        CREATE UNIQUE INDEX uq_edge_identity ON edge
        (from_type, from_id, to_type, to_id, edge_type,
         COALESCE(valid_from_date, '-infinity'::date))
        WHERE deleted_at IS NULL
    """)
    op.execute("""
        CREATE INDEX ix_edge_from ON edge (from_type, from_id, edge_type)
        INCLUDE (valid_from_date, valid_to_date)
    """)
    op.execute("""
        CREATE INDEX ix_edge_to ON edge (to_type, to_id, edge_type)
        INCLUDE (valid_from_date, valid_to_date)
    """)

    # ------------------------------------------------------------------
    # Remaining system entities (section 4.6).
    # ------------------------------------------------------------------
    op.execute(f"""
        CREATE TABLE memory_record (
            {base_cols()},
            memory_type text NOT NULL
                CHECK (memory_type IN ('episodic','semantic','procedural','reflective')),
            content text NOT NULL,
            salience numeric NOT NULL,
            source_refs jsonb,
            embedding vector NOT NULL,
            embedding_model_version text NOT NULL,
            last_accessed_at timestamptz,
            access_count integer NOT NULL DEFAULT 0,
            consolidated_from jsonb,
            expires_at timestamptz
        )
    """)

    op.execute(f"""
        CREATE TABLE embedding_chunk (
            {base_cols(tier_default=None)},
            entity_type text NOT NULL,
            entity_id uuid NOT NULL,
            chunk_index integer NOT NULL,
            chunk_text text NOT NULL,
            token_count integer NOT NULL,
            content_hash text NOT NULL,
            embedding vector NOT NULL,
            embedding_model_version text NOT NULL,
            superseded_by uuid REFERENCES embedding_chunk(id)
        )
    """)
    op.execute("""
        CREATE UNIQUE INDEX uq_embedding_chunk_position ON embedding_chunk
        (entity_type, entity_id, chunk_index, embedding_model_version)
        WHERE superseded_by IS NULL
    """)

    # Append-only audit log (ADR-11); base-field exceptions per section 4.2.
    op.execute("""
        CREATE TABLE audit_log_entry (
            id uuid PRIMARY KEY DEFAULT uuid_v7(),
            created_at timestamptz NOT NULL DEFAULT now(),
            created_by uuid NOT NULL REFERENCES app_user(id),
            origin_type text NOT NULL DEFAULT 'system'
                CHECK (origin_type IN ('manual','ingestion','agent','system')),
            origin_ref_type text,
            origin_ref_id uuid,
            sequence_number bigint GENERATED BY DEFAULT AS IDENTITY,
            occurred_at timestamptz NOT NULL DEFAULT now(),
            actor_type text NOT NULL CHECK (actor_type IN ('user','agent','system')),
            actor_id uuid NOT NULL,
            action text NOT NULL,
            subject_type text,
            subject_id uuid,
            payload_summary jsonb,
            request_id text,
            token_ref text
        )
    """)
    op.execute("CREATE UNIQUE INDEX uq_audit_sequence ON audit_log_entry (sequence_number)")
    op.execute("CREATE INDEX ix_audit_occurred_brin ON audit_log_entry USING brin (occurred_at)")
    op.execute("CREATE INDEX ix_audit_actor ON audit_log_entry (actor_type, actor_id)")
    op.execute("CREATE INDEX ix_audit_subject ON audit_log_entry (subject_type, subject_id)")
    op.execute("""
        CREATE OR REPLACE FUNCTION audit_append_only() RETURNS trigger AS $$
        BEGIN
            RAISE EXCEPTION 'audit_log_entry is append-only (ADR-11)';
        END;
        $$ LANGUAGE plpgsql;
    """)
    op.execute("""
        CREATE TRIGGER trg_audit_append_only
        BEFORE UPDATE OR DELETE ON audit_log_entry
        FOR EACH ROW EXECUTE FUNCTION audit_append_only()
    """)

    op.execute(f"""
        CREATE TABLE ingestion_job (
            {base_cols()},
            job_type text NOT NULL CHECK (job_type IN
                ('upload','github_sync','url_capture','conversation_import','bulk_import')),
            source_descriptor jsonb NOT NULL,
            status text NOT NULL DEFAULT 'queued' CHECK (status IN
                ('queued','parsing','chunking','embedding','graph_extraction','review','complete','failed','cancelled')),
            progress_percent integer CHECK (progress_percent BETWEEN 0 AND 100),
            error_detail jsonb,
            items_created jsonb
        )
    """)

    op.execute(f"""
        CREATE TABLE agent_run (
            {base_cols()},
            agent_name text NOT NULL CHECK (agent_name IN
                ('orchestrator','ingestion','curation','graph','timeline','retrieval',
                 'twin','mentor','research','writing','verification','reflection')),
            task text NOT NULL,
            status text NOT NULL DEFAULT 'planned' CHECK (status IN
                ('planned','awaiting_approval','running','paused','completed','failed','cancelled')),
            plan jsonb,
            current_step integer,
            budget_tokens integer NOT NULL,
            tokens_used integer NOT NULL DEFAULT 0,
            cost_estimate numeric,
            parent_run_id uuid REFERENCES agent_run(id),
            result_summary text
        )
    """)

    # Schema version register (section 4.8).
    op.execute("""
        CREATE TABLE schema_metadata (
            key text PRIMARY KEY,
            value text NOT NULL,
            updated_at timestamptz NOT NULL DEFAULT now()
        )
    """)
    op.execute("INSERT INTO schema_metadata (key, value) VALUES ('schema_version', '1')")

    # touch_row trigger on every mutable base-field table.
    for table in (
        "app_user", "role", "access_grant", "person", "organization", "project",
        "artifact", "event", "idea", "note", "journal_entry", "conversation",
        "skill", "certification", "achievement", "goal", "lesson", "book",
        "talk", "article", "tag", "collection", "source", "claim",
        "claim_source", "edge", "memory_record", "embedding_chunk",
        "ingestion_job", "agent_run",
    ):
        op.execute(f"""
            CREATE TRIGGER trg_touch_{table}
            BEFORE UPDATE ON {table}
            FOR EACH ROW EXECUTE FUNCTION touch_row()
        """)

    # ------------------------------------------------------------------
    # Reference data: the system service principal and the fixed Role table
    # (section 4.6: 'Roles are a small, fixed reference table'). Ceilings per
    # security/AUTHORIZATION.md section 4.1.
    # ------------------------------------------------------------------
    # The system principal self-references created_by in the same row (a
    # same-statement self-reference satisfies the foreign key). Its id is a
    # fixed, well-known UUID so seed scripts can reference it stably.
    op.execute("""
        INSERT INTO app_user
            (id, email, display_name, user_kind, account_status, is_owner,
             created_by, origin_type)
        VALUES
            ('00000000-0000-7000-8000-000000000001', 'system@legacy.invalid',
             'Legacy System', 'service', 'active', false,
             '00000000-0000-7000-8000-000000000001', 'system')
    """)
    op.execute("""
        INSERT INTO role (name, description, max_privacy_tier, created_by, origin_type)
        VALUES
            ('owner',   'The owner: ultimate authority',                  'P3',
             '00000000-0000-7000-8000-000000000001', 'system'),
            ('steward', 'Estate steward; elevated only after succession', 'P3',
             '00000000-0000-7000-8000-000000000001', 'system'),
            ('trusted', 'Trusted collaborator with scoped grants',        'P1',
             '00000000-0000-7000-8000-000000000001', 'system'),
            ('public',  'Unauthenticated or basic public visitor',        'P0',
             '00000000-0000-7000-8000-000000000001', 'system'),
            ('service', 'Agent and machine principals; never P3',         'P2',
             '00000000-0000-7000-8000-000000000001', 'system')
    """)


def downgrade() -> None:
    for table in (
        "schema_metadata", "agent_run", "ingestion_job", "audit_log_entry",
        "embedding_chunk", "memory_record", "edge", "claim_source", "claim",
        "source", "collection", "tag", "article", "talk", "book", "lesson",
        "goal", "achievement", "certification", "skill", "conversation",
        "journal_entry", "note", "idea", "event", "artifact", "project",
        "organization", "person", "access_grant", "role", "app_user",
    ):
        op.execute(f"DROP TABLE IF EXISTS {table} CASCADE")
    for fn in ("claim_tier_guard", "audit_append_only", "touch_row", "uuid_v7"):
        op.execute(f"DROP FUNCTION IF EXISTS {fn} CASCADE")
