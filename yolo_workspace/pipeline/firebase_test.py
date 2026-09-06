import os
import sys

print("Python:", sys.version, flush=True)
print("CWD:", os.getcwd(), flush=True)

cer_path = os.path.join(os.path.dirname(__file__), "serviceKey.json")
print("Key path:", cer_path, flush=True)
print("Key exists:", os.path.exists(cer_path), flush=True)

try:
    from firebase_admin import credentials
    import google.auth
    print("firebase_admin and google.auth available", flush=True)
except ImportError as e:
    print(f"Import error: {e}", flush=True)
    sys.exit(1)

try:
    cer = credentials.Certificate(cer_path)
    print("Certificate loaded successfully", flush=True)
    print("Service account:", cer.service_account_email, flush=True)

    import firebase_admin
    try:
        firebase_admin.initialize_app(cer)
        print("Firebase app initialized", flush=True)

        from firebase_admin import firestore
        db = firestore.client()

        doc_ref = db.collection("boat").document("scuba:9999")
        print("Calling Firestore get()...", flush=True)
        doc = doc_ref.get()
        print("Document exists:", doc.exists, flush=True)
        if doc.exists:
            print("Data:", doc.to_dict(), flush=True)
    except ValueError as e:
        print(f"Already initialized or other error: {e}", flush=True)
except Exception as e:
    print(f"Certificate error: {type(e).__name__}: {e}", flush=True)

print("Time:", end=" ", flush=True)
os.system("date")
