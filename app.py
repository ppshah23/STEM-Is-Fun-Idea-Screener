from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from pipeline import io, steps
from pipeline.intake import classify_level, review_curriculum, screen_idea

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["POST"],
    allow_headers=["*"],
)


class ScreenRequest(BaseModel):
    idea: str


class ClassifyRequest(BaseModel):
    idea: str


class ReviewRequest(BaseModel):
    curriculum_text: str
    constraints: str | None = None


class InterviewTurn(BaseModel):
    role: str
    message: str


class InterviewRequest(BaseModel):
    idea: str
    transcript: list[InterviewTurn] = []
    level: str | None = None


@app.post("/api/screen-idea")
def screen_idea_endpoint(req: ScreenRequest) -> dict:
    assessment, _ = screen_idea(req.idea)
    return assessment


@app.post("/api/classify-level")
def classify_level_endpoint(req: ClassifyRequest) -> dict:
    classification, _ = classify_level(req.idea)
    return classification


@app.post("/api/review-curriculum")
def review_curriculum_endpoint(req: ReviewRequest) -> dict:
    review, _ = review_curriculum(req.curriculum_text, req.constraints)
    return review


@app.post("/api/interview-turn")
def interview_turn_endpoint(req: InterviewRequest) -> dict:
    transcript = [turn.model_dump() for turn in req.transcript]
    return steps.interview_turn(req.idea, transcript, req.level)


@app.post("/api/generate-roadmap")
def generate_roadmap_endpoint(req: InterviewRequest) -> dict:
    transcript = [turn.model_dump() for turn in req.transcript]
    enriched_idea = steps.enrich_idea_with_interview(req.idea, transcript)
    roadmap = steps.draft_curriculum_roadmap(enriched_idea, level=req.level)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    name = f"{timestamp}_{io.slugify(req.idea)}"
    io.save_roadmap(name, req.idea, roadmap)

    return roadmap
