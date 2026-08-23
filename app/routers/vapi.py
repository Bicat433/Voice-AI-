"""Vapi tool-call adapter endpoints."""

import logging
from datetime import date
from typing import Any

from dateutil.parser import parse as parse_date
from fastapi import APIRouter, Depends, Request
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.patient import PatientCreate, PatientUpdate
from app.schemas.validators import normalize_phone
from app.schemas.vapi import VapiToolResponse
from app.services import patient_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/vapi", tags=["vapi"])


def _vapi_response(tool_call_id: str, result: str) -> VapiToolResponse:
    return VapiToolResponse(results=[{"toolCallId": tool_call_id, "result": result}])


async def _extract_tool_call(request: Request) -> tuple[str | None, dict[str, Any], str | None]:
    try:
        body = await request.json()
    except Exception as exc:
        return None, {}, f"Invalid request body: {exc}"

    tool_calls = body.get("message", {}).get("toolCalls", [])
    if not tool_calls:
        return None, {}, "No tool calls in request"

    tool_call = tool_calls[0]
    tool_call_id = tool_call.get("id")
    if not tool_call_id:
        return None, {}, "Missing tool call ID"

    arguments = tool_call.get("function", {}).get("arguments", {})
    if not isinstance(arguments, dict):
        return tool_call_id, {}, "Tool call arguments must be an object"

    return tool_call_id, arguments, None


def _parse_date_of_birth(value: Any) -> date:
    if isinstance(value, date):
        return value
    if not isinstance(value, str):
        raise ValueError("Date of birth must be a string or date")
    try:
        return date.fromisoformat(value)
    except ValueError:
        return parse_date(value, dayfirst=False).date()


def _prepare_create_arguments(arguments: dict[str, Any]) -> dict[str, Any]:
    prepared = dict(arguments)
    if "date_of_birth" in prepared:
        prepared["date_of_birth"] = _parse_date_of_birth(prepared["date_of_birth"])
    return prepared


def _prepare_update_arguments(arguments: dict[str, Any]) -> tuple[str | None, dict[str, Any]]:
    prepared = dict(arguments)
    patient_id = prepared.pop("patient_id", None)
    if "date_of_birth" in prepared:
        prepared["date_of_birth"] = _parse_date_of_birth(prepared["date_of_birth"])
    return patient_id, prepared


@router.post("/lookup_patient", response_model=VapiToolResponse)
async def vapi_lookup_patient(request: Request, db: AsyncSession = Depends(get_db)):
    tool_call_id, arguments, error = await _extract_tool_call(request)
    if error:
        return _vapi_response(tool_call_id or "unknown", error)

    phone_number = arguments.get("phone_number")
    if not phone_number:
        return _vapi_response(tool_call_id, "phone_number is required")

    try:
        normalized = normalize_phone(str(phone_number))
        patient = await patient_service.lookup_by_phone(db, normalized)
    except ValueError as exc:
        return _vapi_response(tool_call_id, str(exc))
    except Exception as exc:
        logger.exception("Vapi lookup failed")
        return _vapi_response(tool_call_id, f"Lookup failed: {exc}")

    if patient is None:
        return _vapi_response(tool_call_id, "No existing patient found.")

    return _vapi_response(
        tool_call_id,
        f"Found existing patient: {patient.first_name} {patient.last_name} "
        f"(patient_id: {patient.patient_id})",
    )


@router.post("/create_patient", response_model=VapiToolResponse)
async def vapi_create_patient(request: Request, db: AsyncSession = Depends(get_db)):
    tool_call_id, arguments, error = await _extract_tool_call(request)
    if error:
        return _vapi_response(tool_call_id or "unknown", error)

    try:
        payload = PatientCreate.model_validate(_prepare_create_arguments(arguments))
        await patient_service.create_patient(db, payload)
    except ValidationError as exc:
        message = exc.errors()[0]["msg"] if exc.errors() else str(exc)
        return _vapi_response(tool_call_id, f"Failed to save: {message}")
    except Exception as exc:
        logger.exception("Vapi create failed")
        return _vapi_response(tool_call_id, f"Failed to save: {exc}")

    return _vapi_response(tool_call_id, "Patient created successfully")


@router.post("/update_patient", response_model=VapiToolResponse)
async def vapi_update_patient(request: Request, db: AsyncSession = Depends(get_db)):
    tool_call_id, arguments, error = await _extract_tool_call(request)
    if error:
        return _vapi_response(tool_call_id or "unknown", error)

    try:
        patient_id, update_args = _prepare_update_arguments(arguments)
        if not patient_id:
            return _vapi_response(tool_call_id, "Failed to save: patient_id is required")

        patient = await patient_service.get_patient_by_id(db, patient_id)
        if patient is None:
            return _vapi_response(tool_call_id, "Failed to save: Patient not found")

        payload = PatientUpdate.model_validate(update_args)
        await patient_service.update_patient(db, patient, payload)
    except ValidationError as exc:
        message = exc.errors()[0]["msg"] if exc.errors() else str(exc)
        return _vapi_response(tool_call_id, f"Failed to save: {message}")
    except Exception as exc:
        logger.exception("Vapi update failed")
        return _vapi_response(tool_call_id, f"Failed to save: {exc}")

    return _vapi_response(tool_call_id, "Patient updated successfully")
