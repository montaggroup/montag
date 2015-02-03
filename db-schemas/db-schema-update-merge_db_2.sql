BEGIN TRANSACTION;

ALTER TABLE authors ADD COLUMN name_key TEXT DEFAULT ''; -- will be set by migration and business-logic

CREATE INDEX IF NOT EXISTS authors_name_key ON authors (name_key);

PRAGMA user_version=2;

COMMIT;

