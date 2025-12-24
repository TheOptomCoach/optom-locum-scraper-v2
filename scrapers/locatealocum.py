import asyncio
from .base import BaseScraper

class LocateALocumScraper(BaseScraper):
    async def run(self):
        print("Starting LocateALocum...")
        await self.init_browser()
        
        try:
            # 1. Login
            await self.page.goto("https://locatealocum.com/login")
            
            # Check if login is needed by looking for the email input field
            if await self.page.is_visible("input[name='email']"):
                 user = self.secrets.get('LOCATE_USER') or ''
                 password = self.secrets.get('LOCATE_PASS') or ''
                 
                 if not user or not password:
                     print("   Warning: LOCATE_USER or LOCATE_PASS not set. Skipping.")
                     return []
                 
                 await self.page.fill("input[name='email']", user)
                 await self.page.fill("input[name='password']", password)
                 await self.page.click("button[type='submit']")
                 
                 # Wait for dashboard
                 await self.page.wait_for_url("**/dashboard**", timeout=20000)
            
            print("Login Successful")

            # 2. Go to Search Page (Auto-filter for Locum Optom)
            # Adjust URL parameters as needed for default filters
            search_url = "https://locatealocum.com/jobs/search?jobType=1008&sort=startTime%2Casc"
            await self.page.goto(search_url)
            
            # Wait for cards to load
            await self.page.wait_for_selector(".jobCardLink", timeout=15000)
            # Give a little extra time for dynamic content to settle
            await asyncio.sleep(2)

            # 3. Extract Cards using the correct selectors
            cards = await self.page.locator(".jobCardLink").all()
            
            print(f"   Found {len(cards)} potential shifts")

            for card in cards:
                try:
                    # -- Extract Data using correct CSS classes --
                    
                    # Date: .cardDate element
                    date_el = card.locator(".cardDate")
                    date_text = await date_el.text_content() if await date_el.count() > 0 else "Unknown"

                    # Time: .cardTime element
                    time_el = card.locator(".cardTime")
                    time_text = await time_el.text_content() if await time_el.count() > 0 else "Unknown"

                    # Rate: .cardRateHr (hourly rate)
                    rate_el = card.locator(".cardRateHr")
                    rate_text = await rate_el.text_content() if await rate_el.count() > 0 else "N/A"

                    # Total: .cardRateTotal
                    total_el = card.locator(".cardRateTotal")
                    total_text = await total_el.text_content() if await total_el.count() > 0 else "0"
                    
                    # Location: .cardLocation (may contain icon, just get text)
                    location_el = card.locator(".cardLocation")
                    location_text = await location_el.text_content() if await location_el.count() > 0 else "Unknown"
                    # Clean up location (remove icon text artifacts)
                    location_text = location_text.strip()
                    
                    # Company: Not visible in public cards, try to get from img if present
                    img = card.locator("img")
                    if await img.count() > 0:
                        img_alt = await img.first.get_attribute("alt")
                        company = img_alt.replace(" Logo", "") if img_alt else "Unknown Agency"
                    else:
                        company = "Unknown Agency"

                    # Link: Get href from the card itself (it's an anchor)
                    link = await card.get_attribute("href")
                    full_link = f"https://locatealocum.com{link}" if link and link.startswith("/") else link or ""

                    # -- Geocode --
                    lat, lon = await self.get_lat_lon(location_text)

                    shift = {
                        "agency": "LocateALocum",
                        "company": company,
                        "location": location_text,
                        "postcode": "", # LocateALocum often doesn't show postcode on card
                        "date": date_text.strip() if date_text else "",
                        "time": time_text.strip() if time_text else "",
                        "rate": rate_text.strip() if rate_text else "",
                        "total": total_text.replace("Total:", "").replace("£", "").strip() if total_text else "0",
                        "lat": lat,
                        "lon": lon,
                        "link": full_link
                    }
                    self.shifts.append(shift)
                    print(f"   + Scraped: {company} in {location_text}")

                except Exception as e:
                    # Log the error to understand what's failing
                    print(f"   X Error extracting card: {e}")
                    continue

        except Exception as e:
            print(f"LocateALocum Error: {e}")
            await self.page.screenshot(path="error_locatealocum.png")
        
        finally:
            await self.close()
        
        return self.shifts
