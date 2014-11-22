BEGIN TRANSACTION;

CREATE TABLE IF NOT EXISTS update_info (
  id NUMERIC UNIQUE,
  last_query_date_authors NUMERIC NOT NULL DEFAULT '0',
  last_query_date_tomes NUMERIC NOT NULL DEFAULT '0'
);

INSERT OR IGNORE INTO update_info (id, last_query_date_authors, last_query_date_tomes) VALUES(0, 0,0);

COMMIT;