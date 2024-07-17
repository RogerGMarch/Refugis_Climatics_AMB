import json
import re
import unicodedata


# Load the scraped data
with open('schedules.json', 'r') as f:
    schedules = json.load(f)

# Catalan months mapping
months_mapping = {
    "gener": "01", "febrer": "02", "març": "03", "abril": "04", "maig": "05", "juny": "06",
    "juliol": "07", "agost": "08", "setembre": "09", "octubre": "10", "novembre": "11", "desembre": "12"
}

# Function to clean the text
def clean_text(text):
    text = text.replace('Â', '')  # Remove unwanted characters
    text = text.strip()  # Remove leading and trailing whitespace
    return text

# Function to standardize period
def standardize_period(period):
    # Replace month names with their numbers
    for month in months_mapping:
        period = re.sub(rf"\b{month}\b", months_mapping[month], period, flags=re.IGNORECASE)
    
    # Extract and format dates
    matches = re.findall(r"(\d{1,2})\s(de\s\d{1,2}|\d{1,2})", period.lower())
    standardized_period = " ".join([f"{day.zfill(2)}/{months_mapping.get(month, month)}" for day, month in matches])
    
    return standardized_period if standardized_period else period

# Process the schedules to clean and standardize the text
for id, schedule in schedules.items():
    for entry in schedule:
        entry['period'] = standardize_period(clean_text(entry['period']))
        for detail in entry['details']:
            detail['days'] = clean_text(detail['days'])
            detail['hours'] = clean_text(detail['hours'])

# Save the cleaned data to a new JSON file
with open('cleaned_schedules.json', 'w') as f:
    json.dump(schedules, f, ensure_ascii=False, indent=4)

# Print the cleaned schedules
for id, schedule in schedules.items():
    print(f"ID: {id}")
    for entry in schedule:
        print(f"  Period: {entry['period']}")
        for detail in entry['details']:
            print(f"    Days: {detail['days']}")
            print(f"    Hours: {detail['hours']}")
    print()

    
# Load the cleaned data
with open('../data/cleaned_schedules.json', 'r') as f:
    schedules = json.load(f)

# Catalan days, months, and additional phrases mapping
days_mapping = {
    "dilluns": "Monday", "dimarts": "Tuesday", "dimecres": "Wednesday", "dijous": "Thursday", 
    "divendres": "Friday", "dissabte": "Saturday", "diumenge": "Sunday", "tots els dies": "Every day",
    "cada dia": "Every day", "festius": "Holidays", "excepte": "except", "tancat": "closed",
    "de": "from", "a": "to", "i": "and", "al": "to", "del": "from", "que romandra tancada": "which will be closed",
    "romandra tancada": "will be closed", "gener": "January", "febrer": "February", "març": "March", 
    "abril": "April", "maig": "May", "juny": "June", "juliol": "July", "agost": "August", 
    "setembre": "September", "octubre": "October", "novembre": "November", "desembre": "December", "dissabtes": "Saturday"
}

# Common misspellings or joined words patterns
joined_words_patterns = {
    r"dimecresexcepte": "dimecres excepte",
    r"divendresexcepte": "divendres excepte",
    r"divendrestancat": "divendres tancat",
    r"diumengeexcepte": "diumenge excepte",
    r"diesexcepte": "dies excepte",
    r"dissabtesexcepte": "dissabtes excepte",
    r"totselsdiesexcepte": "tots els dies excepte",
    r"iexcepte": "i excepte",
    r"ijuliol": "i juliol",
    r"idesembre": "i desembre",
    r"igener": "i gener",
    r"dijousexcepte": "dijous excepte",
    r"divendresclosed": "divendres closed",
    r"desembrei": "desembre i",
    r"julioli": "juliol i",
    r"setembrequewill": "setembre que will",
    r"fromdesembre": "from desembre",
    r"fromgener": "from gener",
    r"fromjuliol": "from juliol",
    r"fromjuny": "from juny",
    r"frommaig": "from maig",
    r"fromsetembre": "from setembre",
    r"fromoctubre": "from octubre",
    r"fromnovembre": "from novembre",
    r"fromabril": "from abril",
    r"i31": "i 31"
}

# Function to clean and normalize text
def clean_text(text):
    text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('ascii')  # Normalize and remove accents
    text = text.replace('Â', '')  # Remove unwanted characters
    text = text.strip()  # Remove leading and trailing whitespace
    return text

# Function to replace joined words with proper spacing
def fix_joined_words(text):
    for pattern, replacement in joined_words_patterns.items():
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    return text

# Function to replace days and months with standardized format
def standardize_days(days):
    days = clean_text(days).lower()
    days = fix_joined_words(days)
    for catalan_day, english_day in days_mapping.items():
        days = re.sub(rf"\b{catalan_day}\b", english_day, days, flags=re.IGNORECASE)
    # Handle specific phrases and patterns
    days = re.sub(r'\bde\b', 'from', days)
    days = re.sub(r'\ba\b', 'to', days)
    days = re.sub(r'\bi\b', 'and', days)
    days = re.sub(r'\bexcepte\b', 'except', days)
    days = re.sub(r'\btancat\b', 'closed', days)
    days = re.sub(r'\bque romandra tancada\b', 'which will be closed', days)
    days = re.sub(r'\bromandra tancada\b', 'will be closed', days)
    # Ensure spacing around keywords
    days = re.sub(r'\s+', ' ', days)
    return days.strip()

