import os
import sys

print("Python:", sys.version, flush=True)
print("CWD:", os.getcwd(), flush=True)

cer_path = os.environ.get(
    "FIREBASE_SERVICE_KEY",
    os.path.join(os.path.dirname(__file__), "serviceKey.json")
)
if not os.path.exists(cer_path):
    cer_path = os.path.join(os.path.dirname(__file__), "servicaAccountKey.json")
print("Key path:", cer_path, flush=True)
print("Key exists:", os.path.exists(cer_path), flush=True)

try:
    from firebase_admin import credentials, initialize_app, firestore
    import firebase_admin
    print("firebase_admin available", flush=True)
except ImportError as e:
    print(f"Import error: {e}", flush=True)
    sys.exit(1)

try:
    cer = credentials.Certificate(cer_path)
    print("Certificate loaded successfully", flush=True)
    print("Service account:", cer.service_account_email, flush=True)
except Exception as e:
    print(f"Certificate error: {type(e).__name__}: {e}", flush=True)
    sys.exit(1)

try:
    initialize_app(cer)
    print("Firebase app initialized", flush=True)
except ValueError:
    print("App already initialized (OK)", flush=True)
except Exception as e:
    print(f"Init error: {type(e).__name__}: {e}", flush=True)
    sys.exit(1)

try:
    db = firestore.client()
    doc_ref = db.collection("boat").document("scuba:9999")
    print("Calling Firestore get() with 10s timeout...", flush=True)
    doc = doc_ref.get(timeout=10)
    print("Document exists:", doc.exists, flush=True)
    if doc.exists:
        print("Data:", doc.to_dict(), flush=True)
    else:
        print("Document not found (doc ID: scuba:9999 doesn't exist in Firestore)", flush=True)
except Exception as e:
    print(f"Firestore error: {type(e).__name__}: {e}", flush=True)
