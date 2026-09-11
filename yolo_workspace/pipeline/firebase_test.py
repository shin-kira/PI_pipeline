import os
import sys

print("Firebase connection test", flush=True)
print("=" * 40, flush=True)

from firebaseManager import (
    initialization_error,
    is_initialized,
    read_data,
    write_data,
)

print(f"Firebase initialized: {is_initialized()}", flush=True)
if not is_initialized():
    print(f"Initialization error: {initialization_error()}", flush=True)

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
    print("\nNo data returned. Check the key, network, and Firestore document.", flush=True)
