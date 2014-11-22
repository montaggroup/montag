BEGIN TRANSACTION;

CREATE TABLE IF NOT EXISTS local_files (
  id INTEGER PRIMARY KEY NOT NULL,
  last_modification_date NUMERIC,
  hash TEXT NOT NULL,
  file_extension TEXT NOT NULL,
  UNIQUE (hash, file_extension)
);

CREATE INDEX IF NOT EXISTS local_files_hash ON local_files (hash);
CREATE INDEX IF NOT EXISTS local_files_last_modification_date ON local_files (last_modification_date);

-- for mappings from one file to another (e.g. after metadata strip)
CREATE TABLE IF NOT EXISTS file_hash_aliases (
  source_hash TEXT PRIMARY KEY NOT NULL,
  target_hash TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS file_hash_aliases_target_hash ON file_hash_aliases (target_hash);

CREATE TABLE IF NOT EXISTS tomes_fusion_log (
  source_guid TEXT NOT NULL UNIQUE,
  target_id INTEGER NOT NULL,
  was_split INTEGER  -- 0 => merge, 1 => split
  timestamp NUMERIC
);

CREATE INDEX IF NOT EXISTS tomes_fusion_log_source_guid ON tomes_fusion_log (source_guid);
CREATE INDEX IF NOT EXISTS tomes_fusion_log_target_id ON tomes_fusion_log (target_id);

CREATE TABLE IF NOT EXISTS authors_fusion_log (
  source_guid TEXT NOT NULL UNIQUE,
  target_id INTEGER NOT NULL,
  was_split INTEGER  -- 0 => merge, 1 => split
  timestamp NUMERIC
);

CREATE INDEX IF NOT EXISTS authors_fusion_log_source_guid ON authors_fusion_log (source_guid);
CREATE INDEX IF NOT EXISTS authors_fusion_log_target_id ON authors_fusion_log (target_id);

COMMIT;