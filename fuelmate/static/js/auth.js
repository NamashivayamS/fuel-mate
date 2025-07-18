// Replace mock submission with real API call
document.getElementById('fuelForm').addEventListener('submit', async (e) => {
  e.preventDefault();
  
  const spinner = document.getElementById('calculateSpinner');
  spinner.classList.remove('d-none');

  try {
    const response = await fetch('/predict', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        source: document.getElementById('source').value,
        destination: document.getElementById('destination').value,
        vehicle_weight: parseInt(document.getElementById('totalLoad').value) + 
                       getVehicleWeight(document.getElementById('vehicleType').value),
        driving_style: document.querySelector('input[name="drivingStyle"]:checked').value,
        fuel_type: document.getElementById('fuelType').value
      })
    });

    const data = await response.json();
    
    // Update UI
    document.getElementById('minFuel').textContent = `${data.min_fuel} liters`;
    document.getElementById('safeFuel').textContent = `${data.safe_fuel} liters`;
    document.getElementById('distanceResult').textContent = data.distance;
    
    if (data.elevation_warning) {
      document.getElementById('warningText').textContent = 
        "Mountainous terrain detected! Add 10% extra fuel.";
    }
    
    document.getElementById('resultsSection').classList.remove('d-none');
    
  } catch (error) {
    alert("Error: " + error.message);
  } finally {
    spinner.classList.add('d-none');
  }
});

// Helper function
function getVehicleWeight(type) {
  const weights = { sedan: 1500, suv: 2000, truck: 2500 };
  return weights[type] || 1500;
}