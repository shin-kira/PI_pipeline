import os
import json
import time
import requests

_READ_TIMEOUT = 10
_WRITE_TIMEOUT = 10
_TOKEN_URL = "https://oauth2.googleapis.com/token"
_SCOPE = "https://www.googleapis.com/auth/cloud-platform"


def _find_credential_path():
    directory = os.path.dirname(__file__)
    candidates = []
    for variable in ("FIREBASE_SERVICE_KEY", "GOOGLE_APPLICATION_CREDENTIALS"):
        value = os.environ.get(variable)
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
            os.path.join(os.getcwd(), "AccountServiceKey.json"),
            os.path.join(os.getcwd(), "serviceKey.json"),
        ]
    )

    seen = set()
    for candidate in candidates:
        if candidate in seen:
            continue
        seen.add(candidate)
        if not os.path.isfile(candidate):
            continue
        try:
            with open(candidate, encoding="utf-8") as key_file:
                key_data = json.load(key_file)
            if all(
                key_data.get(field)
                for field in ("private_key", "client_email", "project_id")
            ):
                return candidate
        except (OSError, ValueError, TypeError):
            continue

    try:
        for entry in os.scandir(directory):
            if not entry.is_file() or not entry.name.lower().endswith(".json"):
                continue
            try:
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


_credential_file = _find_credential_path()
_creds = None
_access_token = None
_token_expires = 0
_initialization_error = None

try:
    if _credential_file is None:
        raise FileNotFoundError(
            "No Firebase service-account key found. Set FIREBASE_SERVICE_KEY or place "
            "serviceAccountKey.json, AccountServiceKey.json, or serviceKey.json beside "
            "firebaseManager.py."
        )
    with open(_credential_file, encoding="utf-8") as key_file:
        _creds = json.load(key_file)
    missing = [
        field
        for field in ("private_key", "client_email", "project_id")
        if not _creds.get(field)
    ]
    if missing:
        raise ValueError(f"Firebase key is missing: {', '.join(missing)}")
    print(
        f"Firebase credentials loaded from {os.path.basename(_credential_file)}",
        flush=True,
    )
except Exception as exc:
    _creds = None
    _initialization_error = exc
    print(f"Firebase init error: {exc}", flush=True)


def is_initialized():
    return _creds is not None


def initialization_error():
    return _initialization_error


def credential_path():
    return _credential_file


def _get_access_token():
    global _access_token, _token_expires
    now = time.time()
    if _access_token and now < _token_expires:
        return _access_token
    if not _creds:
        raise RuntimeError("Firebase credentials not loaded")

    try:
        import jwt
    except ImportError as exc:
        raise RuntimeError(
            "PyJWT is required for Firebase authentication. Install it with: "
            "python3 -m pip install PyJWT"
        ) from exc

    now_int = int(now)
    payload = {
        "iss": _creds["client_email"],
        "scope": _SCOPE,
        "aud": _creds.get("token_uri", _TOKEN_URL),
        "iat": now_int,
        "exp": now_int + 3600,
    }
    signed_jwt = jwt.encode(
        payload,
        _creds["private_key"],
        algorithm="RS256",
    )
    if isinstance(signed_jwt, bytes):
        signed_jwt = signed_jwt.decode("utf-8")

    response = requests.post(
        _creds.get("token_uri", _TOKEN_URL),
        data={
            "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
            "assertion": signed_jwt,
        },
        timeout=10,
    )
    if not response.ok:
        raise RuntimeError(
            f"Firebase token request failed: {response.status_code} {response.text[:500]}"
        )
    token_data = response.json()
    _access_token = token_data["access_token"]
    _token_expires = now + 3500
    return _access_token


def _headers():
    return {"Authorization": f"Bearer {_get_access_token()}"}


def _parse_fields(fields):
    result = {}
    for key, value in fields.items():
        if "stringValue" in value:
            result[key] = value["stringValue"]
        elif "integerValue" in value:
            result[key] = int(value["integerValue"])
        elif "doubleValue" in value:
            result[key] = float(value["doubleValue"])
        elif "booleanValue" in value:
            result[key] = bool(value["booleanValue"])
        elif "arrayValue" in value:
            result[key] = value["arrayValue"]
        elif "mapValue" in value:
            result[key] = _parse_fields(value["mapValue"].get("fields", {}))
    return result


def _value_to_fv(value):
    if isinstance(value, bool):
        return {"booleanValue": value}
    if isinstance(value, int):
        return {"integerValue": value}
    if isinstance(value, float):
        return {"doubleValue": value}
    if isinstance(value, str):
        return {"stringValue": value}
    if isinstance(value, dict):
        return {"mapValue": {"fields": _serialize_fields(value)}}
    if isinstance(value, list):
        return {"arrayValue": {"values": [_value_to_fv(item) for item in value]}}
    return {"nullValue": None}


def _serialize_fields(data):
    return {key: _value_to_fv(value) for key, value in data.items()}


def read_data(boat_name, boat_id):
    if not _creds:
        print("Firebase not initialized", flush=True)
        if _initialization_error is not None:
            print(f"Firebase initialization detail: {_initialization_error}", flush=True)
        return None
    try:
        url = (
            f"https://firestore.googleapis.com/v1/projects/"
            f"{_creds['project_id']}/databases/(default)/documents/"
            f"boat/{boat_name}:{boat_id}"
        )
        response = requests.get(
            url,
            headers=_headers(),
            timeout=_READ_TIMEOUT,
        )
        if response.status_code == 404:
            print("[Firebase] Document not found", flush=True)
            return None
        if not response.ok:
            raise RuntimeError(
                f"Firebase read failed: {response.status_code} {response.text[:500]}"
            )
        return _parse_fields(response.json().get("fields", {}))
    except Exception as exc:
        print(f"Firebase read error: {exc}", flush=True)
        if "Invalid JWT Signature" in str(exc) or "invalid_grant" in str(exc):
            print(
                "Firebase rejected the service-account key. Download a new JSON key "
                "from Google Cloud Console and replace the local key file.",
                flush=True,
            )
        return None


def write_data(boat_name, boat_id, payload):
    if not isinstance(payload, dict):
        print("Firebase payload must be a dict", flush=True)
        return False
    if not _creds:
        print("Firebase not initialized", flush=True)
        if _initialization_error is not None:
            print(f"Firebase initialization detail: {_initialization_error}", flush=True)
        return False
    try:
        data = dict(payload)
        data["timestamp"] = str(int(time.time()))
        url = (
            f"https://firestore.googleapis.com/v1/projects/"
            f"{_creds['project_id']}/databases/(default)/documents/"
            f"boat/{boat_name}:{boat_id}-telemetry"
        )
        response = requests.patch(
            url,
            headers={
                **_headers(),
                "Content-Type": "application/json",
            },
            params=[("updateMask.fieldPaths", key) for key in data],
            json={"fields": _serialize_fields(data)},
            timeout=_WRITE_TIMEOUT,
        )
        if not response.ok:
            raise RuntimeError(
                f"Firebase write failed: {response.status_code} {response.text[:500]}"
            )
        return True
    except Exception as exc:
        print(f"Firebase write error: {exc}", flush=True)
        if "Invalid JWT Signature" in str(exc) or "invalid_grant" in str(exc):
            print(
                "Firebase rejected the service-account key. Download a new JSON key "
                "from Google Cloud Console and replace the local key file.",
                flush=True,
            )
        return False
