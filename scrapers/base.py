import asyncio
import os
from abc import ABC, abstractmethod
from playwright.async_api import async_playwright
from core.geocoder import UKGeocoder

class BaseScraper(ABC):
    def __init__(self, secrets):
        self.secrets = secrets
        self.shifts = []
        # Initialize UK Postcode engine
        self.geo = UKGeocoder()

    async def init_browser(self):
        self.playwright = await async_playwright().start()
        # Launch browser with "Stealth" args to look like a real person
        # We use a user data dir to potentially cache sessions if needed, but for now ephemeral is safer for clean tests
        self.browser = await self.playwright.chromium.launch(headless=True)
        
        # Create a context with a realistic user agent and viewport
        self.context = await self.browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={'width': 1920, 'height': 1080},
            locale='en-GB',
            timezone_id='Europe/London'
        )
        
        # Hide the webdriver property to evade simple bot detection
        await self.context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        self.page = await self.context.new_page()

    async def get_lat_lon(self, location_str):
        """
        Geocodes a location string using the core geocoder.
        """
        return self.geo.get_lat_lon(location_str)

    async def close(self):
        if hasattr(self, 'browser'):
            await self.browser.close()
        if hasattr(self, 'playwright'):
            await self.playwright.stop()

    @abstractmethod
    async def run(self):
        """
        Main execution method for the scraper.
        Must return a list of shift dictionaries.
        """
        pass
