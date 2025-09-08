// server/src/routes/representatives.js
const express = require('express');
const router = express.Router();
const db = require('../db');

// GET /api/representatives?zip=11354&level=federal
router.get('/', (req, res) => {
  const zip = (req.query.zip || '').trim();
  const level = req.query.level;
  
  if (!zip) return res.status(400).json({ error: 'zip query param required' });

  // find geography id
  const geo = db.prepare('SELECT * FROM geography WHERE zip = ?').get(zip);
  if (!geo) return res.status(404).json({ zip, representatives: [] });

  let query = `
    SELECT r.name, r.title, r.office, r.party, r.branch, m.level
    FROM representatives r
    JOIN rep_geography_map m ON r.id = m.representative_id
    WHERE m.geography_id = ?
  `;
  
  const params = [geo.id];
  
  if (level) {
    query += ' AND m.level = ?';
    params.push(level);
  }
  
  query += ' ORDER BY r.branch, r.title';

  const rows = db.prepare(query).all(...params);

  const reps = rows.map(r => {
    const displayTitle = r.office && r.office.trim()
      ? `${r.title}, ${r.office}`
      : r.title;
    return {
      name: r.name,
      title: r.title,
      office: r.office,
      party: r.party,
      branch: r.branch,
      level: r.level,
      displayTitle
    };
  });

  res.json({ 
    zip: zip, 
    city: geo.city, 
    state: geo.state, 
    representatives: reps 
  });
});

// GET /api/representatives/:zip (alternative path parameter format)
router.get('/:zip', (req, res) => {
  req.query.zip = req.params.zip;
  return router.handle(req, res);
});

module.exports = router;
