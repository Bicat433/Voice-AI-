"""Patient API tests."""

import pytest
from httpx import AsyncClient

from tests.conftest import VALID_PATIENT


@pytest.mark.asyncio
async def test_create_patient(client: AsyncClient):
    response = await client.post("/patients", json=VALID_PATIENT)
    assert response.status_code == 201
    body = response.json()
    assert body["error"] is None
    assert body["data"]["first_name"] == "Alice"
    assert body["data"]["phone_number"] == "5551112233"
    assert "patient_id" in body["data"]


@pytest.mark.asyncio
async def test_list_patients(client: AsyncClient):
    await client.post("/patients", json=VALID_PATIENT)
    response = await client.get("/patients")
    assert response.status_code == 200
    body = response.json()
    assert len(body["data"]) >= 1


@pytest.mark.asyncio
async def test_get_patient(client: AsyncClient):
    create_resp = await client.post("/patients", json=VALID_PATIENT)
    patient_id = create_resp.json()["data"]["patient_id"]

    response = await client.get(f"/patients/{patient_id}")
    assert response.status_code == 200
    assert response.json()["data"]["patient_id"] == patient_id


@pytest.mark.asyncio
async def test_get_patient_not_found(client: AsyncClient):
    response = await client.get("/patients/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"


@pytest.mark.asyncio
async def test_update_patient(client: AsyncClient):
    create_resp = await client.post("/patients", json=VALID_PATIENT)
    patient_id = create_resp.json()["data"]["patient_id"]

    response = await client.put(f"/patients/{patient_id}", json={"city": "Evanston"})
    assert response.status_code == 200
    assert response.json()["data"]["city"] == "Evanston"


@pytest.mark.asyncio
async def test_soft_delete_patient(client: AsyncClient):
    create_resp = await client.post("/patients", json=VALID_PATIENT)
    patient_id = create_resp.json()["data"]["patient_id"]

    delete_resp = await client.delete(f"/patients/{patient_id}")
    assert delete_resp.status_code == 200
    assert delete_resp.json()["data"]["deleted_at"] is not None

    get_resp = await client.get(f"/patients/{patient_id}")
    assert get_resp.status_code == 404


@pytest.mark.asyncio
async def test_lookup_by_phone(client: AsyncClient):
    await client.post("/patients", json=VALID_PATIENT)

    response = await client.get("/patients/lookup", params={"phone_number": "5551112233"})
    assert response.status_code == 200
    assert response.json()["data"]["phone_number"] == "5551112233"

    no_match = await client.get("/patients/lookup", params={"phone_number": "5559999999"})
    assert no_match.status_code == 200
    assert no_match.json()["data"] is None


@pytest.mark.asyncio
async def test_validation_future_dob(client: AsyncClient):
    patient = {**VALID_PATIENT, "date_of_birth": "2099-01-01"}
    response = await client.post("/patients", json=patient)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_validation_invalid_phone(client: AsyncClient):
    patient = {**VALID_PATIENT, "phone_number": "123"}
    response = await client.post("/patients", json=patient)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_filter_by_last_name(client: AsyncClient):
    await client.post("/patients", json=VALID_PATIENT)

    response = await client.get("/patients", params={"last_name": "Smith"})
    assert response.status_code == 200
    assert all(p["last_name"] == "Smith" for p in response.json()["data"])
