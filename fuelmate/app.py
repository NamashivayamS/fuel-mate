from flask import Flask, request, render_template, redirect, url_for, session, flash, jsonify
import joblib
import googlemaps
import os
import sqlite3
import pandas as pd
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'default-key-for-dev')

GOOGLE_MAPS_API_KEY = os.getenv('GOOGLE_MAPS_API_KEY')
gmaps = googlemaps.Client(key=GOOGLE_MAPS_API_KEY)

# Load the ML model
model = joblib.load('ml_model/model.pkl')

# Load vehicle specs
VEHICLES_CSV = 'vehicles_specs.csv'
vehicles_df = pd.read_csv(VEHICLES_CSV)

# Database initialization
def init_db():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  username TEXT UNIQUE NOT NULL,
                  email TEXT UNIQUE NOT NULL,
                  password_hash TEXT NOT NULL,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()

init_db()

# Fuel prices
fuel_prices = {
    'petrol': 96.72,
    'diesel': 89.62
}

style_map = {"eco": 0, "normal": 1, "aggressive": 2}
fuel_map = {"petrol": 0, "diesel": 1}

@app.route('/')
def homepage():
    return render_template('homepage.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/services')
def services():
    return render_template('services.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

# API Endpoints for Vehicle Data
@app.route('/api/vehicles/makes')
def get_makes():
    makes = sorted(vehicles_df['make'].unique().tolist())
    return jsonify(makes)

@app.route('/api/vehicles/models/<make>')
def get_models(make):
    models = sorted(vehicles_df[vehicles_df['make'].str.lower() == make.lower()]['model'].unique().tolist())
    return jsonify(models)

@app.route('/api/vehicles/specs')
def get_specs():
    make = request.args.get('make')
    model_name = request.args.get('model')
    spec = vehicles_df[(vehicles_df['make'].str.lower() == make.lower()) & 
                       (vehicles_df['model'] == model_name)].iloc[0]
    return jsonify({
        "engine_size": spec['engine_size'],
        "cylinders": spec['cylinders']
    })

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        c.execute('SELECT * FROM users WHERE email = ?', (email,))
        user = c.fetchone()
        conn.close()
        
        if user and check_password_hash(user[3], password):
            session['user_id'] = user[0]
            session['username'] = user[1]
            return redirect(url_for('index'))
        else:
            flash('Invalid email or password', 'error')
    
    return render_template('login.html')

@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username')
    email = request.form.get('email')
    password = request.form.get('password')
    
    if not username or not email or not password:
        flash('Please fill in all fields', 'error')
        return redirect(url_for('login'))
    
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    try:
        password_hash = generate_password_hash(password)
        c.execute('INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)',
                 (username, email, password_hash))
        conn.commit()
        flash('Registration successful! Please login.', 'success')
    except sqlite3.IntegrityError:
        flash('Email already exists', 'error')
    finally:
        conn.close()
    
    return redirect(url_for('login'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('homepage'))

@app.route('/predict')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('index.html', google_maps_api_key=GOOGLE_MAPS_API_KEY)

@app.route('/predict', methods=['POST'])
def predict():
    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json()
    source = data.get('source')
    dest = data.get('destination')
    engine_size = data.get('engine_size')
    cylinders = data.get('cylinders')
    style = data.get('driving_style')
    fuel = data.get('fuel_type')
    temp = data.get('temperature')

    if not all([source, dest, engine_size, cylinders, style, fuel, temp]):
        return jsonify({"error": "Missing required input fields."}), 400

    # Get distance using Google Maps
    try:
        directions = gmaps.directions(str(source), str(dest), mode="driving")
        if not directions:
            return jsonify({"error": "Route not found"}), 400
        distance_meters = directions[0]['legs'][0]['distance']['value']
        distance = round(distance_meters / 1000, 2)
    except Exception as e:
        return jsonify({"error": f"Google Maps error: {str(e)}"}), 500

    # Get elevation
    try:
        start_loc = directions[0]['legs'][0]['start_location']
        end_loc = directions[0]['legs'][0]['end_location']
        elev_start = gmaps.elevation((start_loc['lat'], start_loc['lng']))[0]['elevation']
        elev_end = gmaps.elevation((end_loc['lat'], end_loc['lng']))[0]['elevation']
        elevation_change = elev_end - elev_start
    except Exception:
        elevation_change = 0

    try:
        # Features order: [distance, engine_size, cylinders, style, elevation, fuel, temp]
        features = [
            float(distance), 
            float(engine_size), 
            float(cylinders), 
            float(style_map[str(style)]), 
            float(elevation_change),
            float(fuel_map[str(fuel)]), 
            float(temp)
        ]
        pred = model.predict([features])[0]
        min_fuel = round(pred, 2)
        safe_fuel = round(pred * 1.1, 2)
        
        current_fuel_price = fuel_prices[str(fuel)]
        estimated_cost = round(safe_fuel * current_fuel_price, 2)
        
    except Exception as e:
        return jsonify({"error": f"Prediction error: {str(e)}"}), 500

    return jsonify({
        "distance": distance,
        "min_fuel": min_fuel,
        "safe_fuel": safe_fuel,
        "current_fuel_price": current_fuel_price,
        "estimated_cost": estimated_cost,
        "driving_style": style.capitalize(),
        "path_type": "Hill" if abs(elevation_change) > 100 else "Plain",
        "terrain_alert": abs(elevation_change) > 150,
        "fuel_type": str(fuel).capitalize()
    })

if __name__ == '__main__':
    app.run(debug=True)
