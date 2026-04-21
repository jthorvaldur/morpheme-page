CREATE TABLE decompositions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  word TEXT NOT NULL UNIQUE,
  prefix TEXT DEFAULT '',
  prefix_meaning TEXT DEFAULT '',
  root TEXT NOT NULL,
  root_meaning TEXT NOT NULL,
  suffix TEXT DEFAULT '',
  suffix_meaning TEXT DEFAULT '',
  is_negated BOOLEAN DEFAULT 0,
  true_meaning TEXT NOT NULL,
  apparent_meaning TEXT NOT NULL,
  domain TEXT DEFAULT 'legal',
  etymology_source TEXT DEFAULT '',
  status TEXT DEFAULT 'pending_review',
  ai_confidence REAL,
  ai_notes TEXT,
  submitter_name TEXT DEFAULT 'anonymous',
  created_at TEXT DEFAULT (datetime('now')),
  updated_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE corrections (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  decomposition_id INTEGER REFERENCES decompositions(id),
  field_name TEXT NOT NULL,
  old_value TEXT NOT NULL,
  new_value TEXT NOT NULL,
  justification TEXT NOT NULL,
  status TEXT DEFAULT 'pending_review',
  ai_confidence REAL,
  submitter_name TEXT DEFAULT 'anonymous',
  created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE domain_suggestions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  domain_name TEXT NOT NULL,
  description TEXT NOT NULL,
  example_words TEXT,
  status TEXT DEFAULT 'pending_review',
  submitter_name TEXT DEFAULT 'anonymous',
  created_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX idx_word ON decompositions(word);
CREATE INDEX idx_status ON decompositions(status);
CREATE INDEX idx_domain ON decompositions(domain);
