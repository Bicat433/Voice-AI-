"""Seed demo data on first boot."""

from datetime import date

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.patient import Patient, SexEnum


async def seed_demo_patient(db: AsyncSession) -> None:
    result = await db.execute(select(func.count()).select_from(Patient))
    count = result.scalar_one()
    if count > 0:
        return

    demo = Patient(
        first_name="Jane",
        last_name="Doe",
        date_of_birth=date(1985, 3, 15),
        sex=SexEnum.FEMALE,
        phone_number="5551234567",
        email="jane.doe@example.com",
        address_line_1="123 Main Street",
        address_line_2="Apt 4B",
        city="Springfield",
        state="IL",
        zip_code="62701",
        insurance_provider="Blue Cross",
        insurance_member_id="BC123456",
        preferred_language="English",
        emergency_contact_name="John Doe",
        emergency_contact_phone="5559876543",
    )
    db.add(demo)
    await db.commit()
