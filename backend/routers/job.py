"""Job status API routes.

This module exposes endpoints for retrieving the status of story generation jobs.
It connects the frontend with the database-backed `StoryJob` model and returns
the serialized status payload expected by the client.

The main responsibility is to provide:
- a way to query job details by job_id
- validation for missing jobs
- a response schema matching the `StoryJobResponse` model
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from db.database import get_db
from models.job import StoryJob
from schemas.job import StoryJobResponse

router = APIRouter(
    prefix="/jobs",
    tags=["jobs"]
)


@router.get("/{job_id}", response_model=StoryJobResponse)
def get_job_status(job_id: str, db: Session = Depends(get_db)):
    """Get the current status of a generation job.

    Path parameter:
        job_id: unique ID of the background job

    Response shape:
        {
            "job_id": "uuid-string",
            "status": "pending" | "processing" | "completed" | "failed",
            "story_id": 12 or null,
            "error": "message or null",
            "created_at": "2026-09-15T12:00:00Z",
            "completed_at": "2026-09-15T12:05:00Z" or null
        }

    Raises:
        404: if the job does not exist
    """
    job = db.query(StoryJob).filter(StoryJob.job_id == job_id).first()

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return job