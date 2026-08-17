"""Tests for Vapi adapter endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_vapi_lookup_found(client: AsyncClient):
    from tests.conftest import VALID_PATIENT

    await client.post("/patients", json=VALID_PATIENT)

    response = await client.post(
        "/vapi/lookup_patient",
        json={
            "message": {
                "toolCalls": [
                    {
                        "id": "call_test1",
                        "function": {
                            "name": "lookup_patient_by_phone",
                            "arguments": {"phone_number": "5551112233"},
                        },
                    }
                ]
            }
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body == {
        "results": [
            {
                "toolCallId": "call_test1",
                "result": "Found existing patient: Alice Smith",
            }
        ]
    }


@pytest.mark.asyncio
async def test_vapi_lookup_not_found(client: AsyncClient):
    response = await client.post(
        "/vapi/lookup_patient",
        json={
            "message": {
                "toolCalls": [
                    {
                        "id": "call_test1",
                        "function": {
                            "name": "lookup_patient_by_phone",
                            "arguments": {"phone_number": "5550000000"},
                        },
                    }
                ]
            }
        },
    )
    assert response.status_code == 200
    assert response.json() == {
        "results": [{"toolCallId": "call_test1", "result": "No existing patient found."}]
    }


@pytest.mark.asyncio
async def test_vapi_create_patient(client: AsyncClient):
    response = await client.post(
        "/vapi/create_patient",
        json={
            "message": {
                "toolCalls": [
                    {
                        "id": "call_test2",
                        "function": {
                            "name": "create_patient",
                            "arguments": {
                                "first_name": "Voice",
                                "last_name": "Test",
                                "date_of_birth": "01/01/1990",
                                "sex": "Male",
                                "phone_number": "5559998888",
                                "address_line_1": "1 Test St",
                                "city": "Austin",
                                "state": "TX",
                                "zip_code": "78701",
                            },
                        },
                    }
                ]
            }
        },
    )
    assert response.status_code == 200
    assert response.json() == {
        "results": [{"toolCallId": "call_test2", "result": "Patient created successfully"}]
    }


@pytest.mark.asyncio
async def test_vapi_update_patient(client: AsyncClient):
    from tests.conftest import VALID_PATIENT

    create_resp = await client.post("/patients", json=VALID_PATIENT)
    patient_id = create_resp.json()["data"]["patient_id"]

    response = await client.post(
        "/vapi/update_patient",
        json={
            "message": {
                "toolCalls": [
                    {
                        "id": "call_test3",
                        "function": {
                            "name": "update_patient",
                            "arguments": {
                                "patient_id": patient_id,
                                "email": "voice@example.com",
                            },
                        },
                    }
                ]
            }
        },
    )
    assert response.status_code == 200
    assert response.json() == {
        "results": [{"toolCallId": "call_test3", "result": "Patient updated successfully"}]
    }
