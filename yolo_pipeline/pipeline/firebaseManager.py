import os
import firebase_admin
from firebase_admin import firestore, credentials

cer_path = os.path.join(os.path.dirname(__file__), "serviceKey.json")
cer = credentials.Certificate(cer_path)
firebase_admin.initialize_app(cer)

db = firestore.client()


def read_data(boat_name, boat_id):
    doc_ref = db.collection("boat").document(f"{boat_name}:{boat_id}")
    payload = doc_ref.get()
    if payload.exists:
        return payload.to_dict()
    return None


def write_data(boat_name, boat_id, payload):
    collection = db.collection("boat").document(f"{boat_name}:{boat_id}")
    try:
        if not isinstance(payload, dict):
            print("write_data payload must be a dict")
            return False
        collection.set(payload, merge=True)
        return True
    except Exception as e:
        print(f"Firebase write error: {e}")
        return False