import asyncio
import re
from .base import BaseScraper

class TeamLocumScraper(BaseScraper):
    async def run(self):
        print("Starting Team Locum...")
        await self.init_browser()
        
        try:
            # 1. Login
            # Team Locum login usually redirects to a specific schedule/bookings ID
            await self.page.goto("https://app.teamlocum.co.uk/login")
            
            # Helper to check if we are on login page
            # We use a broad selector for input to be safe if 'username' vs 'email'
            if await self.page.is_visible("input[type='email']") or await self.page.is_visible("input[type='text']"):
                user = self.secrets.get('TEAMLOCUM_USER') or ''
                password = self.secrets.get('TEAMLOCUM_PASS') or ''
                
                if not user or not password:
                    print("   Warning: TEAMLOCUM_USER or TEAMLOCUM_PASS not set. Skipping.")
                    return []
                
                # Try generic input selectors if config ones aren't specific
                user_sel = "input[type='email']" if await self.page.is_visible("input[type='email']") else "input[type='text']"
                
                await self.page.fill(user_sel, user)
                await self.page.fill("input[type='password']", password)
                await self.page.click("button[type='submit']")
                
                print("   Logging in...")
                await self.page.wait_for_load_state('networkidle')

            print("Login Successful")

            # 2. Navigate to Bookings/Marketplace
            # The URL might be dynamic: /<id>/bookings
            # We assume the login redirects appropriately, or we might need to find the "Bookings" link
            
            # Check for "Bookings" or similar navigation if not immediately visible
            # For now, we assume we land on a dashboard where shifts are listed or we can find the list
            # Based on the HTML snippet, it looks like a list view.
            
            # Wait for list items
            try:
                await self.page.wait_for_selector("li h6", timeout=15000)
            except:
                print("   No shifts found or page failed to load.")
                return []

            # 3. Extract Cards
            # The snippet shows shifts are <li> items containing an <h6> date
            lis = await self.page.locator("li:has(h6)").all()
            print(f"   Found {len(lis)} potential shifts")

            for li in lis:
                try:
                    # Date: h6 tag
                    date_text = await li.locator("h6").first.text_content()
                    
                    # The main info line is in a p.fw-semibold
                    info_p = li.locator("p.fw-semibold").first
                    
                    # Time: Badge inside the p
                    time_text = await info_p.locator(".badge").first.text_content()
                    
                    # Location: Anchor text
                    location_link = info_p.locator("a").first
                    location_text = await location_link.text_content()
                    
                    # Rate: It's text in the p tag, outside the badge and link. 
                    # Structure: <badge>Time</badge> <a ..>Location</a>, £180 - DO
                    # We can get the full text and regex for the price
                    full_text = await info_p.text_content()
                    
                    # Regex to find price: £...
                    rate_match = re.search(r"£(\d+(\.\d{2})?)", full_text)
                    rate_text = f"£{rate_match.group(1)}" if rate_match else "Negotiable"
                    total_text = rate_match.group(1) if rate_match else "0"

                    # Location Name cleaning
                    # "BOL Franchise, Teddington" -> Teddington usually nice for geocoding
                    # But full string is safer for unique matching
                    clean_location = location_text.strip()
                    
                    # Geocode
                    # Team Locum often lacks postcode in list view, so we rely on town name
                    lat, lon = await self.get_lat_lon(clean_location)

                    shift = {
                        "agency": "Team Locum",
                        "company": "Team Locum Client", # Generic unless we parse "BOL Franchise"
                        "location": clean_location,
                        "postcode": "", 
                        "date": date_text.strip(),
                        "time": time_text.strip(),
                        "rate": rate_text,
                        "total": total_text,
                        "lat": lat,
                        "lon": lon,
                        "link": "https://app.teamlocum.co.uk" # Dynamic links require IDs, safer to link root
                    }
                    
                    self.shifts.append(shift)
                    print(f"   + {shift['date']}: {shift['location']} (£{shift['total']})")

                except Exception as e:
                    # Skip rows that might be "You have 0 activity" alerts or different structures
                    continue

        except Exception as e:
            print(f"Team Locum Error: {e}")
            await self.page.screenshot(path="error_teamlocum.png")
        
        finally:
            await self.close()
            
        return self.shifts
