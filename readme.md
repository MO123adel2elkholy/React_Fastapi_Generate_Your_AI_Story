# Choose Your Own Adventure AI

Choose Your Own Adventure AI is a full-stack project that combines a FastAPI backend, SQLAlchemy models, and an LLM-powered story generation engine to create branching narrative adventures. The backend accepts a user theme, generates a story using AI, stores it in a database, and exposes the complete story tree through API endpoints.

This project is currently in the backend + AI integration phase. The frontend and deployment setup will be completed in the next stage.

## Project Overview

This application allows a user to:
- enter a story theme or prompt
- start a story generation job
- wait while an AI model builds a branching story
- view the final generated story as a tree of narrative nodes and choices
- track job status and completion state

The generated story is represented as:
- a parent `Story` record
- multiple `StoryNode` records
- nested choice metadata stored on each node
- job tracking through `StoryJob`

The system is designed to support:
- asynchronous story creation
- session-based client tracking
- structured AI output validation
- API-driven frontend integration

## Current Status

Completed:
- FastAPI backend structure
- SQLAlchemy database models
- Pydantic schemas for request/response payloads
- AI story generation workflow
- background job processing
- story node and options persistence
- API endpoints for story creation and retrieval

Planned next:
- frontend React application
- user-facing story UI
- deployment configuration
- environment hardening
- production deployment pipeline

## Tech Stack

Backend:
- Python 3.11+
- FastAPI
- SQLAlchemy
- Pydantic
- PostgreSQL / SQLite support (depending on config)
- LangChain + OpenAI-compatible LLM integration

Frontend (next phase):
- React
- Vite or Create React App
- Axios or fetch API
- modern UI for story playback and branching choices

Infrastructure / deployment (next phase):
- Docker
- Nginx or reverse proxy
- cloud deployment (optional)
- environment-based configuration

## Architecture

The project follows a layered architecture:

- `routers/`: API endpoints
- `models/`: database schema
- `schemas/`: request/response validation models
- `core/`: AI prompt templates, story generation logic, LLM schema
- `db/`: database connection and setup
- `main.py` / app entrypoint: FastAPI app bootstrap

Typical data flow:
1. Client sends a story theme to `/stories/create`
2. Backend creates a `StoryJob` entry
3. Background task starts the AI generation process
4. AI model returns a structured story JSON
5. Backend validates it with Pydantic models
6. Story and nodes are stored in the database
7. Frontend fetches the story via `/stories/{story_id}/complete`

## Project Structure

```text
Choose-Your-Own-Adventure-AI-main/
├── React_Fastapi_Generate_Your_AI_Story/
│   ├── backend/
│   │   ├── core/
│   │   │   ├── models.py
│   │   │   ├── prompets.py
│   │   │   └── story_generator.py
│   │   │
│   │   ├── db/
│   │   │   └── database.py
│   │   │
│   │   ├── models/
│   │   │   ├── job.py
│   │   │   └── story.py
│   │   │
│   │   ├── routers/
│   │   │   ├── job.py
│   │   │   └── story.py
│   │   │
│   │   ├── schemas/
│   │   │   ├── job.py
│   │   │   └── story.py
│   │   │
│   │   ├── main.py
│   │   └── requirements.txt
│   │
│   └── frontend/           # planned next phase
│       └── ...
│
├── README.md
├── .env.example
└── .gitignore
```

## Database Models

### Story
Represents a single generated story.

Fields:
- `id`: primary key
- `title`: human-readable story title
- `session_id`: user/session tracking ID
- `created_at`: timestamp when the story was created
- `nodes`: relationship to all story nodes

### StoryNode
Represents a single narrative node or scene.

Fields:
- `id`: primary key
- `story_id`: foreign key to the parent story
- `content`: narrative text for the node
- `is_root`: whether this is the starting node
- `is_ending`: whether this node ends the story
- `is_winning_ending`: whether the ending is a successful result
- `options`: JSON array of choices for the node

### StoryJob
Tracks background processing state.

Fields:
- `id`: primary key
- `job_id`: unique async job ID
- `session_id`: associated user session
- `theme`: story theme prompt
- `status`: pending / processing / completed / failed
- `story_id`: generated story ID if completed
- `error`: any failure detail
- `created_at`: creation timestamp
- `completed_at`: completion timestamp

## API Overview

### 1) Create story generation job

Endpoint:
- `POST /stories/create`

Request body:
```json
{
  "theme": "A fantasy story about a lost kingdom"
}
```

Response:
```json
{
  "job_id": "uuid-string",
  "status": "pending",
  "story_id": null,
  "error": null,
  "created_at": "2026-09-16T12:00:00Z",
  "completed_at": null
}
```

### 2) Check job status

Endpoint:
- `GET /jobs/{job_id}`

Example response:
```json
{
  "job_id": "uuid-string",
  "status": "completed",
  "story_id": 4,
  "error": null,
  "created_at": "2026-09-16T12:00:00Z",
  "completed_at": "2026-09-16T12:02:00Z"
}
```

### 3) Get complete story

Endpoint:
- `GET /stories/{story_id}/complete`

