drop table tags;
drop table tomes_tags;
drop table tome_tags;

CREATE TABLE IF NOT EXISTS tome_tags (
  tome_id INTEGER NOT NULL,
  tag_value TEXT NOT NULL,
  last_modification_date NUMERIC,
  fidelity REAL NOT NULL
);

CREATE INDEX IF NOT EXISTS tome_tags_tag_value ON tome_tags (tag_value);
CREATE INDEX IF NOT EXISTS tome_tags_last_modification_date ON tome_tags (last_modification_date);
CREATE UNIQUE INDEX IF NOT EXISTS tome_tags_tome_id_tag_value  ON tome_tags (tome_id, tag_value);

