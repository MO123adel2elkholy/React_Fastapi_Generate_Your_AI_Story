"""Story API routes.

This module exposes the endpoints used to:
- create a new story generation job
- track background generation progress
- retrieve the complete story tree for a finished story

The routes work with:
- a session cookie for user tracking
- a background task system for asynchronous generation
- SQLAlchemy models from `models.story` and `models.job`
- Pydantic response schemas from `schemas.story` and `schemas.job`
"""

import uuid
from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Cookie, Response, BackgroundTasks
from sqlalchemy.orm import Session

from db.database import get_db, SessionLocal
from models.story import Story, StoryNode
from models.job import StoryJob
from schemas.story import (
    CompleteStoryResponse, CompleteStoryNodeResponse, CreateStoryRequest
)
from schemas.job import StoryJobResponse

router = APIRouter(
    prefix="/stories",
    tags=["stories"]
)


def get_session_id(session_id: Optional[str] = Cookie(None)):
    """Read the current session ID from the cookie or create a new one.

    Request shape:
        Cookie: session_id (optional)

    Response behavior:
        - If a cookie already exists, it is reused.
        - If no cookie exists, a new UUID is generated and returned.
    """
    if not session_id:
        session_id = str(uuid.uuid4())
    return session_id


@router.post("/create", response_model=StoryJobResponse)
def create_story(
        request: CreateStoryRequest,
        background_tasks: BackgroundTasks,
        response: Response,
        session_id: str = Depends(get_session_id),
        db: Session = Depends(get_db)
):
    """Create a story-generation job for the given theme.

    Request body shape:
        {
            "theme": "Fantasy adventure in a ruined kingdom"
        }

    Response shape:
        {
            "job_id": "uuid-string",
            "status": "pending",
            "story_id": null,
            "error": null,
            "created_at": "2026-09-15T12:00:00Z",
            "completed_at": null
        }

    Behavior:
        - stores the job in the database
        - sets the session cookie
        - schedules background generation task
    """
    response.set_cookie(key="session_id", value=session_id, httponly=True)

    job_id = str(uuid.uuid4())

    job = StoryJob(
        job_id=job_id,
        session_id=session_id,
        theme=request.theme,
        status="pending"
    )
    db.add(job)
    db.commit()

    background_tasks.add_task(
        generate_story_task,
        job_id=job_id,
        theme=request.theme,
        session_id=session_id
    )

    return job


def generate_story_task(job_id: str, theme: str, session_id: str):
    """Run the story generation work asynchronously.

    This function updates the StoryJob status over time:
        pending -> processing -> completed/failed

    It is expected to:
        - load the related job record
        - generate the actual story
        - save the generated story
        - update job.story_id and final status

    Response/DB update shape:
        {
            "status": "processing" | "completed" | "failed",
            "completed_at": datetime or null,
            "error": "message or null"
        }
    """
    db = SessionLocal()

    try:
        job = db.query(StoryJob).filter(StoryJob.job_id == job_id).first()

        if not job:
            return

        try:
            job.status = "processing"
            db.commit()


            job.story_id = 1  # todo: update story id
            job.status = "completed"
            job.completed_at = datetime.now()
            db.commit()
        except Exception as e:
            job.status = "failed"
            job.completed_at = datetime.now()
            job.error = str(e)
            db.commit()
    finally:
        db.close()


@router.get("/{story_id}/complete", response_model=CompleteStoryResponse)
def get_complete_story(story_id: int, db: Session = Depends(get_db)):
    """Fetch the complete story including the full narrative tree.

    Path parameter:
        story_id: integer ID of the story

    Response shape:
        {
            "id": 1,
            "title": "The Lost Temple",
            "session_id": "abc-123",
            "created_at": "2026-09-15T12:00:00Z",
            "root_node": {
                "id": 10,
                "content": "You awaken in the ruins...",
                "is_ending": false,
                "is_winning_ending": false,
                "options": [
                    {"text": "Explore the hall", "node_id": 11}
                ]
            },
            "all_nodes": {
                "10": {
                    "id": 10,
                    "content": "...",
                    "is_ending": false,
                    "is_winning_ending": false,
                    "options": [...]
                }
            }
        }
    """
    story = db.query(Story).filter(Story.id == story_id).first()
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")

    complete_story = build_complete_story_tree(db, story)
    return complete_story


def build_complete_story_tree(db: Session, story: Story) -> CompleteStoryResponse:
    """Build the final response model from the story and its related nodes.

    This function gathers all `StoryNode` records associated with a `Story`
    and organizes them into a nested response structure.

    Output:
        A `CompleteStoryResponse` object containing:
        - story metadata
        - root node
        - all nodes dictionary
    """
    nodes = db.query(StoryNode).filter(StoryNode.story_id == story.id).all()

    if not story:
        raise HTTPException(status_code=500, detail="Story root node not found")