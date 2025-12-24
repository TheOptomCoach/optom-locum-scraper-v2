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

        # 2. Read Template
        if not os.path.exists(self.template_file):
             print("Template file missing!")
             return

        with open(self.template_file, 'r') as f:
            template = f.read()

        # 3. Inject Data
        # We replace the JS placeholder variables
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M UTC")
        
        # Serialize shifts to compact JSON
        shifts_js = json.dumps(shifts)
        
        html = template.replace('const shiftsData = [];', f'const shiftsData = {shifts_js};')
        html = html.replace('const lastUpdate = "NEVER";', f'const lastUpdate = "{timestamp}";')

        # 4. Write Output
        output_dir = os.path.dirname(self.output_file)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
        with open(self.output_file, 'w') as f:
            f.write(html)
        
        print(f"Map generated at {self.output_file}")

if __name__ == "__main__":
    gen = MapGenerator()
    gen.generate()
