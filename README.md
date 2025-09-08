## Civic Representatives API (Prototype)

A prototype API and scraper that returns political representative details for a given U.S. ZIP code.

### Features
- SQLite schema for `geography`, `representatives`, and `rep_geography_map`
- Scraper/Agent to fetch officials and insert into DB
- Express API endpoint to return reps by ZIP

### Prerequisites
- Node.js 18+
- Python 3.10+

### Setup
1) Create Python virtual environment and install deps
```
cd /Users/manasmehta/Desktop/civic-reps-api
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2) Scrape and populate the database (example: 11354)
```
python scripts/scraper_agent.py --zip 11354
```

3) Start the API server
```
cd server
npm install
npm run start
```

4) Query the API
```
curl "http://localhost:3000/api/representatives?zip=11354"
```

Response includes `zip`, `city`, `state`, and a list of representatives with fields:
`name`, `title`, `office`, `party`, `branch`, `level`, and `displayTitle` (e.g., "U.S. House Rep, NY-6").

### Database Schema
Defined in `server/src/db/schema.sql` with indexes. The database is populated by running the scraper.

### Notes
- Prototype focuses on a small set of ZIP codes. Extend by adding more scrapers and normalizers.
- For demo, ensure DB is populated before starting the API.

### Design Choices
- SQLite for simplicity and zero external dependencies in a prototype.
- Separation of concerns: Python scraper populates DB; Node/Express serves read-only API.
- Schema normalization: `geography`, `representatives`, and `rep_geography_map` to support many-to-many mappings and multiple government levels.
- Defensive scraping: robust selectors, fallbacks to federal sources for arbitrary ZIPs, and basic data cleaning for names and titles.
- API response includes `displayTitle` for easy UI rendering (e.g., "U.S. House Rep, NY-6").



