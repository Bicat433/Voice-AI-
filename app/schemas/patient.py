"""Pydantic schemas for Patient."""

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.models.patient import SexEnum
from app.schemas.validators import (
    normalize_phone,
    validate_alphanumeric,
    validate_dob,
    validate_name,
    validate_state,
    validate_zip_code,
)


class PatientBase(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=50)
    last_name: str = Field(..., min_length=1, max_length=50)
    date_of_birth: date
    sex: SexEnum
    phone_number: str
    email: EmailStr | None = None
    address_line_1: str = Field(..., min_length=1)
    address_line_2: str | None = None
    city: str = Field(..., min_length=1, max_length=100)
    state: str = Field(..., min_length=2, max_length=2)
    zip_code: str
    insurance_provider: str | None = None
    insurance_member_id: str | None = None
    preferred_language: str = "English"
    emergency_contact_name: str | None = None
    emergency_contact_phone: str | None = None

    @field_validator("first_name")
    @classmethod
    def validate_first_name(cls, v: str) -> str:
        return validate_name(v, "First name")

    @field_validator("last_name")
    @classmethod
    def validate_last_name(cls, v: str) -> str:
        return validate_name(v, "Last name")

    @field_validator("date_of_birth")
    @classmethod
    def validate_date_of_birth(cls, v: date) -> date:
        return validate_dob(v)

    @field_validator("phone_number")
    @classmethod
    def validate_phone_number(cls, v: str) -> str:
        return normalize_phone(v)

    @field_validator("state")
    @classmethod
    def validate_state_field(cls, v: str) -> str:
        return validate_state(v)

    @field_validator("zip_code")
    @classmethod
    def validate_zip(cls, v: str) -> str:
        return validate_zip_code(v)

    @field_validator("insurance_member_id")
    @classmethod
    def validate_insurance_member_id(cls, v: str | None) -> str | None:
        if v is None:
            return v
        return validate_alphanumeric(v)

    @field_validator("emergency_contact_phone")
    @classmethod
    def validate_emergency_phone(cls, v: str | None) -> str | None:
        if v is None:
            return v
        return normalize_phone(v)


class PatientCreate(PatientBase):
    pass


class PatientUpdate(BaseModel):
    first_name: str | None = Field(None, min_length=1, max_length=50)
    last_name: str | None = Field(None, min_length=1, max_length=50)
    date_of_birth: date | None = None
    sex: SexEnum | None = None
    phone_number: str | None = None
    email: EmailStr | None = None
    address_line_1: str | None = Field(None, min_length=1)
    address_line_2: str | None = None
    city: str | None = Field(None, min_length=1, max_length=100)
    state: str | None = Field(None, min_length=2, max_length=2)
    zip_code: str | None = None
    insurance_provider: str | None = None
    insurance_member_id: str | None = None
    preferred_language: str | None = None
    emergency_contact_name: str | None = None
    emergency_contact_phone: str | None = None

    @field_validator("first_name")
    @classmethod
    def validate_first_name(cls, v: str | None) -> str | None:
        if v is None:
            return v
        return validate_name(v, "First name")

    @field_validator("last_name")
    @classmethod
    def validate_last_name(cls, v: str | None) -> str | None:
        if v is None:
            return v
        return validate_name(v, "Last name")

    @field_validator("date_of_birth")
    @classmethod
    def validate_date_of_birth(cls, v: date | None) -> date | None:
        if v is None:
            return v
        return validate_dob(v)

    @field_validator("phone_number")
    @classmethod
    def validate_phone_number(cls, v: str | None) -> str | None:
        if v is None:
            return v
        return normalize_phone(v)

    @field_validator("state")
    @classmethod
    def validate_state_field(cls, v: str | None) -> str | None:
        if v is None:
            return v
        return validate_state(v)

    @field_validator("zip_code")
    @classmethod
    def validate_zip(cls, v: str | None) -> str | None:
        if v is None:
            return v
        return validate_zip_code(v)

    @field_validator("insurance_member_id")
    @classmethod
    def validate_insurance_member_id(cls, v: str | None) -> str | None:
        if v is None:
            return v
        return validate_alphanumeric(v)

    @field_validator("emergency_contact_phone")
    @classmethod
    def validate_emergency_phone(cls, v: str | None) -> str | None:
        if v is None:
            return v
        return normalize_phone(v)


class PatientResponse(PatientBase):
    model_config = ConfigDict(from_attributes=True)

    patient_id: str
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None


class CallTranscriptResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    call_id: str | None = None
    patient_id: str | None = None
    phone_number: str | None = None
    transcript: str | None = None
    summary: str | None = None
    ended_reason: str | None = None
    created_at: datetime


class ApiResponse(BaseModel):
    data: Any = None
    error: dict[str, str] | None = None


class ErrorDetail(BaseModel):
    message: str
    code: str
