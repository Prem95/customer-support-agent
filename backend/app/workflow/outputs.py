from pydantic import BaseModel, Field

from app.schemas import IntentName


class IntentAnalysis(BaseModel):
    intent: IntentName
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: str = Field(description="One sentence explaining the classification.")
    needs_retrieval: bool = Field(
        description="True if internal knowledge would help the agent; false for greetings, thanks, or pure emotion."
    )
    search_query: str = Field(
        description="Short keyword query for the knowledge base, or empty string."
    )


class Recommendations(BaseModel):
    suggested_response: str = Field(
        description="Ready-to-send draft reply to the customer, professional and empathetic, grounded in the retrieved knowledge. Do not invent policy details."
    )
    missing_info: list[str] = Field(
        description="Information or documents still needed from the customer, e.g. claim reference number, photos, police report."
    )
    next_action: str = Field(description="One concrete next step for the agent.")


class SummaryOutput(BaseModel):
    summary: str = Field(
        description="Under 120 words, formatted as: Issue: ... | Key facts: ... | Still missing: ... | Next step: ..."
    )
