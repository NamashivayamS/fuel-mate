from flask import Flask, request, render_template, redirect, url_for, session, flash, jsonify
import joblib
import googlemaps
import os
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this-in-production'

GOOGLE_MAPS_API_KEY = "AIzaSyCb9KAAjU4wsaxH9nw6LXyowzYr1B-zxBk"
gmaps = googlemaps.Client(key=GOOGLE_MAPS_API_KEY)

# Load the ML model
model = joblib.load('ml_model/model.pkl')

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

# Initialize database on startup
init_db()

# Fuel prices (you can update these or fetch from an API)
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

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        if not email or not password:
            flash('Please provide both email and password', 'error')
            return render_template('login.html')
        
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        c.execute('SELECT * FROM users WHERE email = ?', (email,))
        user = c.fetchone()
        conn.close()
        
        if user and check_password_hash(user[3], password):
            session['user_id'] = user[0]
            session['username'] = user[1]
            flash('Login successful!', 'success')
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
    
    if len(password) < 8:
        flash('Password must be at least 8 characters long', 'error')
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
    flash('Logged out successfully', 'success')
    return redirect(url_for('homepage'))

@app.route('/predict')
def index():
    return render_template('index.html')

@app.route('/predict', methods=['POST'])
def predict():
    data = request.get_json()
    source = data.get('source')
    dest = data.get('destination')
    weight = data.get('vehicle_weight')
    style = data.get('driving_style')
    fuel = data.get('fuel_type')
    temp = data.get('temperature')

    # Validate input
    if not all([source, dest, weight, style, fuel, temp]):
        return jsonify({"error": "Missing required input fields."}), 400
    try:
        weight = float(weight)
        temp = float(temp)
    except Exception:
        return jsonify({"error": "Invalid numeric input."}), 400

    # Get distance using Google Maps
    try:
        directions = gmaps.directions(str(source), str(dest), mode="driving")
        if not directions:
            return jsonify({"error": "Route not found"}), 400
        distance_meters = directions[0]['legs'][0]['distance']['value']
        distance = round(distance_meters / 1000, 2)  # in km
    except Exception as e:
        return jsonify({"error": f"Google Maps error: {str(e)}"}), 500

    # Get elevation change using Google Maps Elevation API
    try:
        start_loc = directions[0]['legs'][0]['start_location']
        end_loc = directions[0]['legs'][0]['end_location']
        elev_start = gmaps.elevation((start_loc['lat'], start_loc['lng']))[0]['elevation']
        elev_end = gmaps.elevation((end_loc['lat'], end_loc['lng']))[0]['elevation']
        elevation_change = elev_end - elev_start
        elev = 'hill' if abs(elevation_change) > 100 else 'plain'
        elev_factor = 1.1 if elev == 'hill' else 1.0
    except Exception as e:
        # Fallback if elevation fails
        elevation_change = 0
        elev = 'plain'
        elev_factor = 1.0

    try:
        features = [distance, weight, style_map[str(style)], fuel_map[str(fuel)], temp, elev_factor]
        pred = model.predict([features])[0]
        min_fuel = round(pred, 2)
        safe_fuel = round(pred * 1.1, 2)
        elevation_warning = elev == 'hill'
        
        # Calculate fuel cost
        current_fuel_price = fuel_prices[str(fuel)]
        estimated_cost = round(safe_fuel * current_fuel_price, 2)
        
        # Determine driving style display
        style_display = {
            'eco': 'Economic',
            'normal': 'Balanced', 
            'aggressive': 'Aggressive'
        }
        
        # Determine path type
        path_type = 'Hill' if elev == 'hill' else 'Plain'
        
        # Terrain/Load Alert
        terrain_alert = elevation_warning or weight > 2000
        
    except Exception as e:
        return jsonify({"error": f"Prediction error: {str(e)}"}), 500

    return jsonify({
        "distance": distance,
        "min_fuel": min_fuel,
        "safe_fuel": safe_fuel,
        "elevation_warning": elevation_warning,
        "current_fuel_price": current_fuel_price,
        "estimated_cost": estimated_cost,
        "driving_style": style_display[str(style)],
        "path_type": path_type,
        "terrain_alert": terrain_alert,
        "fuel_type": str(fuel).capitalize()
    })

if __name__ == '__main__':
    app.run(debug=True)
