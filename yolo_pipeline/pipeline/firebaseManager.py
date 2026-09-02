import firebase_admin
from firebase_admin import firestore, credentials

cer_path="serviceKey.json"
cer=credentials.Certificate(cer_path)
firebase_admin.initialize_app(cer)

db=firestore.client()

def read_data(boat_name,boat_id):
    payload=db.collection("boat").document(f"{boat_name}:{boat_id}").get()
    return payload

def write_data(boat_name,boat_id,payload):
    collection=db.collection("boat").document(f"{boat_name}:{boat_id}")
    try:
        collection.update(payload)
        return True
    except:
        return False