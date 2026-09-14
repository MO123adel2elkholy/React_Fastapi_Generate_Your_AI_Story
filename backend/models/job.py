"""Job tracking models for asynchronous story generation.

This module stores metadata about background tasks used to generate
stories. It helps track the status of each generation job, the related
session, and any error that may occur during processing.
"""

from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func

from db.database import Base


class StoryJob(Base):
    """Tracks the execution state of a background story generation job.

    Attributes:
        id: Primary key
        job_id: Unique identifier for the Celery/async job
        session_id: ID of the user session that triggered the generation
        theme: Story theme or prompt provided by the user
        status: Current job state such as pending, running, success, or failed
        story_id: Related generated story ID if the job completed successfully
        error: Error message if the job failed
        created_at: Time the job record was created
        completed_at: Time the job completed, if applicable
    """

    __tablename__ = "story_jobs"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(String, index=True, unique=True)
    session_id = Column(String, index=True)
    theme = Column(String)
    status = Column(String)
    story_id = Column(Integer, nullable=True)
    error = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)