BEGIN TRANSACTION;

ALTER TABLE files ADD COLUMN local_file_exists INTEGER DEFAULT 0; -- will be set to one on relevant files by migration and business-logic

UPDATE files SET local_file_exists=1 WHERE files.hash IN (SELECT hash FROM local_files);
CREATE INDEX IF NOT EXISTS files_local_file_exists ON files (local_file_exists);

PRAGMA user_version=1;

COMMIT;

