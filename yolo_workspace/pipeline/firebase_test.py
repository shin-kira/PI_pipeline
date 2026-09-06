import os
import sys

print("Firebase connection test", flush=True)
print("=" * 40, flush=True)

from firebaseManager import read_data, write_data, _creds

print(f"Credentials loaded: {_creds is not None}", flush=True)

print("Testing Firestore read...", flush=True)
data = read_data("scuba", 9999)
print(f"Result: {data}", flush=True)

if data:
    print("\nFirebase is working!", flush=True)
    print(f"  relay: {data.get('relay')}", flush=True)
    print(f"  motor_a: {data.get('motor_a')}", flush=True)
    print(f"  motor_b: {data.get('motor_b')}", flush=True)
    print(f"  drive: {data.get('drive')}", flush=True)
    print(f"  switch: {data.get('switch')}", flush=True)
else:
    print("\nNo data returned. Check key and network.", flush=True)
