"""Patient database operations."""

import json
import logging
from datetime import date, datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.patient import Patient
from app.schemas.patient import PatientCreate, PatientUpdate

logger = logging.getLogger("patient_service")


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _not_deleted(patient: Patient) -> bool:
    return patient.deleted_at is None


async def list_patients(
    db: AsyncSession,
    *,
    last_name: str | None = None,
    date_of_birth: date | None = None,
    phone_number: str | None = None,
) -> list[Patient]:
    query = select(Patient).where(Patient.deleted_at.is_(None))

    if last_name is not None:
        query = query.where(Patient.last_name.ilike(last_name))
    if date_of_birth is not None:
        query = query.where(Patient.date_of_birth == date_of_birth)
    if phone_number is not None:
        query = query.where(Patient.phone_number == phone_number)

    query = query.order_by(Patient.created_at.desc())
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_patient_by_id(db: AsyncSession, patient_id: str) -> Patient | None:
    result = await db.execute(select(Patient).where(Patient.patient_id == patient_id))
    patient = result.scalar_one_or_none()
    if patient is None or not _not_deleted(patient):
        return None
    return patient


async def lookup_by_phone(db: AsyncSession, phone_number: str) -> Patient | None:
    result = await db.execute(
        select(Patient).where(
            Patient.phone_number == phone_number,
            Patient.deleted_at.is_(None),
        )
    )
    return result.scalar_one_or_none()


async def create_patient(db: AsyncSession, payload: PatientCreate) -> Patient:
    patient = Patient(**payload.model_dump())
    db.add(patient)
    await db.commit()
    await db.refresh(patient)
    logger.info(
        json.dumps(
            {
                "event": "patient_created",
                "patient_id": patient.patient_id,
                "payload": payload.model_dump(mode="json"),
            }
        )
    )
    return patient


async def update_patient(
    db: AsyncSession, patient: Patient, payload: PatientUpdate
) -> Patient:
    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(patient, field, value)
    patient.updated_at = _utc_now()
    await db.commit()
    await db.refresh(patient)
    logger.info(
        json.dumps(
            {
                "event": "patient_updated",
                "patient_id": patient.patient_id,
                "payload": update_data,
            }
        )
    )
    return patient


async def soft_delete_patient(db: AsyncSession, patient: Patient) -> Patient:
    patient.deleted_at = _utc_now()
    patient.updated_at = _utc_now()
    await db.commit()
    await db.refresh(patient)
    logger.info(
        json.dumps(
            {
                "event": "patient_soft_deleted",
                "patient_id": patient.patient_id,
            }
        )
    )
    return patient
