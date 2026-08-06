"""
SEHAT - doctor-style health consultation & first aid.

Run:      uvicorn main:app --reload
Deploy:   see render.yaml / README.md
"""

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator, model_validator

import consult
import firstaid
import otc
from llm import config

app = FastAPI(title="SEHAT", version="2.0")

STATIC = Path(__file__).parent / "static"


# ------------------------------------------------------------------- models

class StartBody(BaseModel):
    age: int = Field(ge=0, le=120)
    sex: str
    pregnant: bool = False
    pregnancy_weeks: int | None = Field(default=None, ge=1, le=45)
    complaint: str = Field(min_length=3, max_length=2000)
    duration: str = Field(default="", max_length=200)
    conditions: str = Field(default="", max_length=500)

    @field_validator("sex")
    @classmethod
    def _sex(cls, v: str) -> str:
        v = v.lower().strip()
        if v not in {"male", "female"}:
            raise ValueError("sex must be male or female")
        return v

    @model_validator(mode="after")
    def _pregnancy(self):
        if self.pregnant:
            if self.sex != "female":
                raise ValueError("pregnancy applies to female patients")
            if not self.pregnancy_weeks:
                raise ValueError("pregnancy_weeks is required when pregnant - "
                                 "how many weeks along is she?")
        else:
            self.pregnancy_weeks = None
        return self


class AnswerBody(BaseModel):
    session_id: str = Field(min_length=8, max_length=64)
    answer: str = Field(min_length=1, max_length=2000)


# ------------------------------------------------------------------- routes

@app.get("/api/health")
def health():
    cfg = config()
    return {
        "ok": True,
        "app": "SEHAT",
        "version": "2.0",
        "ai_configured": cfg["configured"],
        "provider": cfg["provider"] if cfg["configured"] else None,
        "model": cfg["model"] if cfg["configured"] else None,
        "mode": "full" if cfg["configured"] else "demo",
        "emergency_number": firstaid.CALL,
    }


@app.get("/api/otc")
def otc_table(pregnant: bool = False):
    return {"pregnant": pregnant, "medicines": otc.table(pregnant)}


@app.get("/api/firstaid")
def firstaid_list():
    return {"call": firstaid.CALL, "protocols": firstaid.list_protocols()}


@app.get("/api/firstaid/{pid}")
def firstaid_item(pid: str):
    p = firstaid.get_protocol(pid)
    if not p:
        raise HTTPException(404, "Unknown first-aid protocol")
    return p


@app.post("/api/consult/start")
def consult_start(body: StartBody):
    return consult.start(body.model_dump())


@app.post("/api/consult/answer")
def consult_answer(body: AnswerBody):
    return consult.answer(body.session_id, body.answer)


# ------------------------------------------------------------------- static

app.mount("/static", StaticFiles(directory=STATIC), name="static")

_FAVICON = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32">'
    '<rect width="32" height="32" rx="7" fill="#0e6e5c"/>'
    '<path d="M13 6h6v7h7v6h-7v7h-6v-7H6v-6h7z" fill="#fff"/></svg>'
)


@app.get("/favicon.ico")
def favicon():
    return Response(content=_FAVICON, media_type="image/svg+xml")


@app.get("/")
def index():
    return FileResponse(STATIC / "index.html")
