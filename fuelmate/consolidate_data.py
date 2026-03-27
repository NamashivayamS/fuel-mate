import pandas as pd
import os

# Paths
CSV_PATH = r'd:\NEED\Sem\Sem 6\Fuelmate\fuel-mate\Dataset\FuelEfficiency.csv'
XLSX_PATH = r'd:\NEED\Sem\Sem 6\Fuelmate\fuel-mate\Dataset\20250814 MY25 ICE,EV,PHEV For DOE R2public.xlsx'
OUTPUT_PATH = r'd:\NEED\Sem\Sem 6\Fuelmate\fuel-mate\fuelmate\vehicles_specs.csv'

def consolidate():
    # 1. Load CSV
    print("Loading CSV...")
    df_csv = pd.read_csv(CSV_PATH)
    # Standardize columns
    # Mfr Name,Carline,Eng Displ,Cylinders,Transmission,CityMPG,HwyMPG,CombMPG,# Gears
    df_csv = df_csv[['Mfr Name', 'Carline', 'Eng Displ', 'Cylinders', 'CombMPG']]
    df_csv.columns = ['make', 'model', 'engine_size', 'cylinders', 'mpg']

    # 2. Load Excel
    print("Loading Excel...")
    df_xl = pd.read_excel(XLSX_PATH)
    # Standardize columns
    # Mfr Name,Carline,Eng Displ,# Cyl,Comb FE (Guide) - Conventional Fuel
    df_xl = df_xl[['Mfr Name', 'Carline', 'Eng Displ', '# Cyl', 'Comb FE (Guide) - Conventional Fuel']]
    df_xl.columns = ['make', 'model', 'engine_size', 'cylinders', 'mpg']

    # 3. Combine
    print("Combining datasets...")
    combined = pd.concat([df_csv, df_xl], ignore_index=True)

    # 4. Clean
    print("Cleaning data...")
    combined['make'] = combined['make'].str.strip().str.title()
    combined['model'] = combined['model'].str.strip()
    
    # Drop duplicates
    combined = combined.drop_duplicates(subset=['make', 'model', 'engine_size'])
    
    # Handle NaN
    combined = combined.dropna()

    # Save
    combined.to_csv(OUTPUT_PATH, index=False)
    print(f"✅ Successfully saved {len(combined)} vehicle models to {OUTPUT_PATH}")

if __name__ == "__main__":
    consolidate()
