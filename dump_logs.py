import subprocess
import os

try:
    # ml-service logs
    with open('/home/brayone-xv/Documents/My File/CODE/pijak-by-dicoding/CAPSTONE/agrolytics/ml_service/ml_service_logs.txt', 'w') as f:
        subprocess.run(['docker', 'logs', 'ml-service'], stdout=f, stderr=subprocess.STDOUT)
    
    # predictive-ml-service logs
    with open('/home/brayone-xv/Documents/My File/CODE/pijak-by-dicoding/CAPSTONE/agrolytics/ml_service/predictive_logs.txt', 'w') as f:
        subprocess.run(['docker', 'logs', 'predictive-ml-service'], stdout=f, stderr=subprocess.STDOUT)
    
    # bridge logs
    with open('/home/brayone-xv/Documents/My File/CODE/pijak-by-dicoding/CAPSTONE/agrolytics/ml_service/bridge_logs.txt', 'w') as f:
        subprocess.run(['docker', 'logs', 'fastapi-ml-bridge'], stdout=f, stderr=subprocess.STDOUT)
        
    print("Logs exported successfully.")
except Exception as e:
    print(f"Error: {e}")
