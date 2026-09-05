import os
import firebase_admin
from firebase_admin import firestore, credentials

cer_path = os.path.join(os.path.dirname(__file__), "serviceKey.json")

db = None
try:
    cer = credentials.Certificate(cer_path)
    firebase_admin.initialize_app(cer)
    db = firestore.client()
except Exception as e:
    print(f"Firebase init error: {e}", flush=True)


def read_data(boat_name, boat_id):
    if db is None:
        print("Firebase not initialized", flush=True)
        return None
    doc_ref = db.collection("boat").document(f"{boat_name}:{boat_id}")
    payload = doc_ref.get()
    if payload.exists:
        return payload.to_dict()
    return None


def write_data(boat_name, boat_id, payload):
    if db is None:
        print("Firebase not initialized", flush=True)
        return False
    collection = db.collection("boat").document(f"{boat_name}:{boat_id}")
    try:
        if not isinstance(payload, dict):
            print("write_data payload must be a dict", flush=True)
            return False
        collection.set(payload, merge=True)
        return True
    except Exception as e:
        print(f"Firebase write error: {e}", flush=True)
        return False
