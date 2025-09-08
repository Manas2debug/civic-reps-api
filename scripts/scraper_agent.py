import os
import sqlite3
from bs4 import BeautifulSoup
import argparse
import time
import requests

# New imports for Selenium
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
# Import for the timeout exception
from selenium.common.exceptions import TimeoutException


DB = os.path.join(os.path.dirname(__file__), '..', 'server', 'data', 'civic.db')

class RepresentativeScraper:
    def __init__(self):
        # HTTP session for requests-based fallbacks
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        options = webdriver.ChromeOptions()
        # --- IMPROVED: Options to make the browser look more human ---
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
        # This option helps avoid detection
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        # --- End of improved options ---
        
        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        self.reps = []
        self.city = "Unknown"
        self.state = "Unknown"

    def scrape_all_reps_for_11354(self):
        """Scrapes all federal, state, and local reps for ZIP 11354 from a single source."""
        url = "https://www.nyc.gov/site/queenscb4/about/elected-officials.page"
        try:
            self.driver.get(url)
            # This script helps to hide the fact that it's an automated browser
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            # --- IMPROVED: Wait for the ACTUAL content, not just the container ---
            # We will now wait up to 20 seconds for a list item (li) to appear
            # inside the main content area. This is much more reliable.
            wait = WebDriverWait(self.driver, 20)
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".about-description li")))
            
            # --- END of improved wait ---
            
            # Add a small extra sleep just in case, for any final rendering
            time.sleep(1)

            html = self.driver.page_source
            soup = BeautifulSoup(html, 'html.parser')

            # Find a content root; fallback to body if not present
            content_area = soup.find('div', class_='about-description') or \
                           soup.find('div', class_='main-content') or \
                           soup.find('article') or \
                           soup.body
            if not content_area:
                print("[ERROR] Could not find any content area on the page.")
                return

            def clean_name(raw):
                text = raw.strip()
                # Prefer stopping at line breaks or en dashes often used before addresses
                for sep in ['\n', '–', '|', ':']:
                    if sep in text:
                        text = text.split(sep)[0].strip()
                # If digits appear (addresses, suite numbers), cut before the first digit token
                if any(ch.isdigit() for ch in text):
                    tokens = text.split()
                    trimmed_tokens = []
                    for tok in tokens:
                        if any(ch.isdigit() for ch in tok):
                            break
                        trimmed_tokens.append(tok)
                    text = ' '.join(trimmed_tokens).strip()
                # Drop trailing commas/periods
                return text.rstrip('.,;:').strip()

            def process_list(list_ul, title, branch, level):
                for li in list_ul.find_all('li'):
                    # Heuristics to pick the best candidate for the name
                    candidate = None
                    # 1) Anchor text often wraps the name
                    a = li.find('a')
                    if a and a.get_text(strip=True):
                        candidate = a.get_text(" ", strip=True)
                    # 2) Bold/strong/span commonly wrap the name
                    if not candidate:
                        strong_like = li.find(['strong', 'b', 'span'])
                        if strong_like and strong_like.get_text(strip=True):
                            candidate = strong_like.get_text(" ", strip=True)
                    # 3) Fallback: text before line break or before address-like digits
                    if not candidate:
                        full_text = li.get_text("\n", strip=True)  # keep line breaks to split name/address
                        candidate = full_text.split('\n', 1)[0].strip()

                    name = clean_name(candidate)
                    # Avoid very short or obviously invalid names
                    if name and len(name) >= 3:
                        self.reps.append({"name": name, "title": title, "branch": branch, "level": level})

            # Map section keywords to titles/branches
            # Specific-to-generic ordering to avoid mislabeling
            section_mappings = [
                ("nys senate", ("NYS Senator", "state", "state")),
                ("state senate", ("NYS Senator", "state", "state")),
                ("nys assembly", ("NYS Assembly Member", "state", "state")),
                ("state assembly", ("NYS Assembly Member", "state", "state")),
                ("house of representatives", ("U.S. House Rep", "federal", "federal")),
                ("u.s. house", ("U.S. House Rep", "federal", "federal")),
                ("u.s. senate", ("U.S. Senator", "federal", "federal")),
                ("us senate", ("U.S. Senator", "federal", "federal")),
                ("nyc council", ("NYC Council Member", "local", "local")),
                ("city council", ("NYC Council Member", "local", "local")),
            ]

            # Consider multiple possible heading tag types
            candidate_heading_tags = ['p', 'h2', 'h3', 'strong', 'b']
            headings = [el for el in content_area.find_all(candidate_heading_tags)]
            found_any = False
            for heading in headings:
                section_text = heading.get_text(" ", strip=True).lower()
                for needle, (title, branch, level) in section_mappings:
                    if needle in section_text:
                        # Find the nearest following UL within a small sibling distance window
                        rep_list = None
                        # 1) Immediate next sibling
                        rep_list = heading.find_next_sibling('ul')
                        if not rep_list:
                            # 2) Walk next elements until we hit another heading or UL
                            for elem in heading.next_elements:
                                if getattr(elem, 'name', None) in candidate_heading_tags and elem is not heading:
                                    break
                                if getattr(elem, 'name', None) == 'ul':
                                    rep_list = elem
                                    break
                        if rep_list:
                            process_list(rep_list, title, branch, level)
                            found_any = True
                        break

            # Governors and Mayor mentions may be inline text rather than lists; include well-known entries if present
            page_text = content_area.get_text(" ", strip=True)
            if 'kathy hochul' in page_text.lower():
                self.reps.append({"name": "Kathy Hochul", "title": "Governor, New York", "branch": "state", "level": "state"})
                found_any = True

            # If nothing found, dump minimal debug to help iterate
            if not found_any:
                print("[WARN] No sections matched known headings; writing debug_page.html for inspection")
                with open("debug_page.html", "w", encoding="utf-8") as f:
                    f.write(html)

            print(f"[INFO] Scraped a total of {len(self.reps)} representatives from NYC.gov.")
            for rep in self.reps: print(f"  - Found: {rep['name']} ({rep['title']})")

        except TimeoutException:
            # --- NEW: Robust debugging if the wait fails ---
            print("[FATAL ERROR] Page content did not load in time. Saving debug files.")
            # Save a screenshot of what the browser sees
            self.driver.save_screenshot("debug_screenshot.png")
            # Save the HTML source of the page
            with open("debug_page.html", "w", encoding="utf-8") as f:
                f.write(self.driver.page_source)
            print("--> Please check 'debug_screenshot.png' and 'debug_page.html' to see what the scraper saw.")
            
        except Exception as e:
            print(f"[ERROR] An unexpected error occurred: {e}")
        finally:
            self.driver.quit()
    
    # The rest of your script (insert_geo_and_reps, process_zipcode, etc.) remains the same.
    def insert_geo_and_reps(self, zipcode, city, state):
        # This function remains unchanged.
        if not os.path.exists(os.path.dirname(DB)): os.makedirs(os.path.dirname(DB))
        conn = sqlite3.connect(DB); cur = conn.cursor()
        cur.execute('''CREATE TABLE IF NOT EXISTS geography (id INTEGER PRIMARY KEY AUTOINCREMENT, zip TEXT UNIQUE, city TEXT, state TEXT)''')
        cur.execute('''CREATE TABLE IF NOT EXISTS representatives (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, title TEXT, office TEXT, party TEXT, branch TEXT)''')
        cur.execute('''CREATE TABLE IF NOT EXISTS rep_geography_map (geography_id INTEGER, representative_id INTEGER, level TEXT, FOREIGN KEY(geography_id) REFERENCES geography(id), FOREIGN KEY(representative_id) REFERENCES representatives(id))''')
        conn.commit()
        try:
            cur.execute("INSERT OR REPLACE INTO geography (zip, city, state) VALUES (?, ?, ?)", (zipcode, city, state)); cur.execute("SELECT id FROM geography WHERE zip = ?", (zipcode,)); geo_id = cur.fetchone()[0]; cur.execute("DELETE FROM rep_geography_map WHERE geography_id = ?", (geo_id,))
            for rep in self.reps:
                cur.execute("SELECT id FROM representatives WHERE name = ? AND title = ? AND office = ?", (rep['name'], rep['title'], rep.get('office', ''))); result = cur.fetchone()
                if result: rep_id = result[0]
                else: cur.execute("INSERT INTO representatives (name, title, office, party, branch) VALUES (?, ?, ?, ?, ?)", (rep['name'], rep.get('title', ''), rep.get('office', ''), rep.get('party', ''), rep.get('branch', 'federal'))); rep_id = cur.lastrowid
                cur.execute("INSERT INTO rep_geography_map (geography_id, representative_id, level) VALUES (?, ?, ?)", (geo_id, rep_id, rep.get('level', 'federal')))
            conn.commit(); print(f"[SUCCESS] Inserted {len(self.reps)} representatives for ZIP {zipcode}")
        except Exception as e: conn.rollback(); print(f"[ERROR] Database error: {e}")
        finally: conn.close()
    
    def process_zipcode(self, zipcode):
        print(f"[INFO] Starting to process ZIP code: {zipcode}")
        self.reps = []
        # Location lookup
        self.get_location_info(zipcode)

        if zipcode == '11354':
            # Use the NYC page for richer local/state data for this specific ZIP
            self.scrape_all_reps_for_11354()
            # Ensure governor for NY
            if self.state == 'NY':
                self.add_governor_for_state('NY')
        else:
            # Fallback nationwide sources: House + Senate + Governor
            self.scrape_house_gov(zipcode)
            self.scrape_senate_gov(self.state)
            self.add_governor_for_state(self.state)

        if self.reps:
            self.insert_geo_and_reps(zipcode, self.city, self.state)
        else:
            print(f"[WARN] No representatives found for ZIP {zipcode}")

    # ---------------- Requests-based helpers ----------------
    def get_location_info(self, zipcode):
        try:
            resp = self.session.get(f"http://api.zippopotam.us/us/{zipcode}", timeout=6)
            resp.raise_for_status()
            data = resp.json()
            self.city = data['places'][0]['place name']
            self.state = data['places'][0]['state abbreviation']
        except Exception as e:
            print(f"[WARN] ZIP lookup failed: {e}. Using fallback.")
            self.city, self.state = 'Unknown', 'Unknown'

    def scrape_house_gov(self, zipcode):
        url = "https://ziplook.house.gov/htbin/findrep_house"
        try:
            resp = self.session.post(url, data={"ZIP": zipcode}, timeout=10)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, 'html.parser')
            reps_found = []
            for link in soup.find_all("a", href=lambda h: h and ".house.gov" in h and "house.gov/" not in h):
                text = link.get_text(strip=True)
                if text:
                    reps_found.append({
                        'name': text,
                        'title': 'U.S. House Rep',
                        'branch': 'federal',
                        'level': 'federal'
                    })
            # de-duplicate by name
            unique = {r['name']: r for r in reps_found}
            self.reps.extend(unique.values())
            print(f"[INFO] Fallback: found {len(unique)} House rep(s).")
        except Exception as e:
            print(f"[WARN] House.gov fallback failed: {e}")

    def scrape_senate_gov(self, state_abbr):
        url = "https://www.senate.gov/senators/senators-contact.htm"
        found = 0
        try:
            resp = self.session.get(url, timeout=12)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, 'html.parser')
            listing = soup.find('div', class_='contact-listing')
            if listing:
                for item in listing.find_all('div', class_='senator-item'):
                    name_el = item.find('h2')
                    state_el = item.find('span', class_='contact-state')
                    if name_el and state_el and state_el.get_text(strip=True) == state_abbr:
                        self.reps.append({
                            'name': name_el.get_text(strip=True),
                            'title': 'U.S. Senator',
                            'branch': 'federal',
                            'level': 'federal'
                        })
                        found += 1
            print(f"[INFO] Fallback: found {found} Senator(s).")
        except Exception as e:
            print(f"[WARN] Senate.gov fallback failed: {e}")

    def add_governor_for_state(self, state_abbr):
        governors = {
            'NY': ('Kathy Hochul', 'D'),
        }
        if state_abbr in governors:
            name, party = governors[state_abbr]
            self.reps.append({
                'name': name,
                'title': f'Governor, {"New York" if state_abbr=="NY" else state_abbr}',
                'office': 'State',
                'party': party,
                'branch': 'state',
                'level': 'state'
            })


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Multi-source representative scraper agent')
    parser.add_argument('--zip', required=True, help='ZIP code to process')
    args = parser.parse_args()
    scraper = RepresentativeScraper()
    scraper.process_zipcode(args.zip)