BEGIN TRANSACTION;

CREATE TABLE IF NOT EXISTS identifier_files (
  hash TEXT NOT NULL,
  input_state TEXT NOT NULL,   -- Pending, Running, Unidentified, Identified
  date_import NUMERIC NOT NULL,
  date_last_state_change NUMERIC NOT NULL,
  PRIMARY KEY(hash)
);

CREATE INDEX IF NOT EXISTS identifier_files_input_state ON identifier_files (input_state);


CREATE TABLE IF NOT EXISTS identifier_facts (
    hash TEXT NOT NULL,
    `key` TEXT NOT NULL,
    `value` TEXT NOT NULL,
    PRIMARY KEY(hash, `key`)
);

CREATE TABLE IF NOT EXISTS identifier_results (
    id INTEGER PRIMARY KEY,
    hash TEXT NOT NULL,
    identifier_name TEXT NOT NULL,
    fidelity REAL NOT NULL,
    tome_document TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS identifier_results_hash ON identifier_results (hash);

COMMIT;