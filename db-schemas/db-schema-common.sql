BEGIN TRANSACTION;
CREATE TABLE IF NOT EXISTS tome_types (
   id INTEGER PRIMARY KEY NOT NULL,
   name TEXT NOT NULL
);

INSERT OR IGNORE INTO tome_types (id,name) VALUES (1,'fiction');
INSERT OR IGNORE INTO tome_types (id,name) VALUES (2,'non-fiction');


CREATE TABLE IF NOT EXISTS tomes ( 
  id INTEGER PRIMARY KEY NOT NULL, 
  guid TEXT NOT NULL UNIQUE, 
  title TEXT NOT NULL, 
  subtitle TEXT, 
  edition TEXT, 
  principal_language TEXT NOT NULL, 
  publication_year NUMERIC,
  last_modification_date NUMERIC,
  type INTEGER,
  fidelity REAL
);

CREATE INDEX IF NOT EXISTS tomes_title ON tomes (title);
CREATE INDEX IF NOT EXISTS tomes_guid ON tomes (guid);
CREATE INDEX IF NOT EXISTS tomes_last_modification_date ON tomes (last_modification_date);


CREATE TABLE IF NOT EXISTS tome_tags (
  tome_id INTEGER NOT NULL,
  tag_value TEXT NOT NULL,
  last_modification_date NUMERIC,
  fidelity REAL NOT NULL,
  UNIQUE (tome_id, tag_value)
    
);

CREATE INDEX IF NOT EXISTS tome_tags_tome_id ON tome_tags (tome_id);
CREATE INDEX IF NOT EXISTS tome_tags_tag_value ON tome_tags (tag_value);
CREATE INDEX IF NOT EXISTS tome_tags_last_modification_date ON tome_tags (last_modification_date);


CREATE TABLE IF NOT EXISTS synopses (
  id INTEGER PRIMARY KEY NOT NULL,
  guid TEXT NOT NULL UNIQUE,
  tome_id INTEGER NOT NULL,
  content TEXT NOT NULL, -- reStructuredText markup
  last_modification_date NUMERIC,
  fidelity REAL NOT NULL
);

CREATE INDEX IF NOT EXISTS synopses_tome_id ON synopses (tome_id);
CREATE INDEX IF NOT EXISTS synopses_last_modification_date ON synopses (last_modification_date);


CREATE TABLE IF NOT EXISTS file_types (
   id INTEGER PRIMARY KEY NOT NULL,
   name TEXT NOT NULL
);

INSERT OR IGNORE INTO file_types (id,name) VALUES (1,'content');
INSERT OR IGNORE INTO file_types (id,name) VALUES (2,'cover');



CREATE TABLE IF NOT EXISTS files (
  id INTEGER PRIMARY KEY NOT NULL,
  tome_id INTEGER NOT NULL,
  size NUMERIC NOT NULL,
  file_type INTEGER NOT NULL,
  hash TEXT NOT NULL,
  file_extension TEXT NOT NULL,
  last_modification_date NUMERIC,
  fidelity REAL NOT NULL,
  UNIQUE (tome_id, hash)
);

CREATE INDEX IF NOT EXISTS files_tome_id ON files (tome_id);
CREATE INDEX IF NOT EXISTS files_hash ON files (hash);
CREATE INDEX IF NOT EXISTS files_last_modification_date ON files (last_modification_date);



CREATE TABLE IF NOT EXISTS authors (
  id INTEGER PRIMARY KEY NOT NULL,
  guid TEXT NOT NULL UNIQUE, 
  name TEXT NOT NULL, 
  date_of_birth TEXT,
  date_of_death TEXT,
  last_modification_date NUMERIC,
  fidelity REAL NOT NULL
);

CREATE INDEX IF NOT EXISTS authors_guid ON authors (guid);
CREATE INDEX IF NOT EXISTS authors_name ON authors (name);
CREATE INDEX IF NOT EXISTS authors_last_modification_date ON authors (last_modification_date);



CREATE TABLE IF NOT EXISTS pseudonyms (
  id INTEGER PRIMARY KEY NOT NULL,
  author_id INTEGER NOT NULL,
  name TEXT NOT NULL,
  last_modification_date NUMERIC,
  fidelity REAL NOT NULL
);

CREATE INDEX IF NOT EXISTS pseudonyms_author_id ON pseudonyms (author_id);
CREATE INDEX IF NOT EXISTS pseudonyms_name ON pseudonyms (name);
CREATE INDEX IF NOT EXISTS pseudonyms_last_modification_date ON pseudonyms (last_modification_date);

  
CREATE TABLE IF NOT EXISTS tomes_authors (
  tome_id INTEGER NOT NULL,
  author_id INTEGER NOT NULL,
  author_order REAL,
  last_modification_date NUMERIC,
  fidelity REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS tomes_authors_tome_id ON tomes_authors (tome_id);
CREATE INDEX IF NOT EXISTS tomes_authors_author_id ON tomes_authors (author_id);
CREATE UNIQUE INDEX IF NOT EXISTS tomes_authors_tomes_authors on tomes_authors (tome_id, author_id);
CREATE INDEX IF NOT EXISTS tomes_authors_last_modification_date ON tomes_authors (last_modification_date);


CREATE TABLE IF NOT EXISTS tome_fusion_sources (
  source_guid TEXT NOT NULL UNIQUE,
  tome_id INTEGER NOT NULL,
  last_modification_date NUMERIC,
  fidelity REAL NOT NULL
);

CREATE INDEX IF NOT EXISTS tome_fusion_sources_source_guid ON tome_fusion_sources (source_guid);
CREATE INDEX IF NOT EXISTS tome_fusion_sources_tome_id ON tome_fusion_sources (tome_id);

CREATE TABLE IF NOT EXISTS author_fusion_sources (
  source_guid TEXT NOT NULL UNIQUE,
  author_id INTEGER NOT NULL,
  last_modification_date NUMERIC,
  fidelity REAL NOT NULL
);

CREATE INDEX IF NOT EXISTS author_fusion_sources_source_guid ON author_fusion_sources (source_guid);
CREATE INDEX IF NOT EXISTS author_fusion_sources_author_id ON author_fusion_sources (author_id);



COMMIT;
