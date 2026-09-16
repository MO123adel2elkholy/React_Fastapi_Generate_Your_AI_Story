"""Story API routes.

This module defines the REST endpoints used to:
- create a new story-generation job from a user theme
- run background AI generation for a choose-your-own-adventure story
- fetch the complete story tree after generation finishes
- return the final structure in a frontend-friendly response format

The routes connect the client-facing API to the database models and the AI
story generation engine. They also manage session persistence through cookies
so the frontend can associate a story with the correct user session.

Responsibilities:
- validate incoming story creation requests
- persist a job record with status tracking
- schedule background generation work
- fetch finished story records from the database
- build nested story data for the frontend response payload
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
    CompleteStoryResponse,
    CompleteStoryNodeResponse,
    CreateStoryRequest,
)
from schemas.job import StoryJobResponse
from core.story_generator import StoryGenerator

router = APIRouter(
    prefix="/stories",
    tags=["stories"],
)


def get_session_id(session_id: Optional[str] = Cookie(None)):
    """Return the existing session ID or create a new one.

    This helper reads the browser cookie named `session_id`. If the client has
    already generated a session, we reuse it. Otherwise, a new UUID is created
    and returned so the story can be tracked against that user session.

    Args:
        session_id: Optional session identifier from the request cookie.

    Returns:
        str: A valid session ID used to associate the story with the user.
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
    db: Session = Depends(get_db),
):
    """Create a story-generation job and schedule background AI work.

    This endpoint receives a story theme from the client, creates a `StoryJob`
    database record, and starts asynchronous generation in the background.

    Request body example:
        {
            "theme": "A fantasy adventure in a hidden temple"
        }

    Response example:
        {
            "job_id": "8ce8aa2f-2d2d-4d7a-b7f8-c440f4ba0c29",
            "status": "pending",
            "story_id": null,
            "error": null,
            "created_at": "2026-09-16T12:00:00Z",
            "completed_at": null
        }

    Args:
        request: The user-submitted story generation request.
        background_tasks: FastAPI BackgroundTasks used to run async generation.
        response: HTTP response object used to set cookies.
        session_id: Current user's session ID.
        db: Database session dependency.

    Returns:
        StoryJob: The newly created job object in the database.
    """
    # Store session ID in a cookie so the client can send it back later.
    response.set_cookie(key="session_id", value=session_id, httponly=True)

    # Create a unique job identifier for tracking this generation task.
    job_id = str(uuid.uuid4())

    # Create a database record for the pending story job.
    job = StoryJob(
        job_id=job_id,
        session_id=session_id,
        theme=request.theme,
        status="pending",
    )
    db.add(job)
    db.commit()

    # Schedule the real generation work in the background so the API returns fast.
    background_tasks.add_task(
        generate_story_task,
        job_id=job_id,
        theme=request.theme,
        session_id=session_id,
    )

    return job


def generate_story_task(job_id: str, theme: str, session_id: str):
    """Run the actual AI story generation in the background.

    This function loads the matching `StoryJob`, marks it as processing, calls
    the `StoryGenerator`, and then updates the job with:
    - the generated story ID
    - final state: completed or failed
    - completion timestamp
    - any error message if generation failed

    Args:
        job_id: Unique identifier for the task being processed.
        theme: Story prompt provided by the user.
        session_id: Current session identifier associated with the user.
    """
    db = SessionLocal()

    try:
        # Find the job record to update.
        job = db.query(StoryJob).filter(StoryJob.job_id == job_id).first()

        if not job:
            return

        try:
            # Mark the task as started.
            job.status = "processing"
            db.commit()

            # Generate the actual story using the AI engine.
            story = StoryGenerator.generate_story(db, session_id, theme)

            # Link the created story to the job record.
            job.story_id = story.id
            job.status = "completed"
            job.completed_at = datetime.now()
            db.commit()

        except Exception as e:
            # Save failure metadata so the frontend can show the issue.
            job.status = "failed"
            job.completed_at = datetime.now()
            job.error = str(e)
            db.commit()

    finally:
        db.close()


@router.get("/{story_id}/complete", response_model=CompleteStoryResponse)
def get_complete_story(story_id: int, db: Session = Depends(get_db)):
    """Fetch the full generated story and its nested narrative tree.

    This endpoint returns the final story payload for the frontend. It includes:
    - story metadata
    - the root node
    - all story nodes in a dictionary keyed by node id

    Args:
        story_id: Integer ID of the generated story.
        db: Database session dependency.

    Returns:
        CompleteStoryResponse: Full story payload for the frontend.

    Raises:
        HTTPException: 404 if the story does not exist.
    """
    story = db.query(Story).filter(Story.id == story_id).first()

    if not story:
        raise HTTPException(status_code=404, detail="Story not found")

    complete_story = build_complete_story_tree(db, story)
    return complete_story


def build_complete_story_tree(db: Session, story: Story) -> CompleteStoryResponse:
    """Build the final frontend response from the stored story records.

    This function:
    - loads all `StoryNode` rows for the given story
    - converts each node to a `CompleteStoryNodeResponse`
    - identifies the root node
    - returns the final story object in a shape expected by the frontend

    Args:
        db: Database session used to query story nodes.
        story: Parent `Story` object to build the response for.

    Returns:
        CompleteStoryResponse: Structured story payload with nested node data.

    Raises:
        HTTPException: 500 if a root node cannot be found.
    """
    nodes = db.query(StoryNode).filter(StoryNode.story_id == story.id).all()

    node_dict = {}

    # Convert every stored node into the API response schema.
    for node in nodes:
        node_response = CompleteStoryNodeResponse(
            id=node.id,
            content=node.content,
            is_ending=node.is_ending,
            is_winning_ending=node.is_winning_ending,
            options=node.options,
        )
        node_dict[node.id] = node_response

    # Find the root node from the story tree.
    root_node = next((node for node in nodes if node.is_root), None)

    if not root_node:
        raise HTTPException(status_code=500, detail="Story root node not found")

    return CompleteStoryResponse(
        id=story.id,
        title=story.title,
        session_id=story.session_id,
        created_at=story.created_at,
        root_node=node_dict[root_node.id],
        all_nodes=node_dict,
    )