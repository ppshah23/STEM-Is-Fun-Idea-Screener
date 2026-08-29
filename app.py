from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from pipeline.intake import screen_idea

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["POST"],
    allow_headers=["*"],
)


class ScreenRequest(BaseModel):
    idea: str


@app.post("/api/screen-idea")
def screen_idea_endpoint(req: ScreenRequest) -> dict:
    assessment, _ = screen_idea(req.idea)
    return assessment
