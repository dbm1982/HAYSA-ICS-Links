import json
import re
from playwright.sync_api import sync_playwright

BASE_URL = "https://www.haysa.org/schedules"
OUTPUT_FILE = "feeds.json"

def scrape_feeds():
    feeds = {}

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(BASE_URL)

        # Step 1: Extract team names and URLs
        team_data = []
        team_links = page.locator('a[href*="/schedule/"]')
        count = team_links.count()
        print(f"🔍 Found {count} team pages")

        for i in range(count):
            try:
                link = team_links.nth(i)
                team_name = link.inner_text().strip()
                team_url = link.get_attribute("href")
                full_url = f"https://www.haysa.org{team_url}"
                team_data.append((team_name, full_url))
            except Exception as e:
                print(f"⚠️ Could not get team info for index {i}: {e}")

        # Step 2: Visit each team page and extract ICS link
        for team_name, full_url in team_data:
            try:
                page.goto(full_url)
                page.click("text=Subscribe")
                page.wait_for_timeout(2000)  # Let modal render

                # Try regex match from full page content
                html = page.content()
                match = re.search(r'https?://tmsdln\.com/[a-zA-Z0-9]+', html)
                if match:
                    ics_url = match.group(0)
                    feeds[team_name] = ics_url
                    print(f"✅ {team_name}: {ics_url}")
                else:
                    print(f"❌ {team_name}: ICS link not found")
            except Exception as e:
                print(f"❌ {team_name}: {e}")

        browser.close()

    # Step 3: Write to feeds.json
    with open(OUTPUT_FILE, "w") as f:
        json.dump(feeds, f, indent=2)
    print(f"📁 Saved {len(feeds)} feeds to {OUTPUT_FILE}")

if __name__ == "__main__":
    scrape_feeds()
