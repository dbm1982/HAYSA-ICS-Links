import json
import re
from collections import defaultdict
from playwright.sync_api import sync_playwright

BASE_URL = "https://www.haysa.org/schedules"
OUTPUT_FILE = "feeds.json"

def scrape_feeds():
    feeds = {}
    name_counts = defaultdict(int)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(BASE_URL)

        team_links = page.locator('a[href*="/schedule/"]')
        count = team_links.count()
        print(f"🔍 Found {count} team pages")

        for i in range(count):
            try:
                link = team_links.nth(i)
                team_name = link.inner_text().strip()
                team_url = link.get_attribute("href")
                full_url = f"https://www.haysa.org{team_url}"

                # Visit team page to extract ICS link
                page.goto(full_url)
                page.click("text=Subscribe")
                page.wait_for_timeout(2000)

                html = page.content()
                match = re.search(r'https?://tmsdln\.com/[a-zA-Z0-9]+', html)
                if match:
                    ics_url = match.group(0)

                    # Disambiguate team name if repeated
                    name_counts[team_name] += 1
                    suffix = f".{name_counts[team_name]}" if name_counts[team_name] > 1 else ""
                    final_name = f"{team_name}{suffix}"

                    feeds[final_name] = ics_url
                    print(f"✅ {final_name}: {ics_url}")
                else:
                    print(f"❌ {team_name}: ICS link not found")
            except Exception as e:
                print(f"❌ Error at index {i}: {e}")

        browser.close()

    with open(OUTPUT_FILE, "w") as f:
        json.dump(feeds, f, indent=2)
    print(f"📁 Saved {len(feeds)} feeds to {OUTPUT_FILE}")

if __name__ == "__main__":
    scrape_feeds()
