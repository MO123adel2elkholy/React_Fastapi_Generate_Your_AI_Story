"""Story generation engine for AI-driven branching narratives.

This module is responsible for converting a user theme into a full
Choose-Your-Own-Adventure story using an LLM. It:
- selects the correct OpenAI model configuration
- sends a prompt and output parser to the language model
- validates the returned JSON against the `StoryLLMResponse` schema
- converts the nested story tree into SQLAlchemy `Story` and `StoryNode` records
- persists the generated story into the database

The generation process follows this pattern:
1. Build a prompt using the story template and user theme.
2. Invoke the LLM with structured output parsing.
3. Validate the AI response according to the schema.
4. Create the parent `Story` record.
5. Recursively convert each node into a `StoryNode` row.
6. Store choice metadata (`text` + `next_node_id`) in the `options` JSON field.
7. Commit the database transaction.

This file acts as the bridge between:
- raw AI-generated content
- validated application schema
- database storage model
"""

from sqlalchemy.orm import Session

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser

from core.prompets import STORY_PROMPT
from models.story import Story, StoryNode
from core.models import StoryLLMResponse, StoryNodeLLM
from dotenv import load_dotenv
import os

load_dotenv()


class StoryGenerator:
    """Generate and persist a branching story from a user prompt.

    This class encapsulates the logic needed to:
    - initialize the LLM
    - generate a story from a theme
    - parse the LLM output into structured Python objects
    - transform the nested tree into SQLAlchemy records
    """

    @classmethod
    def _get_llm(cls):
        """Create and return the configured LLM client.

        The method prefers the environment-based OpenAI configuration if both
        `OPENAI_API_KEY` and `CHOREO_OPENAI_CONNECTION_SERVICEURL` are present.
        Otherwise, it falls back to the default ChatOpenAI configuration.

        Returns:
            ChatOpenAI: An initialized LLM client configured for story generation.
        """
        openai_api_key = os.getenv("OPENAI_API_KEY")
        serviceurl = os.getenv("CHOREO_OPENAI_CONNECTION_SERVICEURL")

        # If the app is configured to use a custom OpenAI-compatible service,
        # prefer that endpoint instead of the default public API endpoint.
        if openai_api_key and serviceurl:
            return ChatOpenAI(
                model="gpt-4o-mini",
                api_key=openai_api_key,
                base_url=serviceurl
            )

        # Default local/public OpenAI setup
        return ChatOpenAI(model="gpt-4o-mini")

    @classmethod
    def generate_story(cls, db: Session, session_id: str, theme: str = "fantasy") -> Story:
        """Generate a complete story and save it to the database.

        Args:
            db: SQLAlchemy database session used to persist the story.
            session_id: Session identifier associated with the story.
            theme: Main story idea or user prompt used to guide the model.

        Returns:a
            Story: The created parent story object persisted in the database.

        Workflow:
            1. Initialize the LLM.
            2. Build a structured prompt.
            3. Invoke the LLM.
            4. Parse the JSON output into the `StoryLLMResponse` schema.
            5. Save the root story record.
            6. Recursively save each story node and branch.
            7. Commit the transaction.
        """
        # Create a language model instance with the correct environment settings
        llm = cls._get_llm()

        # Use Pydantic parser to enforce the JSON structure returned by the LLM
        story_parser = PydanticOutputParser(pydantic_object=StoryLLMResponse)

        # Build chat prompt using the stored template and the user's theme
        prompt = ChatPromptTemplate.from_messages([
            (
                "system",
                STORY_PROMPT
            ),
            (
                "human",
                f"Create the story with this theme: {theme}"
            )
        ]).partial(format_instructions=story_parser.get_format_instructions())

        # Invoke the LLM and get the response
        raw_response = llm.invoke(prompt.invoke({}))

        # Extract the text content in case LangChain returns a message object
        response_text = raw_response
        if hasattr(raw_response, "content"):
            response_text = raw_response.content

        # Parse string content into the validated Pydantic model
        story_structure = story_parser.parse(response_text)

        # Create the parent Story row
        story_db = Story(title=story_structure.title, session_id=session_id)
        db.add(story_db)
        db.flush()  # ensure the story gets an id before creating related nodes

        # Get the root node from the parsed AI response
        root_node_data = story_structure.rootNode

        # In case the parser gives a dict instead of a model object, validate it
        if isinstance(root_node_data, dict):
            root_node_data = StoryNodeLLM.model_validate(root_node_data)

        # Recursively process the whole story tree starting from the root node
        cls._process_story_node(db, story_db.id, root_node_data, is_root=True)

        db.commit()
        return story_db

    @classmethod
    def _process_story_node(
        cls,
        db: Session,
        story_id: int,
        node_data: StoryNodeLLM,
        is_root: bool = False
    ) -> StoryNode:
        """Convert one AI story node into a persisted `StoryNode` record.

        Args:
            db: SQLAlchemy session to write into.
            story_id: Parent story id.
            node_data: The parsed node object from the LLM schema.
            is_root: True if this is the starting node of the story.

        Returns:
            StoryNode: The persisted database row for this story node.

        The method:
        - creates a `StoryNode` record
        - stores content and ending flags
        - recursively creates child nodes for each option
        - writes option choices as a JSON list containing:
          {"text": "...", "node_id": <child_id>}
        """
        # Extract content safely from either a Pydantic model or raw dict
        content = node_data.content if hasattr(node_data, "content") else node_data["content"]

        # Extract boolean flags safely
        is_ending = node_data.isEnding if hasattr(node_data, "isEnding") else node_data["isEnding"]
        is_winning_ending = (
            node_data.isWinningEnding
            if hasattr(node_data, "isWinningEnding")
            else node_data["isWinningEnding"]
        )

        # Create the StoryNode database row
        node = StoryNode(
            story_id=story_id,
            content=content,
            is_root=is_root,
            is_ending=is_ending,
            is_winning_ending=is_winning_ending,
            options=[]
        )
        db.add(node)
        db.flush()  # assign the node id before linking child options

        # If this node is an ending, there are no further branches to process
        if not node.is_ending and (hasattr(node_data, "options") and node_data.options):
            options_list = []

            # Each option contains a label + the nested next node
            for option_data in node_data.options:
                next_node = option_data.nextNode

                # Validate nested node dicts into the schema before recursion
                if isinstance(next_node, dict):
                    next_node = StoryNodeLLM.model_validate(next_node)

                # Recursively save the child node
                child_node = cls._process_story_node(db, story_id, next_node, False)

                # Store a lightweight JSON structure for frontend choices
                options_list.append({
                    "text": option_data.text,
                    "node_id": child_node.id
                })

            # Save the list of choices in the JSON field on the current node
            node.options = options_list

        db.flush()
        return node