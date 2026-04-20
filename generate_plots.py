import pandas as pd
import joblib
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import os

# Set professional white theme
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_context("paper", font_scale=1.2)

def generate_comparison_plot():
    # Paths
    csv_path = 'fuelmate/fuel_data_v2.csv'
    model_path = 'fuelmate/ml_model/model.pkl'
    output_image = 'fuel_prediction_comparison.png'

    if not os.path.exists(csv_path) or not os.path.exists(model_path):
        print(f"Error: Required files not found correctly.")
        return

    # Load data and model
    df = pd.read_csv(csv_path)
    model = joblib.load(model_path)

    # Prepare features and target
    X = df.drop('fuel_consumption', axis=1)
    y_actual = df['fuel_consumption']
    
    # Predict
    y_pred = model.predict(X)

    # Metrics
    mae = mean_absolute_error(y_actual, y_pred)
    mse = mean_squared_error(y_actual, y_pred)
    r2 = r2_score(y_actual, y_pred)

    print(f"METRICS_START")
    print(f"MAE: {mae:.4f}")
    print(f"MSE: {mse:.4f}")
    print(f"R2: {r2:.4f}")
    print(f"METRICS_END")

    # Plot
    plt.figure(figsize=(10, 7))
    sns.scatterplot(x=y_actual, y=y_pred, alpha=0.5, color='#4A90E2', edgecolor='w')
    
    # Ideal line
    max_val = max(y_actual.max(), y_pred.max())
    plt.plot([0, max_val], [0, max_val], 'r--', lw=2, label='Ideal Prediction')
    
    plt.title('Actual vs Predicted Fuel Consumption', fontsize=15, pad=20)
    plt.xlabel('Actual Fuel Consumption (Liters)', fontsize=12)
    plt.ylabel('Predicted Fuel Consumption (Liters)', fontsize=12)
    plt.legend(frameon=True)
    plt.tight_layout()
    
    plt.savefig(output_image, dpi=300)
    print(f"Successfully saved plot to {output_image}")

if __name__ == "__main__":
    generate_comparison_plot()
