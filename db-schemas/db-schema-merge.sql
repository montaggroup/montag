BEGIN TRANSACTION;

CREATE TABLE IF NOT EXISTS tome_document_changes (
  document_guid TEXT PRIMARY KEY NOT NULL,
  last_modification_date NUMERIC
);

CREATE INDEX IF NOT EXISTS tome_document_changes_last_modification_date ON tome_document_changes (last_modification_date);
CREATE INDEX IF NOT EXISTS tome_document_changes_document_id ON tome_document_changes (document_guid);


CREATE TABLE IF NOT EXISTS author_document_changes (
  document_guid TEXT PRIMARY KEY NOT NULL,
  last_modification_date NUMERIC
);


CREATE INDEX IF NOT EXISTS author_document_changes_last_modification_date ON author_document_changes (last_modification_date);
CREATE INDEX IF NOT EXISTS author_document_changes_document_id ON author_document_changes (document_guid);


-- these are only required for fetch_missing files which is only called on merge db
CREATE INDEX IF NOT EXISTS tomes_fidelity ON tomes (fidelity);
CREATE INDEX IF NOT EXISTS files_fidelity ON files (fidelity);


CREATE TABLE IF NOT EXISTS local_files (
  id INTEGER PRIMARY KEY NOT NULL,
  last_modification_date NUMERIC,
  hash TEXT NOT NULL,
  file_extension TEXT NOT NULL,
  UNIQUE (hash, file_extension)
);

CREATE INDEX IF NOT EXISTS local_files_hash ON local_files (hash);
CREATE INDEX IF NOT EXISTS local_files_last_modification_date ON local_files (last_modification_date);
CREATE INDEX IF NOT EXISTS tomes_language_fidelity ON tomes (principal_language, fidelity);


COMMIT;
