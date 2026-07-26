import sys
import os
import logging

# Setup basic logging for system feedback
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Add the backend directory to the system path so Python can resolve your application models
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../backend')))

try:
    from app import create_app, db
    # ⚠️ Check 'backend/app/models.py' to make sure your class name is exactly 'Vehicle'
    from app.models import Vehicle 
    
    # Initialize the app context to pull your active database configs automatically
    flask_app = create_app()
    HAS_DB = True
except ImportError as e:
    logging.error(f"❌ Structural Path Error: Could not load backend database structures: {e}")
    HAS_DB = False

def get_owner_details(plate_number):
    """
    Queries the live database directly for a specific license plate number.
    Returns: Dict containing owner details/status or None if not found.
    """
    if not plate_number:
        return None

    # Force clean uppercase layout to match database records
    cleaned_plate = plate_number.strip().upper()
    import re
    cleaned_plate = re.sub(r'[^A-Z0-9]', '', cleaned_plate)
    match = re.match(r'^([A-Z]{2,3})(\d{4})$', cleaned_plate)
    if match:
        cleaned_plate = f"{match.group(1)}-{match.group(2)}"

    if not HAS_DB:
        logging.warning("⚠️ Database connection module unavailable.")
        return None

    # Open the Flask context to execute a secure query on the live DB connection
    with flask_app.app_context():
        try:
            # ⚠️ Verify that your column name in models.py is exactly 'plate_number'
            # If your column is named 'plate' or 'vehicle_plate', update it here:
            vehicle = Vehicle.query.filter_by(plate_number=cleaned_plate).first()

            if vehicle:
                logging.info(f"🔓 Record found for plate: {cleaned_plate}")
                
                # Format the database attributes to match the structure your main.py expects
                # Adjust 'vehicle.owner_name' or 'vehicle.status' to match your exact DB columns
                return {
                    "owner": getattr(vehicle, 'owner_name', 'Registered Owner'),
                    "status": getattr(vehicle, 'status', 'allowed')  # e.g., 'allowed', 'blocked'
                }
            else:
                logging.warning(f"🔒 Unknown vehicle approach: {cleaned_plate} not found in DB.")
                return None
                
        except Exception as e:
            logging.error(f"❌ Live database query failed: {e}")
            return None

# Simple manual command-line tester to verify connection execution
if __name__ == "__main__":
    test_plate = "ABC1234"
    print(f"🔄 Testing live query lookup for plate: {test_plate}...")
    result = get_owner_details(test_plate)
    print("Database Response:", result)