import os
import time

_db = None
_initialization_error = None
_READ_TIMEOUT = 10
_WRITE_TIMEOUT = 10


def _credential_path():
    configured = os.environ.get("FIREBASE_SERVICE_KEY")
    standard = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    directory = os.path.dirname(__file__)
    candidates = []
    for value in (configured, standard):
        if value:
            candidates.append(os.path.abspath(value))
    candidates.extend(
        [
            os.path.join(directory, "serviceAccountKey.json"),
            os.path.join(directory, "ServiceAccountKey.JSON"),
            os.path.join(directory, "AccountServiceKey.json"),
            os.path.join(directory, "accountServiceKey.json"),
            os.path.join(directory, "AccountServiceKey.JSON"),
            os.path.join(directory, "serviceKey.json"),
            os.path.join(directory, "servicaAccountKey.json"),
            os.path.join(os.getcwd(), "serviceAccountKey.json"),
            os.path.join(os.getcwd(), "serviceKey.json"),
        ]
    )

    seen = set()
    for candidate in candidates:
        if candidate in seen:
            continue
        seen.add(candidate)
        if os.path.isfile(candidate):
            return candidate

    try:
        for entry in os.scandir(directory):
            if not entry.is_file() or not entry.name.lower().endswith(".json"):
                continue
            try:
                import json

                with open(entry.path, encoding="utf-8") as key_file:
                    key_data = json.load(key_file)
                if all(
                    key_data.get(field)
                    for field in ("private_key", "client_email", "project_id")
                ):
                    return os.path.abspath(entry.path)
            except (OSError, ValueError, TypeError):
                continue
    except OSError:
        pass

    return None


try:
    from firebase_admin import credentials
    from google.cloud import firestore

    credential_path = _credential_path()
    if credential_path is None:
        raise FileNotFoundError(
            "No Firebase service-account key found. Set FIREBASE_SERVICE_KEY or place "
            "a service-account JSON file beside firebaseManager.py."
        )

    certificate = credentials.Certificate(credential_path)
    _db = firestore.Client(
        project=certificate.project_id,
        credentials=certificate.get_credential(),
    )
    print(f"Firebase initialized from {os.path.basename(credential_path)}", flush=True)
except Exception as exc:
    _initialization_error = exc
    print(f"Firebase init error: {exc}", flush=True)


def is_initialized():
    return _db is not None


def initialization_error():
    return _initialization_error


def _report_auth_error(exc):
    message = str(exc)
    if "Invalid JWT Signature" in message or "invalid_grant" in message:
        print(
            "Firebase rejected the service-account key. Download a new JSON key "
            "from Google Cloud Console and replace the local key file.",
            flush=True,
        )


def _require_firestore():
    if _db is None:
        print("Firebase not initialized", flush=True)
        if _initialization_error is not None:
            print(f"Firebase initialization detail: {_initialization_error}", flush=True)
        return None
    return _db


def read_data(boat_name, boat_id):
    db = _require_firestore()
    if db is None:
        return None
    try:
        document = db.collection("boat").document(f"{boat_name}:{boat_id}")
        snapshot = document.get(timeout=_READ_TIMEOUT, retry=False)
        if not snapshot.exists:
            print("[Firebase] Document not found", flush=True)
            return None
        return snapshot.to_dict() or {}
    except Exception as exc:
        print(f"Firebase read error: {exc}", flush=True)
        _report_auth_error(exc)
        return None


def write_data(boat_name, boat_id, payload):
    if not isinstance(payload, dict):
        print("Firebase payload must be a dict", flush=True)
        return False
    db = _require_firestore()
    if db is None:
        return False
    try:
        data = dict(payload)
        data["timestamp"] = str(int(time.time()))
        document = db.collection("boat").document(f"{boat_name}:{boat_id}-telemetry")
        document.set(data, merge=True, timeout=_WRITE_TIMEOUT, retry=False)
        return True
    except Exception as exc:
        print(f"Firebase write error: {exc}", flush=True)
        _report_auth_error(exc)
        return False
