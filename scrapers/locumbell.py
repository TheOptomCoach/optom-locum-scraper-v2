import json
import asyncio
from .base import BaseScraper

class LocumbellScraper(BaseScraper):
    async def run(self):
        agency_name = self.secrets.get('AGENCY_NAME', 'Locumbell')
        print(f"Starting {agency_name}...")
        
        await self.init_browser()
        
        try:
            # 1. Login
            login_url = self.secrets.get('LOGIN_URL') 
            await self.page.goto(login_url)
            
            # Helper to check if we are on login page
            # Locumbell (SPA) uses #username / #password
            try:
                await self.page.wait_for_selector("#username", timeout=5000)
                is_login_page = True
            except:
                is_login_page = False

            if is_login_page:
                # Use generic keys if agency specific ones aren't provided
                user = self.secrets.get('LOCUMB_USER') or ''
                password = self.secrets.get('LOCUMB_PASS') or ''
                
                if not user or not password:
                    print(f"   Warning: LOCUMB_USER or LOCUMB_PASS not set. Skipping {agency_name}.")
                    return []
                
                await self.page.fill("#username", user)
                await self.page.fill("#password", password)
                # Click the button that says "Log in"
                await self.page.click("button:has-text('Log in')")
                print("   Logging in...")
                
                # Wait for the #Available Shifts hash or the table to appear
                # The URL usually changes to .../index.html#Available%20Shifts
                # We wait for network idle to ensure redirection is complete
                await self.page.wait_for_load_state('networkidle')
                await asyncio.sleep(2) # Safety buffer

            print("Login Successful / Dashboard Loaded")

            # 2. Ensure we are on the Available Shifts tab
            # Sometimes it lands on Home. Force the hash if needed.
            current_url = self.page.url
            if "Available%20Shifts" not in current_url:
                target_url = f"{current_url.split('#')[0]}#Available%20Shifts"
                await self.page.goto(target_url)
                await asyncio.sleep(2)
            
            # 3. Wait for the data table
            try:
                # We wait for the specific icon that holds the data
                await self.page.wait_for_selector(".practice-icon", timeout=15000)
            except:
                print("   No shifts found (timeout waiting for table).")
                return []

            # 4. Extract Data from the 'data-row-data' attribute
            icons = await self.page.locator(".practice-icon").all()
            print(f"   Found {len(icons)} potential shifts")

            for icon in icons:
                try:
                    # Get the raw JSON string from the attribute
                    raw_data = await icon.get_attribute("data-row-data")
                    
                    if not raw_data:
                        continue
                        
                    data = json.loads(raw_data)

                    # --- MAPPING DATA ---
                    postcode = data.get('postcode')
                    city = data.get('city', '')
                    location_name = f"{city}, {postcode}" if postcode else city
                    
                    # Geocode using our offline tool (prefer postcode)
                    lat, lon = await self.get_lat_lon(postcode if postcode else city)

                    shift = {
                        "agency": agency_name,
                        "company": data.get('branch_name', 'Unknown'),
                        "location": location_name,
                        "postcode": postcode,
                        "date": data.get('Shift Dates'),
                        "time": f"{data.get('start_time')} - {data.get('end_time')}",
                        "rate": f"£{data.get('Rate', 0)}/day",
                        "total": str(data.get('Rate', 0)),
                        "lat": lat,
                        "lon": lon,
                        "link": login_url # Direct linking is hard in SPAs
                    }
                    
                    self.shifts.append(shift)
                    print(f"   + {shift['date']}: {shift['company']} (£{shift['total']})")

                except Exception as e:
                    print(f"   X Error parsing row: {e}")

        except Exception as e:
            print(f"Error: {e}")
            await self.page.screenshot(path=f"error_{agency_name}.png")
        
        finally:
            await self.close()
        
        return self.shifts
