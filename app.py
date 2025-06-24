from flask import Flask, request, render_template, redirect, url_for, jsonify
import joblib
import numpy as np

app = Flask(__name__)

# Load the trained model
model = joblib.load('ml_model/model.pkl')

# Distance and elevation data
distance_map = {
    ("Coimbatore", "Ooty"): 86,
    ("Coimbatore", "Chennai"): 510,
    ("Coimbatore", "Trichy"): 210,
    ("Trichy", "Karur"): 80,
}

elevation_map = {
    ("Coimbatore", "Ooty"): "hill",
    ("Coimbatore", "Chennai"): "plain",
    ("Coimbatore", "Trichy"): "plain",
    ("Trichy", "Karur"): "plain",
}

style_map = {"eco": 0, "normal": 1, "aggressive": 2}
fuel_map = {"petrol": 0, "diesel": 1}

# Home route
@app.route('/')
def homepage():
    return render_template('homepage.html')

# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # In real case: verify user
        return redirect(url_for('result'))
    return render_template('login.html')

# Fuel prediction form & result display
@app.route('/result', methods=['GET', 'POST'])
def result():
    if request.method == 'POST':
        try:
            source = request.form.get("source")
            dest = request.form.get("destination")
            weight = float(request.form.get("vehicle_weight"))
            style = request.form.get("driving_style")
            fuel = request.form.get("fuel_type")
            temp = float(request.form.get("temperature"))

            key = (source, dest)
            if key not in distance_map:
                return render_template('result.html', error="Invalid route selected.")

            distance = distance_map[key]
            elevation_type = elevation_map.get(key, "plain")
            elevation_factor = 1.1 if elevation_type == "hill" else 1.0

            features = [distance, weight, style_map[style], fuel_map[fuel], temp, elevation_factor]
            predicted_fuel = model.predict([features])[0]
            safe_fuel = round(predicted_fuel * 1.1, 2)

            return render_template('result.html',
                                   distance=distance,
                                   fuel_required=safe_fuel,
                                   elevation=elevation_type)
        except Exception as e:
            return render_template('result.html', error=f"Error: {str(e)}")

    return render_template('result.html')  # GET request

# Optional API for testing
@app.route('/api/predict', methods=['POST'])
def api_predict():
    data = request.get_json()
    try:
        source = data.get("source")
        dest = data.get("destination")
        weight = float(data.get("vehicle_weight"))
        style = data.get("driving_style")
        fuel = data.get("fuel_type")
        temp = float(data.get("temperature"))

        key = (source, dest)
        if key not in distance_map:
            return jsonify({"error": "Route not found."}), 400

        distance = distance_map[key]
        elevation_type = elevation_map.get(key, "plain")
        elevation_factor = 1.1 if elevation_type == "hill" else 1.0

        features = [distance, weight, style_map[style], fuel_map[fuel], temp, elevation_factor]
        predicted_fuel = model.predict([features])[0]
        safe_fuel = round(predicted_fuel * 1.1, 2)

        return jsonify({
            "distance": f"{distance} km",
            "min_fuel": round(predicted_fuel, 2),
            "safe_fuel": safe_fuel,
            "elevation_warning": elevation_type == "hill"
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
