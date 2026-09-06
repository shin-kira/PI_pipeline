import os
import sys
import traceback

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
    import firebase_admin
    print("firebase_admin version:", firebase_admin.__version__, flush=True)
except ImportError as e:
    print(f"Import error: {e}", flush=True)
    sys.exit(1)

try:
    import google.auth
    from google.oauth2 import service_account
    print("google-auth version:", google.auth.__version__, flush=True)
except ImportError:
    pass

try:
    cer = credentials.Certificate(cer_path)
    print("Certificate loaded successfully", flush=True)
    print("Service account:", cer.service_account_email, flush=True)
except Exception as e:
    print(f"Certificate error: {type(e).__name__}: {e}", flush=True)
    traceback.print_exc()
    sys.exit(1)

# Try 1: Direct OAuth token request
try:
    print("Attempt 1: Direct OAuth token...", flush=True)
    access_token = cer.get_access_token()
    token_val = getattr(access_token, 'token', None) or getattr(access_token, 'access_token', None)
    print(f"OAuth token obtained: {token_val[:20] if token_val else 'None'}...", flush=True)
except Exception as e:
    print(f"OAuth token error: {type(e).__name__}: {e}", flush=True)
    traceback.print_exc()

# Try 2: Firestore client
try:
    print("Attempt 2: Firestore client...", flush=True)
    db = firestore.client()
    doc_ref = db.collection("boat").document("scuba:9999")
    print("Calling Firestore get()...", flush=True)
    doc = doc_ref.get()
    print("Document exists:", doc.exists, flush=True)
    if doc.exists:
        print("Data:", doc.to_dict(), flush=True)
    else:
        print("Document not found.", flush=True)
except Exception as e:
    print(f"Firestore error: {type(e).__name__}: {e}", flush=True)
    traceback.print_exc()

# Try 3: Raw HTTP request
try:
    print("Attempt 3: Raw HTTP test...", flush=True)
    import urllib.request
    import json

    # Try basic connectivity to Google OAuth
    req = urllib.request.Request("https://oauth2.googleapis.com/token", method="POST")
    req.add_header("Content-Type", "application/x-www-form-urlencoded")
    print("HTTPS connection to oauth2.googleapis.com succeeded (request sent)", flush=True)
except Exception as e:
    print(f"HTTPS error: {type(e).__name__}: {e}", flush=True)
    traceback.print_exc()
