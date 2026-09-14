"""Story data models.

This module defines the database schema used to store a generated
Choose-Your-Own-Adventure story and its branching narrative nodes.

A Story is the parent record for a single session/story run, and each
StoryNode represents one narrative point in the story tree.
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from db.database import Base


class Story(Base):
    """Represents a complete story generated for a user session.

    Attributes:
        id: Primary key
        title: Human-readable story title
        session_id: Unique session identifier for tracking the story
        created_at: Timestamp when the story was created
        nodes: Related story nodes that belong to this story
    """

    __tablename__ = "stories"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    session_id = Column(String, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Each story can contain many narrative nodes, such as scenes or choices.
    nodes = relationship("StoryNode", back_populates="story")


class StoryNode(Base):
    """Represents a single scene or decision point inside a story.

    Each node stores the content shown to the user and metadata describing
    whether it is a root node, an ending, or a winning ending.
    """

    __tablename__ = "story_nodes"

    id = Column(Integer, primary_key=True, index=True)
    story_id = Column(Integer, ForeignKey("stories.id"), index=True)
    content = Column(String)
    is_root = Column(Boolean, default=False)
    is_ending = Column(Boolean, default=False)
    is_winning_ending = Column(Boolean, default=False)

    # JSON column storing possible choices from this node, e.g.:
    # [{"label": "Continue", "next_node_id": 2}, ...]
    options = Column(JSON, default=list)

    # Many-to-one relationship back to the parent story.
    story = relationship("Story", back_populates="nodes")