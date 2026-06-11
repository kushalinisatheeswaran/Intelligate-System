# db_check.py

def get_owner_details(plate_number):
    # temporary dummy logic
    # later connect to PostgreSQL or Flask API

    dummy_db = {
        "ABC1234": {"owner": "Karthi", "status": "allowed"},
        "TEST123": {"owner": "Admin", "status": "allowed"}
    }

    return dummy_db.get(plate_number, None)