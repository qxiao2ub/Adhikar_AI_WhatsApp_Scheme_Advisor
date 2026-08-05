from pathlib import Path
from typing import Optional

from fastapi import FastAPI
from pydantic import BaseModel, Field

from core_engine import UserProfile, load_default_engine

ROOT = Path(__file__).resolve().parent
engine = load_default_engine(ROOT)
app = FastAPI(title="Adhikar AI Mobile API", version="0.1.0")


class ProfileRequest(BaseModel):
    age: Optional[int] = Field(default=None, ge=0, le=120)
    annual_income: Optional[float] = Field(default=None, ge=0)
    gender: str = "Prefer not to say"
    marital_status: str = "Prefer not to say"
    state: str = ""
    residence: str = "Prefer not to say"
    social_category: str = "Prefer not to say"
    student: bool = False
    pregnant: bool = False
    disability: bool = False
    entrepreneur: bool = False
    street_vendor: bool = False
    farmer: bool = False
    housing_need: bool = False
    bank_account: bool = False
    need_text: str = ""


@app.get("/health")
def health():
    return {"status": "ok", "service": "adhikar-ai-mobile-api"}


@app.post("/recommend")
def recommend(request: ProfileRequest):
    profile = UserProfile(**request.model_dump())
    return {
        "disclaimer": "Potential matches only. Verify every result with myScheme or the responsible authority.",
        "need_cluster": engine.need_cluster(profile.need_text),
        "results": engine.recommend(profile, top_k=6),
    }