# Function to categorize days
def categorize_days(days):
    if "except" in days:
        parts = days.split(" except ")
        main_days = parts[0].strip()
        exception = parts[1].strip() if len(parts) > 1 else ""
        return {"day type": "exception", "days": main_days, "exception": exception}
    elif "to" in days:
        return {"day type": "range", "days": days, "exception": ""}
    elif "," in days:
        return {"day type": "list", "days": days, "exception": ""}
    else:
        return {"day type": "single", "days": days, "exception": ""}

# Function to standardize periods
def standardize_period(period):
    period = clean_text(period)
    
    # Special replacements
    replacements = {
        "de l'1 d'08-l 31 d'08": "01/08-31/08",
        "Hor-ri d'estiu: de l'1 d'04-l 31 d'10": "01/04-31/10",
        "Estiu 2024;de l'1 d'08-l 31 d'08": "01/08-31/08"
    }

    for old, new in replacements.items():
        if old in period:
            period = period.replace(old, new)
            return period

    # Replace common separators with slashes
    period = re.sub(r'\s+', ' ', period)  # Remove extra whitespace
    period = re.sub(r'(\d{1,2})\s*[dDe]\s*(\d{1,2})', r'\1/\2', period)  # Normalize date format
    period = re.sub(r'\s*-\s*', '-', period)  # Normalize dash
    period = re.sub(r'\s*[aA]\s*', '-', period)  # Normalize "a" to dash

    # Check for single months or single days and set them to "to check"
    if re.match(r'^\d{2}$', period):  # Single month
        return "to check"
    if re.match(r'^\d{1,2}/\d{1,2}$', period):  # Single day
        return "to check"
    
    # Phrases that should be marked as "to check"
    phrases_to_check = [
        "De 09 a 07 Horari habitual",
        "01/11",
        "tot l'any",
        "D'10 a marA",
        "Horari al llarg de l'any",
        "Horari al llarg del curs",
        "Hor-ri h-bitu-l",
        "Tot l'-ny",
        "N/-",
        "De 09-12",
        "De 09-07",
        "de l'1 d'04-l 31 d'10",
        "Hor-ri-l ll-rg del curs",
        "D'10-m-r-",
        "De 01-06",
        "De 05-08",
        "Hor-ri-l ll-rg de l'-ny"
    ]
    if any(phrase in period for phrase in phrases_to_check):
        return "to check"

    # Match and format the period
    match = re.match(r'(\d{1,2}/\d{1,2})-(\d{1,2}/\d{1,2})', period)
    if match:
        start, end = match.groups()
        start_day, start_month = start.split('/')
        end_day, end_month = end.split('/')
        standardized_period = f"{start_day.zfill(2)}/{start_month.zfill(2)}-{end_day.zfill(2)}/{end_month.zfill(2)}"
        return standardized_period
    
    return period

# Function to format period
def format_period(period):
    return period.replace(" ", "-")

# Function to standardize hours
def standardize_hours(hours):
    hours = clean_text(hours).lower()
    hours = re.sub(r'\bde\b', 'from', hours)
    hours = re.sub(r'\ba\b', 'to', hours)
    hours = re.sub(r'\s*h\b', '', hours)  # Remove standalone 'h'
    return hours

# Function to extract and format hours into start and end times
def extract_hours(hours):
    hour_ranges = re.findall(r'(\d{2}[:.]\d{2})\s*[aA]?\s*to\s*(\d{2}[:.]\d{2})', hours)
    formatted_hours = []
    for start, end in hour_ranges:
        start = start.replace('.', ':')
        end = end.replace('.', ':')
        formatted_hours.append({"start": start, "end": end})
    return formatted_hours

# Process the schedules and structure the data
structured_places = []

for place_id, schedule in schedules.items():
    place = {"id": place_id, "schedules": []}
    for entry in schedule:
        standardized_period = standardize_period(entry["period"])
        formatted_period = format_period(standardized_period)
        details = []
        for detail in entry["details"]:
            standardized_day = standardize_days(detail["days"])
            categorized_day = categorize_days(standardized_day)
            standardized_hour = standardize_hours(detail["hours"])
            formatted_hours = extract_hours(standardized_hour)
            details.append({
                "days": categorized_day["days"],
                "hours": formatted_hours,
                "day type": categorized_day["day type"],
                "exception": categorized_day["exception"]
            })
        place["schedules"].append({
            "period": formatted_period,
            "details": details
        })
    structured_places.append(place)

# Save the structured data to a JSON file
with open('../data/structured_places.json', 'w') as f:
    json.dump(structured_places, f, ensure_ascii=False, indent=4)

# Print the structured data
print(json.dumps(structured_places, ensure_ascii=False, indent=4))


import json
import re


