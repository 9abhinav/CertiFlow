"""Pydantic schemas for recipient data."""

from pydantic import BaseModel, EmailStr, Field


class RecipientRequest(BaseModel):
    """Schema for a single recipient in a job creation request."""

    name: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Full name of the recipient",
        examples=["Abhinav Dewangan"],
    )
    email: EmailStr = Field(
        ...,
        description="Email address of the recipient",
        examples=["abhinav@example.com"],
    )
