from .lead_model import db
from sqlalchemy import text

class AuditLog(db.Model):
    __tablename__ = 'lead_audit_log'

    id = db.Column(db.Integer, primary_key=True)
    table_name = db.Column(db.String, nullable=False)
    row_id = db.Column(db.Integer, nullable=False)
    column_name = db.Column(db.String, nullable=False)
    old_value = db.Column(db.Text)
    new_value = db.Column(db.Text)
    username = db.Column(db.String, nullable=False)
    changed_at = db.Column(db.DateTime, nullable=False)

def ensure_audit_log_infrastructure(db):
    audit_sql = '''
    CREATE TABLE IF NOT EXISTS lead_audit_log (
        id SERIAL PRIMARY KEY,
        table_name TEXT NOT NULL,
        row_id INTEGER NOT NULL,
        column_name TEXT NOT NULL,
        old_value TEXT,
        new_value TEXT,
        username TEXT NOT NULL,
        changed_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
    );

    CREATE OR REPLACE FUNCTION set_app_user(username TEXT) RETURNS VOID AS $$
    BEGIN
        PERFORM set_config('app.current_user', username, FALSE);
    END;
    $$ LANGUAGE plpgsql;

    CREATE OR REPLACE FUNCTION audit_lead_changes() RETURNS TRIGGER AS $$
    DECLARE
        app_user TEXT;
        col_name TEXT;
        old_val TEXT;
        new_val TEXT;
    BEGIN
        app_user := current_setting('app.current_user', TRUE);
        IF app_user IS NULL THEN
            app_user := session_user;
        END IF;

        -- Special handling for soft delete
        IF NEW.deleted = TRUE AND OLD.deleted = FALSE THEN
            EXECUTE format('INSERT INTO lead_audit_log (table_name, row_id, column_name, old_value, new_value, username, changed_at) VALUES (%L, %s, %L, %L, %L, %L, now())',
                TG_TABLE_NAME,
                OLD.id,
                'LEAD_DELETED',
                'false',
                'true',
                app_user
            );
        END IF;

        FOR col_name IN SELECT column_name 
                          FROM information_schema.columns 
                          WHERE table_name = TG_TABLE_NAME 
                          AND table_schema = TG_TABLE_SCHEMA
        LOOP
            -- Skip updated_at column
            IF col_name = 'updated_at' THEN
                CONTINUE;
            END IF;
            BEGIN
                EXECUTE format('SELECT ($1).%I::text', col_name) INTO old_val USING OLD;
                EXECUTE format('SELECT ($1).%I::text', col_name) INTO new_val USING NEW;
                IF old_val IS DISTINCT FROM new_val THEN
                    EXECUTE format('INSERT INTO lead_audit_log (table_name, row_id, column_name, old_value, new_value, username, changed_at) VALUES (%L, %s, %L, %L, %L, %L, now())',
                        TG_TABLE_NAME,
                        OLD.id,
                        col_name,
                        old_val,
                        new_val,
                        app_user
                    );
                END IF;
            EXCEPTION WHEN undefined_column THEN
                NULL;
            END;
        END LOOP;
        RETURN NEW;
    END;
    $$ LANGUAGE plpgsql;

    DO $$
    BEGIN
        IF NOT EXISTS (
            SELECT 1 FROM pg_trigger WHERE tgname = 'leads_audit_trigger'
        ) THEN
            EXECUTE 'CREATE TRIGGER leads_audit_trigger AFTER UPDATE ON lead FOR EACH ROW EXECUTE FUNCTION audit_lead_changes();';
        END IF;
    END $$;
    '''
    try:
        db.session.execute(text(audit_sql))
        db.session.commit()
    except Exception as e:
        print("[Audit log setup] Warning:", e) 