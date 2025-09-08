// server/src/db.js
const Database = require('better-sqlite3');
const fs = require('fs');
const path = require('path');

const DB_PATH = path.join(__dirname, '..', 'data', 'civic.db');

// ensure data directory
const dataDir = path.join(__dirname, '..', 'data');
if (!fs.existsSync(dataDir)) fs.mkdirSync(dataDir);

// initialize DB and run schema/seed if database doesn't exist
const initDb = () => {
  const db = new Database(DB_PATH);
  const schemaPath = path.join(__dirname, 'db', 'schema.sql');
  const seedPath = path.join(__dirname, 'db', 'seed.sql');
  
  // if DB file size is small/zero or just newly created, run schema and seed
  const createNeeded = db.prepare("SELECT name FROM sqlite_master WHERE type='table' AND name='geography'").get() ? false : true;
  if (createNeeded) {
    console.log('Initializing database with schema and seed data...');
    const schema = fs.readFileSync(schemaPath, 'utf8');
    db.exec(schema);
    const seed = fs.readFileSync(seedPath, 'utf8');
    db.exec(seed);
    console.log('Database initialized successfully.');
  }
  return db;
};

module.exports = initDb();
