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
    print("  [read_data] entered", flush=True)
    if db is None:
        print("Firebase not initialized", flush=True)
        return None
    try:
        print("  [read_data] about to call get()", flush=True)
        doc_ref = db.collection("boat").document(f"{boat_name}:{boat_id}")
        payload = doc_ref.get(timeout=10)
        print("  [read_data] get() returned", flush=True)
        if payload.exists:
            return payload.to_dict()
        print("  [read_data] document does not exist", flush=True)
        return None
    except Exception as e:
        print(f"Firebase read error: {e}", flush=True)
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
