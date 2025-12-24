import pgeocode
import json
import os
import time
from geopy.geocoders import Nominatim
from geopy.exc import GeopyError

class UKGeocoder:
    def __init__(self, cache_file='data/geocache.json'):
        self.nomi = pgeocode.Nominatim('gb')
        # Initialize geopy for town name lookups
        self.geolocator = Nominatim(user_agent="optom_locum_scraper_v2")
        self.cache_file = cache_file
        self.cache = self._load_cache()

    def _load_cache(self):
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def _save_cache(self):
        os.makedirs(os.path.dirname(self.cache_file), exist_ok=True)
        with open(self.cache_file, 'w') as f:
            json.dump(self.cache, f, indent=2)

    def get_lat_lon(self, postcode_or_town):
        """
        Returns (lat, lon) for a given postcode or town name.
        Checks local cache first, then pgeocode for postcodes, 
        then geopy for town names.
        """
        if not postcode_or_town:
            return None, None

        query = postcode_or_town.upper().strip()
        
        # Check cache
        if query in self.cache:
            return self.cache[query]

        # 1. Try as Postcode first (pgeocode)
        # We only try this if it looks like a postcode (contains a digit)
        if any(char.isdigit() for char in query):
            data = self.nomi.query_postal_code(query)
            if not data.empty and str(data.latitude) != 'nan':
                res = (float(data.latitude), float(data.longitude))
                self.cache[query] = res
                self._save_cache()
                return res

        # 2. If it failed or is likely a town name, use geopy (Nominatim)
        try:
            # We add ", UK" to the query to make it more specific
            location = self.geolocator.geocode(f"{postcode_or_town}, UK")
            if location:
                res = (location.latitude, location.longitude)
                self.cache[query] = res
                self._save_cache()
                # Nominatim requires a 1s delay per request (we are cached so it's rare)
                time.sleep(1)
                return res
        except GeopyError:
            pass
        
        return None, None
