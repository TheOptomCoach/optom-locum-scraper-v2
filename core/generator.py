import json
import os
from datetime import datetime

class MapGenerator:
    def __init__(self, data_file='data/history.json', template_file='templates/index.html', output_file='output/index.html'):
        self.data_file = data_file
        self.template_file = template_file
        self.output_file = output_file

    def generate(self):
        # 1. Load Data
        if not os.path.exists(self.data_file):
            print("No data file found, generating empty map.")
            shifts = []
        else:
            with open(self.data_file, 'r') as f:
                shifts = json.load(f)

        # 2. Group Data by Location
        grouped_data = {}
        
        for shift in shifts:
            # Skip invalid coordinates
            if shift.get('lat') is None or shift.get('lon') is None:
                continue

            loc_name = shift.get('location', 'Unknown')
            lat = shift.get('lat')
            lon = shift.get('lon')
            key = (loc_name, lat, lon)

            if key not in grouped_data:
                grouped_data[key] = {
                    "name": loc_name,
                    "lat": lat,
                    "lon": lon,
                    "shifts": [],
                    "count": 0,
                    "companies": set()
                }
            
            # Process shift for inner list
            # Ensure total is a float
            try:
                total_val = float(str(shift.get('total', 0)).replace(',', ''))
            except (ValueError, TypeError):
                total_val = 0.0

            grouped_data[key]["shifts"].append({
                "location": loc_name,
                "total": total_val,
                "company": shift.get('company', 'Unknown Agency')
            })
            grouped_data[key]["count"] += 1
            grouped_data[key]["companies"].add(shift.get('company', 'Unknown Agency'))

        # Convert to list for JSON and handle sets
        locations_list = []
        for key, data in grouped_data.items():
            data["companies"] = list(data["companies"]) # Convert set to list
            locations_list.append(data)

        # 3. Read Template
        if not os.path.exists(self.template_file):
             print(f"Template file missing at {self.template_file}!")
             return

        with open(self.template_file, 'r', encoding='utf-8') as f:
            template = f.read()

        # 4. Inject Data
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M UTC")
        locations_js = json.dumps(locations_list, indent=2)
        
        # Replace placeholders defined in the template
        html = template.replace('const locationsData = []; // WILL BE REPLACED BY PYTHON', f'const locationsData = {locations_js};')
        html = html.replace('const lastUpdate = "NEVER"; // WILL BE REPLACED BY PYTHON', f'const lastUpdate = "{timestamp}";')

        # 5. Write Output
        output_dir = os.path.dirname(self.output_file)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
            
        with open(self.output_file, 'w', encoding='utf-8') as f:
            f.write(html)
        
        print(f"Map generated at {self.output_file} with {len(locations_list)} locations.")

if __name__ == "__main__":
    gen = MapGenerator()
    gen.generate()
