import asyncio
from .base import BaseScraper

class LocumotiveScraper(BaseScraper):
    async def run(self):
        print("Starting Locumotive...")
        await self.init_browser()
        
        try:
            # 1. Login
            await self.page.goto("https://locumotive.co.uk/login")
            
            # Check if login required
            if await self.page.is_visible("input[formcontrolname='email']"):
                user = self.secrets.get('LOCUMOTIVE_USER') or ''
                password = self.secrets.get('LOCUMOTIVE_PASS') or ''
                
                if not user or not password:
                    print("   Warning: LOCUMOTIVE_USER or LOCUMOTIVE_PASS not set. Skipping.")
                    return []
                
                await self.page.fill("input[formcontrolname='email']", user)
                await self.page.fill("input[formcontrolname='password']", password)
                await self.page.click("button[type='submit']")
                await self.page.wait_for_url("**/dashboard**", timeout=20000)
            
            print("Login Successful")
            
            # 2. Go to Search 
            # Often redirected to dashboard, so explicitly go to search or use nav
            await self.page.goto("https://locumotive.co.uk/advance-search")

            # 3. Wait for job cards
            # We use the unique class 'bg-white.rounded-xl' which wraps each job in the list
            try:
                await self.page.wait_for_selector(".rounded-xl", timeout=15000)
            except:
                print("   No shifts found or page failed to load.")
                return []
            
            # 4. Scrape the cards
            # We select all divs that start with 'job_' in their class list
            # This is specific to the Locumotive Angular app structure
            job_cards = await self.page.locator("div[class*='job_']").all()
            print(f"   Found {len(job_cards)} job cards")

            for card in job_cards:
                try:
                    # Extracting data using the specific classes
                    date_text = await card.locator(".locum-date").inner_text()
                    time_text = await card.locator(".locum-time").inner_text()
                    rate_text = await card.locator(".locum-price").inner_text()
                    
                    # City is in the h2 inside .address-area
                    city_text = await card.locator(".address-area h2").last.inner_text()
                    
                    # Clean up the rate (e.g. " £325 /day " -> "325")
                    clean_rate = rate_text.replace("£", "").replace("/day", "").strip()

                    # Since there is no postcode, we geocode the City
                    lat, lon = await self.get_lat_lon(city_text)

                    shift = {
                        "agency": "Locumotive",
                        "company": "Locum Optometrist", # Blind until viewed
                        "location": city_text.strip(),
                        "postcode": "", 
                        "date": date_text.strip(),
                        "time": time_text.strip(),
                        "rate": rate_text.strip(),
                        "total": clean_rate,
                        "lat": lat,
                        "lon": lon,
                        "link": "https://locumotive.co.uk/advance-search"
                    }
                    
                    self.shifts.append(shift)
                    print(f"   + {shift['date']}: {shift['location']} (£{shift['total']})")

                except Exception as e:
                    continue 

        except Exception as e:
            print(f"Locumotive Error: {e}")
            await self.page.screenshot(path="error_locumotive.png")
        
        finally:
            await self.close()
            
        return self.shifts
