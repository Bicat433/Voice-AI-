"""Schemas for Vapi tool-call webhook payloads."""

from typing import Any

from pydantic import BaseModel, Field


class VapiFunction(BaseModel):
    name: str | None = None
    arguments: dict[str, Any] = Field(default_factory=dict)


class VapiToolCall(BaseModel):
    id: str
    function: VapiFunction = Field(default_factory=VapiFunction)


class VapiMessage(BaseModel):
    toolCalls: list[VapiToolCall] = Field(default_factory=list)


class VapiWebhookPayload(BaseModel):
    message: VapiMessage = Field(default_factory=VapiMessage)


class VapiToolResult(BaseModel):
    toolCallId: str
    result: str


class VapiToolResponse(BaseModel):
    results: list[VapiToolResult]
