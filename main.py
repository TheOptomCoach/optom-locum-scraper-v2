import asyncio
import json
import os
import yaml
from scrapers.locatealocum import LocateALocumScraper
from scrapers.locumbell import LocumbellScraper
from scrapers.locumotive import LocumotiveScraper
from scrapers.teamlocum import TeamLocumScraper
from core.generator import MapGenerator

async def main():
    print("Starting Daily Scrape...")
    
    # 1. Load Config
    try:
        with open('config/agencies.yaml', 'r') as f:
            config = yaml.safe_load(f)
    except FileNotFoundError:
        print("Config file not found!")
        return

    # 2. Shared Secrets (Env Vars)
    secrets = {
        "LOCATE_USER": os.environ.get("LOCATE_USER"),
        "LOCATE_PASS": os.environ.get("LOCATE_PASS"),
        "LOCUMB_USER": os.environ.get("LOCUMB_USER"),
        "LOCUMB_PASS": os.environ.get("LOCUMB_PASS"),
        "LOCUMOTIVE_USER": os.environ.get("LOCUMOTIVE_USER"),
        "LOCUMOTIVE_PASS": os.environ.get("LOCUMOTIVE_PASS"),
        "TEAMLOCUM_USER": os.environ.get("TEAMLOCUM_USER"),
        "TEAMLOCUM_PASS": os.environ.get("TEAMLOCUM_PASS"),
    }

    all_shifts = []

    # 3. Dynamic Runner
    for key, agency_conf in config['agencies'].items():
        if not agency_conf.get('enabled'):
            print(f"Skipping {key} (Disabled)")
            continue

        scraper = None
        
        # Merge secrets with agency specific config
        agency_secrets = secrets.copy()
        agency_secrets['LOGIN_URL'] = agency_conf.get('login_url')
        agency_secrets['AGENCY_NAME'] = agency_conf.get('name')

        # Factory Pattern
        impl = agency_conf.get('implementation', key) # Default to key name
        
        if key == 'locatealocum':
            scraper = LocateALocumScraper(agency_secrets)
        elif impl == 'locumbell':
            scraper = LocumbellScraper(agency_secrets)
        elif key == 'locumotive':
            scraper = LocumotiveScraper(agency_secrets)
        elif key == 'teamlocum':
            scraper = TeamLocumScraper(agency_secrets)

        if scraper:
            try:
                shifts = await scraper.run()
                all_shifts.extend(shifts)
            except Exception as e:
                print(f"Critical failure in {key}: {e}")

    # 4. Save to History (Simple overwrite for now, Merge logic comes next)
    print(f"Scrape Complete. Total shifts: {len(all_shifts)}")
    
    # Ensure directory exists
    os.makedirs('data', exist_ok=True)
    
    with open('data/history.json', 'w') as f:
        json.dump(all_shifts, f, indent=2)

    # 5. Generate Map HTML
    gen = MapGenerator(output_file='index.html')
    gen.generate()

if __name__ == "__main__":
    asyncio.run(main())
