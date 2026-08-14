"""Patient API routes."""

from datetime import date

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.patient import ApiResponse, PatientCreate, PatientResponse, PatientUpdate
from app.schemas.validators import normalize_phone
from app.services import patient_service

router = APIRouter(prefix="/patients", tags=["patients"])


def _success(data, status_code: int = status.HTTP_200_OK) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content=ApiResponse(data=data, error=None).model_dump(mode="json"),
    )


def _error(message: str, code: str, status_code: int) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content=ApiResponse(data=None, error={"message": message, "code": code}).model_dump(),
    )


@router.get("/lookup")
async def lookup_patient(
    phone_number: str = Query(..., description="US 10-digit phone number"),
    db: AsyncSession = Depends(get_db),
):
    try:
        normalized = normalize_phone(phone_number)
    except ValueError as exc:
        return _error(str(exc), "INVALID_PHONE", status.HTTP_400_BAD_REQUEST)

    patient = await patient_service.lookup_by_phone(db, normalized)
    if patient is None:
        return _success(None)

    return _success(PatientResponse.model_validate(patient).model_dump(mode="json"))


@router.get("")
async def list_patients(
    last_name: str | None = Query(None),
    date_of_birth: date | None = Query(None),
    phone_number: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    normalized_phone = None
    if phone_number is not None:
        try:
            normalized_phone = normalize_phone(phone_number)
        except ValueError as exc:
            return _error(str(exc), "INVALID_PHONE", status.HTTP_400_BAD_REQUEST)

    patients = await patient_service.list_patients(
        db,
        last_name=last_name,
        date_of_birth=date_of_birth,
        phone_number=normalized_phone,
    )
    data = [PatientResponse.model_validate(p).model_dump(mode="json") for p in patients]
    return _success(data)


@router.get("/{patient_id}")
async def get_patient(patient_id: str, db: AsyncSession = Depends(get_db)):
    patient = await patient_service.get_patient_by_id(db, patient_id)
    if patient is None:
        return _error("Patient not found", "NOT_FOUND", status.HTTP_404_NOT_FOUND)
    return _success(PatientResponse.model_validate(patient).model_dump(mode="json"))


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_patient(payload: PatientCreate, db: AsyncSession = Depends(get_db)):
    try:
        patient = await patient_service.create_patient(db, payload)
    except Exception:
        return _error(
            "Failed to create patient record",
            "DATABASE_ERROR",
            status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
    return _success(
        PatientResponse.model_validate(patient).model_dump(mode="json"),
        status_code=status.HTTP_201_CREATED,
    )


@router.put("/{patient_id}")
async def update_patient(
    patient_id: str,
    payload: PatientUpdate,
    db: AsyncSession = Depends(get_db),
):
    patient = await patient_service.get_patient_by_id(db, patient_id)
    if patient is None:
        return _error("Patient not found", "NOT_FOUND", status.HTTP_404_NOT_FOUND)

    try:
        updated = await patient_service.update_patient(db, patient, payload)
    except Exception:
        return _error(
            "Failed to update patient record",
            "DATABASE_ERROR",
            status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
    return _success(PatientResponse.model_validate(updated).model_dump(mode="json"))


@router.delete("/{patient_id}")
async def delete_patient(patient_id: str, db: AsyncSession = Depends(get_db)):
    patient = await patient_service.get_patient_by_id(db, patient_id)
    if patient is None:
        return _error("Patient not found", "NOT_FOUND", status.HTTP_404_NOT_FOUND)

    try:
        deleted = await patient_service.soft_delete_patient(db, patient)
    except Exception:
        return _error(
            "Failed to delete patient record",
            "DATABASE_ERROR",
            status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
    return _success(PatientResponse.model_validate(deleted).model_dump(mode="json"))
