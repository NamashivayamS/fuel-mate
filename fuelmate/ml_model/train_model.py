import pandas as pd
import pickle
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
import os

# Load the dataset
df = pd.read_csv('fuel_data.csv')

# Features and target
X = df[['distance_km', 'vehicle_weight', 'driving_style', 'elevation_change', 'fuel_type', 'temperature']]
y = df['fuel_consumption']

# Split the data
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Train the model
model = RandomForestRegressor(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# Save the model
os.makedirs('ml_model', exist_ok=True)
with open('ml_model/model.pkl', 'wb') as f:
    pickle.dump(model, f)

print("✅ Model trained and saved to ml_model/model.pkl")
