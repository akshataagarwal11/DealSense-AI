"""Pydantic schemas validating Claude's scoring JSON response before it's trusted downstream."""
from typing import Literal

from pydantic import BaseModel, Field


class RiskFactor(BaseModel):
    factor: str
    severity: Literal["High", "Medium", "Low"]
    explanation: str


class RecommendedAction(BaseModel):
    action: str
    timeline: str
    owner: str


class ScoreResult(BaseModel):
    final_score: Literal["High", "Medium", "Low"]
    confidence: int = Field(ge=0, le=100)
    risk_factors: list[RiskFactor]
    recommended_actions: list[RecommendedAction]
    policy_references: list[str] = []
    narrative_summary: str
    confidence_explanation: str
