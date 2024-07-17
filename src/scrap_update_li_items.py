import requests
from lxml import html
import json
import random
import time
from tqdm import tqdm

# Load the JSON file with schedules
with open('./schedules.json', 'r') as f:
    schedules_data = json.load(f)

# Load the JSON file with IDs
with open('./json_refugis.json', 'r') as f:
    data = json.load(f)

# Extract the IDs
ids = [entry['id'] for entry in data['data']]

# Find IDs with missing schedules
missing_schedule_ids = [id for id in ids if not schedules_data.get(id)]

# Base URL
base_url = 'https://www.barcelona.cat/barcelona-pel-clima/ca/ajuntament-maps/data/getDetall?bloc=ajuntament_maps&lang=ca&id='

# Function to get the schedule from the webpage
def get_schedule(id):
    url = f"{base_url}{id}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Ensure we raise an error for bad responses
        tree = html.fromstring(response.content)

        # Extract the schedule
        schedule_elements = tree.xpath('//div[@class="horari"]/ul[@class="content-horari"]/*')
        schedule = []
        current_period = None
        details = []

        for element in schedule_elements:
            if 'periode' in element.attrib.get('class', ''):
                if current_period or details:
                    schedule.append({
                        'period': current_period or 'N/A',
                        'details': details
                    })
                    details = []
                current_period = ' '.join(element.xpath('.//p[@class="periode-title"]/text()')).strip()
                
                days_elements = element.xpath('.//p[@class="dies"]/text()')
                hours_elements = element.xpath('.//div[@class="hores"]/text()')
                
                for days_elem, hours_elem in zip(days_elements, hours_elements):
                    details.append({
                        'days': days_elem.strip(),
                        'hours': hours_elem.strip()
                    })
            elif 'dies' in element.attrib.get('class', ''):
                days = ' '.join(element.xpath('.//text()')).strip()
                details.append({
                    'days': days,
                    'hours': None
                })
            elif 'hores' in element.attrib.get('class', ''):
                hours = ' '.join(element.xpath('.//text()')).strip()
                if details and details[-1]['hours'] is None:
                    details[-1]['hours'] = hours
                else:
                    details.append({
                        'days': None,
                        'hours': hours
                    })
            elif element.tag == 'li':  # Handling cases where periods are missing
                days = ' '.join(element.xpath('.//p[@class="dies"]/text()')).strip()
                hours = ' '.join(element.xpath('.//div[@class="hores"]/text()')).strip()
                if days and hours:
                    details.append({
                        'days': days,
                        'hours': hours
                    })
                elif days:
                    details.append({
                        'days': days,
                        'hours': None
                    })
                elif hours:
                    details.append({
                        'days': None,
                        'hours': hours
                    })

        if current_period or details:
            schedule.append({
                'period': current_period or 'N/A',
                'details': details
            })

        return schedule
    except requests.RequestException as e:
        print(f"Request failed for ID {id}: {e}")
        return []

# Iterate over the IDs with missing schedules and scrape the schedule
print("Starting the scraping process for missing schedules...")
for id in tqdm(missing_schedule_ids, desc="Scraping missing schedules"):
    schedule = get_schedule(id)
    schedules_data[id] = schedule
    print(f"Scraped schedule for ID: {id}")
    time.sleep(random.uniform(0.5, 2))  # Random delay between 0.5 and 2 seconds

# Save the updated schedules to the JSON file
with open('../data/schedules_updated.json', 'w') as f:
    json.dump(schedules_data, f, indent=4)

# Print the count of empty schedules
empty_schedules_count = sum(1 for schedule in schedules_data.values() if not schedule or all(not entry['details'] for entry in schedule))
print(f"Number of entries with empty schedules: {empty_schedules_count}")

# Print the schedules (Optional)
print("\nCompleted scraping. Here are the schedules:")
for id, schedule in schedules_data.items():
    print(f"ID: {id}")
    for entry in schedule:
        print(f"  Period: {entry['period']}")
        for detail in entry['details']:
            print(f"    Days: {detail['days']}")
            print(f"    Hours: {detail['hours']}")
    print()
