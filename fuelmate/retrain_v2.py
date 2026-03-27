import pandas as pd
import numpy as np
import random
import os
import joblib
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split

# Constants
L_100KM_FROM_MPG = 235.215

def generate_and_train():
    # 1. Load vehicle specs
    specs_path = r'd:\NEED\Sem\Sem 6\Fuelmate\fuel-mate\fuelmate\vehicles_specs.csv'
    if not os.path.exists(specs_path):
        print("Error: vehicles_specs.csv not found!")
        return
    
    df_specs = pd.read_csv(specs_path)
    
    # 2. Generate Synthetic Data
    rows = []
    print("Generating synthetic data...")
    
    # Generate ~5000 samples for a robust model
    for i in range(5000):
        # Pick a random vehicle
        vehicle = df_specs.sample().iloc[0]
        
        # Scenario variables
        distance_km = random.uniform(5, 500)
        driving_style = random.choice([0, 1, 2]) # 0: eco, 1: normal, 2: aggressive
        elevation_change = random.uniform(-500, 500)
        fuel_type = random.choice([0, 1]) # 0: petrol, 1: diesel
        temperature = random.uniform(0, 45)
        
        # Calculate base consumption (L/100km)
        l_per_100km = L_100KM_FROM_MPG / vehicle['mpg']
        
        # Apply multipliers
        # style: eco=0.85, normal=1.0, aggressive=1.25
        style_mult = 1.0
        if driving_style == 0: style_mult = 0.85
        elif driving_style == 2: style_mult = 1.25
        
        # elevation: every 100m uphill +5%, downhill -2%
        elev_mult = 1.0 + (elevation_change / 100 * (0.05 if elevation_change > 0 else 0.02))
        
        # temp: cold (<10) or hot (>35) increases consumption by 5-10% (AC/Heater)
        temp_mult = 1.0
        if temperature < 10 or temperature > 35:
            temp_mult = 1.05
            
        # Result
        fuel_consumption = (distance_km / 100) * l_per_100km * style_mult * elev_mult * temp_mult
        
        # Add slight noise (±3%)
        fuel_consumption *= random.uniform(0.97, 1.03)
        
        rows.append({
            'distance_km': round(distance_km, 2),
            'engine_size': vehicle['engine_size'],
            'cylinders': vehicle['cylinders'],
            'driving_style': driving_style,
            'elevation_change': round(elevation_change, 2),
            'fuel_type': fuel_type,
            'temperature': round(temperature, 2),
            'fuel_consumption': round(max(0.1, fuel_consumption), 2)
        })
    
    df_train = pd.DataFrame(rows)
    df_train.to_csv('fuel_data_v2.csv', index=False)
    print("✅ Created fuel_data_v2.csv with 5000 samples.")

    # 3. Train Model
    print("Training model...")
    X = df_train.drop('fuel_consumption', axis=1)
    y = df_train['fuel_consumption']
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    model = RandomForestRegressor(n_estimators=150, random_state=42)
    model.fit(X_train, y_train)
    
    # 4. Save
    os.makedirs('ml_model', exist_ok=True)
    joblib.dump(model, 'ml_model/model_v2.pkl')
    # Update current model
    joblib.dump(model, 'ml_model/model.pkl')
    
    print("✅ Model trained and saved as model.pkl")

if __name__ == "__main__":
    generate_and_train()
