import datetime

def log_audit(client, audit_data):
    db = client['kritaka_guardaas']
    audit_collection = db['audit_data']
    try:
        audit_collection.insert_one(audit_data)
        print("Successful.")
    except Exception as e:
        print("Failed: ", e)
