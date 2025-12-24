import pgeocode
import json
import os

class UKGeocoder:
    def __init__(self, cache_file='data/geocache.json'):
        self.nomi = pgeocode.Nominatim('gb')
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
        Check's local cache first, then uses pgeocode.
        """
        query = postcode_or_town.upper().strip()
        
        # Check cache
        if query in self.cache:
            return self.cache[query]

        # Try as Postcode first (pgeocode works best with outcode or full postcode)
        # If it's a full postcode like 'CV1 1FX', pgeocode handles it.
        # If it's a town like 'Pontypridd', we might need a different approach or rely on pgeocode fuzzy match if available, 
        # but pgeocode is primarily postal.
        
        # Strategy: 
        # 1. Try exact query
        data = self.nomi.query_postal_code(query)
        
        if not data.empty and str(data.latitude) != 'nan':
            res = (float(data.latitude), float(data.longitude))
            self.cache[query] = res
            self._save_cache()
            return res

        # 2. If it failed, it might be a town name. 
        # pgeocode is strictly postal. For town names, we might technically need an external API if we want perfect accuracy,
        # but for now we will return None. The scraper logic handles the 'Town' fallback by geocoding manually later
        # or we could add a small hardcoded map for major cities if needed.
        
        return None, None