Example response:
```json
{
  "id": 4,
  "title": "The Lost Temple of Dawn",
  "session_id": "session-uuid",
  "created_at": "2026-09-16T12:00:00Z",
  "root_node": {
    "id": 15,
    "content": "You awaken in an abandoned temple...",
    "is_ending": false,
    "is_winning_ending": false,
    "options": [
      {
        "text": "Explore the corridor",
        "node_id": 16
      },
      {
        "text": "Search the altar",
        "node_id": 17
      }
    ]
  },
  "all_nodes": {
    "15": {
      "id": 15,
      "content": "You awaken in an abandoned temple...",
      "is_ending": false,
      "is_winning_ending": false,
      "options": [
        {
          "text": "Explore the corridor",
          "node_id": 16
        }
      ]
    }
  }
}
```

## AI Generation Flow

The AI workflow is designed to convert a simple prompt into a structured story tree.

### Prompting
A template is stored in `core/prompets.py` and used to instruct the LLM to return:
- a valid title
- a root node
- nested narrative branches
- story endings
- winning ending markers
- JSON-only response format

### Validation
The raw LLM output is validated against Pydantic schemas in `core/models.py`.

This prevents malformed output and ensures the app can safely parse:
- story title
- roots and child nodes
- choice labels
- ending flags

### Persistence
The `StoryGenerator` class in `core/story_generator.py`:
- initializes the language model
- builds the prompt
- invokes the model
- parses the result
- creates the parent story row
- recursively stores each branch as a `StoryNode`
- writes choice metadata as JSON
- commits the result

## Required Environment Variables

Create a `.env` file in the backend root or project root depending on your configuration.

Example:

```env
OPENAI_API_KEY=your_openai_key_here
DATABASE_URL=sqlite:///./stories.db
```

Optional:
```env
CHOREO_OPENAI_CONNECTION_SERVICEURL=your_openai_compatible_endpoint
```

If the project uses SQLite, the app can usually run with a local database file. For larger deployments, PostgreSQL is recommended.

## Installation

### 1) Clone the repository

```bash
git clone <repository-url>
cd Choose-Your-Own-Adventure-AI-main
```

### 2) Create a virtual environment

```bash
python -m venv venv
```

On Windows:
```bash
venv\Scripts\activate
```

On macOS/Linux:
```bash
source venv/bin/activate
```

### 3) Install dependencies

```bash
pip install -r requirements.txt
```

If a project-specific backend requirements file is in a subfolder:
```bash
cd React_Fastapi_Generate_Your_AI_Story/backend
pip install -r requirements.txt
```

## Running the Backend

From the backend directory:

```bash
uvicorn main:app --reload
```

If you are using a package entrypoint or module path different from `main.py`, adjust the command accordingly.

Once running, open:
- Swagger UI: `http://localhost:8000/docs`
- Redoc: `http://localhost:8000/redoc`

## Example Workflow

1. Start the backend
2. Open the Swagger docs
3. Call `POST /stories/create` with a story prompt
4. Save the returned `job_id`
5. Poll `GET /jobs/{job_id}`
6. When status is `completed`, call `GET /stories/{story_id}/complete`
7. Render the result in the frontend

## Why This Project Matters

This project demonstrates how to:
- use AI to generate creative content
- validate LLM output with strict schemas
- convert model output into database records
- create branching narratives with choice-based logic
- expose content through a clean API layer
- build a foundation for interactive game/story experiences

It is a strong example of combining:
- generative AI
- backend APIs
- structured data models
- asynchronous processing
- modern web application architecture

## Frontend Roadmap

The next major stage is the frontend.

Planned frontend features:
- story theme input form
- loading state while the AI story is being generated
- polling for job completion
- story display with narrative text
- clickable choices to navigate the story tree
- ending screens and win/loss states
- session-aware story persistence

## Deployment Roadmap

The project will eventually support:
- Docker-based deployment
- production environment variables
- secure secret management
- database migration support
- CI/CD pipeline
- container deployment to cloud or VPS

Recommended production improvements:
- store secrets in environment variables or secret manager
- use PostgreSQL instead of SQLite in production
- enable logging and monitoring
- use HTTPS
- add authentication/authorization if needed
- add error tracking and analytics

## Development Notes

This project is currently built around a clean backend-first workflow.

Important patterns used:
- FastAPI for API exposure
- SQLAlchemy for ORM persistence
- Pydantic for validation and API contracts
- background jobs for AI work
- tree-based story structure for branching narrative design

This is suitable for:
- interactive storytelling apps
- AI-generated game engines
- adaptive narrative experiences
- content generation demos

## License

This project is intended for educational and personal development use unless a separate license file is added.

## Contributing

You are welcome to contribute improvements such as:
- frontend implementation
- deployment setup
- database migrations
- better prompt design
- error handling and retries
- story generation quality improvements

## Summary

This project already includes the core backend logic for:
- story generation
- AI-driven branching narrative creation
- async processing
- structured API contracts
- database persistence
- story retrieval

The next milestone is frontend implementation and deployment preparation.

This README reflects the current backend + AI integration stage and sets the foundation for the next development phase.

## Quick Start

```bash
cd React_Fastapi_Generate_Your_AI_Story/backend
python -m venv venv
source venv/bin/activate   # or venv\Scripts\activate on Windows
pip install -r requirements.txt
cp .env.example .env
# Add your OpenAI key and database config
uvicorn main:app --reload
```

Then visit:
- `http://localhost:8000/docs`
