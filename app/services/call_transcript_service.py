"""Call transcript database operations."""

import json
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.call_transcript import CallTranscript

logger = logging.getLogger("call_transcript_service")


async def save_transcript(
    db: AsyncSession,
    *,
    call_id: str | None,
    patient_id: str | None,
    phone_number: str | None,
    transcript: str | None,
    summary: str | None,
    ended_reason: str | None,
) -> CallTranscript:
    record = CallTranscript(
        call_id=call_id,
        patient_id=patient_id,
        phone_number=phone_number,
        transcript=transcript,
        summary=summary,
        ended_reason=ended_reason,
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)
    logger.info(
        json.dumps(
            {
                "event": "call_transcript_saved",
                "call_id": call_id,
                "patient_id": patient_id,
                "has_transcript": transcript is not None,
                "has_summary": summary is not None,
            }
        )
    )
    return record


async def list_transcripts_for_patient(db: AsyncSession, patient_id: str) -> list[CallTranscript]:
    result = await db.execute(
        select(CallTranscript)
        .where(CallTranscript.patient_id == patient_id)
        .order_by(CallTranscript.created_at.desc())
    )
    return list(result.scalars().all())
