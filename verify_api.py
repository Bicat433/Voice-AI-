"""Verify CRUD endpoints against local API."""

import httpx
import json

base = "http://localhost:8000"
payload = {
    "first_name": "Jane",
    "last_name": "Doe",
    "date_of_birth": "1990-01-01",
    "sex": "Female",
    "phone_number": "5551234567",
    "address_line_1": "123 Main St",
    "city": "Austin",
    "state": "TX",
    "zip_code": "78701",
}

print("=== CREATE ===")
r = httpx.post(f"{base}/patients", json=payload)
print(r.status_code, json.dumps(r.json(), indent=2))
assert r.status_code == 201, r.text
pid = r.json()["data"]["patient_id"]

print("\n=== LIST ===")
r = httpx.get(f"{base}/patients")
body = r.json()
print(r.status_code, f"count={len(body['data'])}")
assert r.status_code == 200

print("\n=== GET ONE ===")
r = httpx.get(f"{base}/patients/{pid}")
print(r.status_code, json.dumps(r.json(), indent=2))
assert r.status_code == 200

print("\n=== UPDATE ===")
r = httpx.put(f"{base}/patients/{pid}", json={"email": "jane@example.com"})
print(r.status_code, json.dumps(r.json(), indent=2))
assert r.status_code == 200
assert r.json()["data"]["email"] == "jane@example.com"

print("\n=== SOFT DELETE ===")
r = httpx.delete(f"{base}/patients/{pid}")
print(r.status_code, json.dumps(r.json(), indent=2))
assert r.status_code == 200
assert r.json()["data"]["deleted_at"] is not None

print("\n=== GET AFTER DELETE (expect 404) ===")
r = httpx.get(f"{base}/patients/{pid}")
print(r.status_code, json.dumps(r.json(), indent=2))
assert r.status_code == 404

print("\nAll checks passed.")
