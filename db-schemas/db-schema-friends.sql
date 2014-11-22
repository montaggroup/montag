BEGIN TRANSACTION;

CREATE TABLE IF NOT EXISTS friends (
  id INTEGER PRIMARY KEY NOT NULL,
  name TEXT UNIQUE NOT NULL,
  comm_data TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS format_info
(
    id INTEGER PRIMARY KEY NOT NULL,
    is_locked INTEGER, -- not existing or 0 => false, 1 => true
    salt TEXT,
    iteration_count INTEGER,
    encrypted_canary TEXT

);

COMMIT;