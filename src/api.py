
from fastapi import FastAPI
from pydantic import BaseModel
from src.agents import OrchestratorAgent
import uvicorn
from starlette.middleware.cors import CORSMiddleware # Import CORSMiddleware

# Initialize the FastAPI app
app = FastAPI(
    title="Agentic RAG System API",
    description="An API for interacting with a multi-agent RAG system for customer support.",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Allow requests from your frontend origin
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods (GET, POST, etc.)
    allow_headers=["*"],  # Allow all headers
)

# Load the OrchestratorAgent once at startup
# This is efficient as the models and DB connections are initialized only once.
print("Initializing OrchestratorAgent...")
orchestrator = OrchestratorAgent()
print("Initialization complete. API is ready.")

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
    return {"response": response}

# To run this API, use the command:
# uvicorn src.api:app --reload

if __name__ == "__main__":
    # This allows running the app directly for development
    # The --reload flag automatically restarts the server when code changes
    uvicorn.run("src.api:app", host="0.0.0.0", port=8000, reload=True)
