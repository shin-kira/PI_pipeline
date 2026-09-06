import os
import json
import time
import requests

cer_path = os.environ.get(
    "FIREBASE_SERVICE_KEY",
    os.path.join(os.path.dirname(__file__), "serviceKey.json")
)
if not os.path.exists(cer_path):
    cer_path = os.path.join(os.path.dirname(__file__), "servicaAccountKey.json")


def _load_credentials():
    with open(cer_path) as f:
        return json.load(f)


_creds = None
try:
    _creds = _load_credentials()
    print("Firebase credentials loaded", flush=True)
except Exception as e:
    print(f"Firebase init error: {e}", flush=True)

_project_id = _creds.get("project_id") if _creds else None
_client_email = _creds.get("client_email") if _creds else None
_private_key = _creds.get("private_key") if _creds else None

SCOPE = "https://www.googleapis.com/auth/datastore"
TOKEN_URL = "https://oauth2.googleapis.com/token"
FIRESTORE_BASE = f"https://firestore.googleapis.com/v1/projects/{_project_id}/databases/(default)/documents"

_access_token = None
_token_expires = 0


def _get_access_token():
    global _access_token, _token_expires
    now = time.time()
    if _access_token and now < _token_expires:
        return _access_token

    if not _private_key or not _client_email:
        raise RuntimeError("Firebase credentials not loaded")

    try:
        import jwt
    except ImportError:
        print("PyJWT not installed. Install with: pip install PyJWT", flush=True)
        raise

    now_int = int(now)
    payload = {
        "iss": _client_email,
        "scope": SCOPE,
        "aud": TOKEN_URL,
        "iat": now_int,
        "exp": now_int + 3600,
    }
    signed_jwt = jwt.encode(payload, _private_key, algorithm="RS256")
    if isinstance(signed_jwt, bytes):
        signed_jwt = signed_jwt.decode("utf-8")

    resp = requests.post(
        TOKEN_URL,
        data={
            "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
            "assertion": signed_jwt,
        },
        timeout=10,
    )
    resp.raise_for_status()
    _access_token = resp.json()["access_token"]
    _token_expires = now + 3500
    return _access_token


def _headers():
    return {"Authorization": f"Bearer {_get_access_token()}"}


def read_data(boat_name, boat_id):
    if not _creds:
        print("Firebase not initialized", flush=True)
        return None
    try:
        url = f"{FIRESTORE_BASE}/boat/{boat_name}:{boat_id}"
        resp = requests.get(url, headers=_headers(), timeout=10)
        if resp.status_code == 404:
            print("[Firebase] Document not found", flush=True)
            return None
        resp.raise_for_status()
        fields = resp.json().get("fields", {})
        return _parse_fields(fields)
    except Exception as e:
        print(f"Firebase read error: {e}", flush=True)
        return None


def write_data(boat_name, boat_id, payload):
    if not _creds or not isinstance(payload, dict):
        print("Firebase not initialized or payload not a dict", flush=True)
        return False
    try:
        headers = _headers()
        headers["Content-Type"] = "application/json"
        body = {"fields": _serialize_fields(payload)}
        resp = requests.patch(
            f"{FIRESTORE_BASE}/boat/{boat_name}:{boat_id}",
            headers=headers,
            json=body,
            timeout=10,
        )
        resp.raise_for_status()
        return True
    except Exception as e:
        print(f"Firebase write error: {e}", flush=True)
        return False


def _parse_fields(fields):
    result = {}
    for key, val in fields.items():
        if "stringValue" in val:
            result[key] = val["stringValue"]
        elif "integerValue" in val:
            result[key] = int(val["integerValue"])
        elif "doubleValue" in val:
            result[key] = float(val["doubleValue"])
        elif "booleanValue" in val:
            result[key] = bool(val["booleanValue"])
        elif "arrayValue" in val:
            result[key] = val["arrayValue"]
        elif "mapValue" in val:
            result[key] = _parse_fields(val["mapValue"].get("fields", {}))
    return result


def _value_to_fv(val):
    if isinstance(val, bool):
        return {"booleanValue": val}
    elif isinstance(val, int):
        return {"integerValue": val}
    elif isinstance(val, float):
        return {"doubleValue": val}
    elif isinstance(val, str):
        return {"stringValue": val}
    elif isinstance(val, dict):
        return {"mapValue": {"fields": _serialize_fields(val)}}
    elif isinstance(val, list):
        return {"arrayValue": {"values": [_value_to_fv(v) for v in val]}}
    return {"nullValue": None}


def _serialize_fields(data):
    result = {}
    for key, val in data.items():
        result[key] = _value_to_fv(val)
    return result
