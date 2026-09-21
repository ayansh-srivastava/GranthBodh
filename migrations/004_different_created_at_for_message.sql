ALTER TABLE Message
ALTER COLUMN created_at SET DEFAULT clock_timestamp();