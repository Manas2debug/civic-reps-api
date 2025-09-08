-- sample geography rows
INSERT INTO geography (zip, city, state, congressional_district) VALUES
('11354', 'Flushing', 'NY', 'NY-06'),
('13662', 'Massena', 'NY', 'NY-21');

-- sample representatives
INSERT INTO representatives (name, title, office, party, branch) VALUES
('Grace Meng', 'U.S. House Rep', 'NY-06', 'D', 'federal'),
('Chuck Schumer', 'U.S. Senator', 'NY', 'D', 'federal'),
('Kathy Hochul', 'Governor', 'New York', 'D', 'state'),
('Example Local', 'City Councilor', 'Flushing District 1', 'D', 'local'),
('Elise Stefanik', 'U.S. House Rep', 'NY-21', 'R', 'federal');

-- link 11354 to reps (geography_id assumed 1)
INSERT INTO rep_geography_map (geography_id, representative_id, level) VALUES
(1, 1, 'federal'),
(1, 2, 'federal'),
(1, 3, 'state'),
(1, 4, 'local');

-- link 13662 to minimal set (geography_id assumed 2)
INSERT INTO rep_geography_map (geography_id, representative_id, level) VALUES
(2, 5, 'federal'),
(2, 2, 'federal'),
(2, 3, 'state');
