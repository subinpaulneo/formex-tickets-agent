
import sys
import os

# Add the project root to the sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import logging
logger = logging.getLogger(__name__)
import chromadb
from src.agents import OrchestratorAgent
from fastapi import FastAPI, Response
from fastapi.responses import FileResponse
from pydantic import BaseModel
from src.agents import OrchestratorAgent
import uvicorn
from starlette.middleware.cors import CORSMiddleware
from starlette.background import BackgroundTask
import os
import tempfile
import argparse

USE_LOCAL_LLM = False # Global variable to control local LLM usage

from contextlib import asynccontextmanager

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Initializes the ChromaDB client and the ticket processing orchestrator.
    This function is called when the FastAPI application starts up.
    """
    logger.info("ChromaDB client initializing...")
    # Initialize ChromaDB client
    db_client = chromadb.PersistentClient(path="vector_db")
    logger.info("ChromaDB client initialized.")

    # Initialize the orchestrator
    global orchestrator
    orchestrator = OrchestratorAgent(use_local_llm=USE_LOCAL_LLM) # Use OrchestratorAgent
    logger.info("Orchestrator initialized.")
    yield
    # Shutdown logic (if any)
    logger.info("Application shutting down.")

from starlette.staticfiles import StaticFiles

# Initialize the FastAPI app
app = FastAPI(
    title="Agentic RAG System API",
    description="An API for interacting with a multi-agent RAG system for customer support.",
    version="1.0.0",
    lifespan=lifespan
)

# Mount static files directory
app.mount("/manuals", StaticFiles(directory="output"), name="manuals")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow requests from your frontend origin
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods (GET, POST, etc.)
    allow_headers=["*"],  # Allow all headers
)

# Define the request body model for type checking
class PromptRequest(BaseModel):
    prompt: str

@app.get("/", tags=["Health Check"])
async def read_root():
    """A simple endpoint to check if the API is running."""
    return {"status": "online"}

@app.post("/handle-request", tags=["Agent Interaction"])
async def handle_request(request: PromptRequest):
    """
    Receives a user prompt and returns the agent system's response.
    """
    response = orchestrator.handle_request(user_prompt=request.prompt)

    if request.prompt.strip().lower() == "generate all manuals":
        output_dir = "output"
        os.makedirs(output_dir, exist_ok=True)
        file_path = os.path.join(output_dir, "Formex_Generated_Manual.md")
        with open(file_path, "w", encoding='utf-8') as f:
            f.write(response)

        return {"download_link": "/manuals/Formex_Generated_Manual.md"}

    return {"response": response}

# To run this API, use the command:
# uvicorn src.api:app --reload

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Agentic RAG System API")
    parser.add_argument("--use-local-llm", action="store_true", help="Use the local LLM instead of the Gemini API.")
    args = parser.parse_args()
    USE_LOCAL_LLM = args.use_local_llm

    # Orchestrator and DB client are initialized in startup_event

    uvicorn.run("src.api:app", host="0.0.0.0", port=8000, reload=True)
