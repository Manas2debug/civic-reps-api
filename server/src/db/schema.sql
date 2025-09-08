-- geography: stores zip -> city/state/district (district may be congressional/state/local)
CREATE TABLE geography (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  zip TEXT NOT NULL UNIQUE,
  city TEXT,
  state TEXT,
  congressional_district TEXT, -- e.g., "NY-06"
  state_senate_district TEXT,
  state_house_district TEXT
);

-- representatives: master list of reps
CREATE TABLE representatives (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  title TEXT NOT NULL,       -- e.g., "U.S. Senator", "Governor", "U.S. House Rep"
  office TEXT,               -- e.g., "NY-6"
  party TEXT,
  branch TEXT                -- "federal", "state", "local"
);

-- join table mapping geography -> representative(s)
CREATE TABLE rep_geography_map (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  geography_id INTEGER NOT NULL,
  representative_id INTEGER NOT NULL,
  level TEXT,                -- "federal", "state", "local"
  FOREIGN KEY(geography_id) REFERENCES geography(id),
  FOREIGN KEY(representative_id) REFERENCES representatives(id),
  UNIQUE(geography_id, representative_id)
);

-- Performance indexes
CREATE INDEX IF NOT EXISTS idx_geography_zip ON geography(zip);
CREATE INDEX IF NOT EXISTS idx_map_geo ON rep_geography_map(geography_id);
