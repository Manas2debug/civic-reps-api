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
### Scraping Design Overview

To meet the project requirements while ensuring robust data ingestion, this prototype implements a two-tiered scraping strategy:

#### 1. Primary Scraper for ZIP 11354 (Flushing, Queens, NY)
- Target: NYC Queens Community Board 4 elected officials page  
  ([https://www.nyc.gov/site/queenscb4/about/elected-officials.page](https://www.nyc.gov/site/queenscb4/about/elected-officials.page))
- This page centrally lists federal, state, and local representatives for the 11354 area, enabling scraping of a comprehensive and accurate set of officials in one pass.
- Method:
  - Use Selenium + BeautifulSoup to fully load and wait for page content
  - Broadly detect the main content area
  - Identify government level sections (U.S. Senate, U.S. House, NYS Senate, NYS Assembly, NYC Council) via heuristic keyword mapping on headings
  - Extract representative names while cleaning out extraneous address fragments
  - Explicitly include the NY Governor if referenced on the page
- Outcome:
  - Provides high-quality, complete data for ZIP 11354, fulfilling the project’s requirement to support 1–2 ZIP codes in depth.

#### 2. Fallback Scrapers for Other U.S. ZIP Codes
- For ZIP codes other than 11354, the agent uses multiple fallback sources:
  - U.S. House of Representatives: POST request to [ziplook.house.gov](https://ziplook.house.gov/htbin/findrep_house) endpoint
  - U.S. Senate: Scrapes [senate.gov](https://www.senate.gov/senators/senators-contact.htm) directory to match senators by state
  - Governors: Maps known governors by state (currently supports NY Governor Kathy Hochul)

---
