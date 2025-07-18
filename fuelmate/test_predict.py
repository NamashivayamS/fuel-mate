import requests

url = 'http://127.0.0.1:5000/predict'

# Sample data
data = {
    "source": "Coimbatore",
    "destination": "Ooty",
    "vehicle_weight": 1600,
    "driving_style": "eco",  # or 'normal' or 'aggressive'
    "fuel_type": "petrol",   # or 'diesel'
    "temperature": 27
}

# Send POST request
response = requests.post(url, json=data)

# Print response
print("Status Code:", response.status_code)
print("Response JSON:", response.json())
