DO $$ BEGIN
    CREATE TYPE method_enum AS ENUM ('POST', 'PUT', 'DELETE');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

CREATE TABLE IF NOT EXISTS logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    method method_enum NOT NULL,
    url VARCHAR(255) NOT NULL,
    request_body JSONB,
    response_body JSONB,
    status_code INTEGER NOT NULL,
    time_taken NUMERIC NOT NULL,
    timestamp TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_logs_user_id ON logs(user_id);

CREATE INDEX IF NOT EXISTS idx_logs_method ON logs(method);