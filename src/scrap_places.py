import requests
from lxml import html
import json
import random
import time
from tqdm import tqdm

# Load the JSON file
with open('../data/json_refugis.json', 'r') as f:
    data = json.load(f)

# Extract the IDs
ids = [entry['id'] for entry in data['data']]

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
                if current_period:
                    schedule.append({
                        'period': current_period,
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
            elif 'hores' in element.attrib.get('class', ''):
                hours = ' '.join(element.xpath('.//text()')).strip()
                if current_period:
                    details.append({
                        'days': days,
                        'hours': hours
                    })
        
        if current_period:
            schedule.append({
                'period': current_period,
                'details': details
            })

        return schedule
    except requests.RequestException as e:
        print(f"Request failed for ID {id}: {e}")
        return []

# Iterate over the IDs and scrape the schedule
schedules = {}
print("Starting the scraping process...")
for id in tqdm(ids, desc="Scraping schedules"):
    schedules[id] = get_schedule(id)
    print(f"Scraped schedule for ID: {id}")
    time.sleep(random.uniform(0.5, 2))  # Random delay between 0.5 and 2 seconds

# Print the schedules
print("\nCompleted scraping. Here are the schedules:")
for id, schedule in schedules.items():
    print(f"ID: {id}")
    for entry in schedule:
        print(f"  Period: {entry['period']}")
        for detail in entry['details']:
            print(f"    Days: {detail['days']}")
            print(f"    Hours: {detail['hours']}")
    print()

with open('../data/schedules.json', 'w', encoding='utf-8') as f:
    json.dump(schedules, f, ensure_ascii=False, indent=4)

print("\nCompleted scraping. The schedules have been saved to schedules.json.")