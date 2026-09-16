"""LLM response models for generated story data.

This module defines the Pydantic schema used to validate the JSON returned by the
language model when generating a choose-your-own-adventure story.

The AI is expected to return a story object with:
- a title
- a rootNode
- nested child nodes
- multiple choices
- ending markers for winning and non-winning endings

These models act as the bridge between raw LLM output and the backend logic that
stores the story in the database.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class StoryOptionLLM(BaseModel):
    """Represents a single choice from a story node.

    Attributes:
        text: The label shown to the user for this option.
        nextNode: The next narrative node reached when the user chooses this option.
    """

    text: str = Field(description="the text of the option shown to the user")
    nextNode: Dict[str, Any] = Field(
        description="the next node content and its options"
    )


class StoryNodeLLM(BaseModel):
    """Represents a single narrative node in the generated story tree.

    Each story node contains story content and may either:
    - continue to more nodes
    - end the story
    - end with a winning outcome
    """

    content: str = Field(description="The main content of the story node")
    isEnding: bool = Field(description="Whether this node is an ending node")
    isWinningEnding: bool = Field(
        description="Whether this node is a winning ending node"
    )
    options: Optional[List[StoryOptionLLM]] = Field(
        default=None,
        description="The options for this node"
    )


class StoryLLMResponse(BaseModel):
    """Top-level schema for a generated story returned by the LLM.

    Attributes:
        title: The title of the generated story.
        rootNode: The starting node from which the user begins the adventure.
    """

    title: str = Field(description="The title of the story")
    rootNode: StoryNodeLLM = Field(description="The root node of the story")