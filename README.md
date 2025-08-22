# Agentic RAG System for Customer Support

## Overview

This project implements an intelligent, multi-agent system designed to assist customer support teams. It leverages Retrieval Augmented Generation (RAG) to analyze customer support tickets and business documents, generate knowledge base articles, and provide a foundation for future real-time agent assistance. The system features an intuitive web-based chat interface for easy interaction.

## Features

*   **Automated Data Ingestion**: Processes customer tickets and knowledge documents, extracting key information and categorizing them automatically.
*   **Intelligent Ticket Analysis**: Summarizes specific customer tickets, providing insights into customer queries, agent actions, and resolutions.
*   **Automated Knowledge Base Generation**: Synthesizes information from across your dataset to create structured, categorized user manuals or guides for various topics.
*   **Multi-Agent Orchestration**: An intelligent orchestrator agent routes user requests to specialized agents for efficient task handling.
*   **Web-based User Interface**: A user-friendly chat interface built with React for seamless interaction with the AI system.
*   **Scalable Backend**: Powered by FastAPI, providing a robust and deployable API for the agentic system.

## Core Technologies

*   **Agent Framework**: `smol-agents` (for multi-agent orchestration)
*   **Language Model (LLM)**: An open-source model from Hugging Face (e.g., Mistral-7B-Instruct-v0.2) via Hugging Face Inference API.
*   **Vector Database**: ChromaDB (for efficient storage and retrieval of document embeddings)
*   **Backend API**: FastAPI (Python)
*   **Frontend UI**: React (JavaScript) with Vite

## Setup (Local Development)

To get the project running on your local machine, follow these steps:

### Prerequisites

*   **Python 3.9+**: [Download Python](https://www.python.org/downloads/)
*   **Node.js & npm**: [Download Node.js](https://nodejs.org/en/download/) (npm is included)
*   **Docker Desktop**: [Download Docker Desktop](https://www.docker.com/products/docker-desktop/) (for deployment)

### 1. Clone the Repository

First, clone the project repository to your local machine:

```bash
git clone <repository_url>
cd <repository_directory>
```

### 2. Backend Setup (Python)

This sets up the FastAPI application and the data ingestion pipeline.

#### a. Create and Activate Virtual Environment

It's highly recommended to use a virtual environment to manage Python dependencies:

```bash
python3 -m venv venv
source venv/bin/activate  # On macOS/Linux
# .\venv\Scripts\activate  # On Windows
```

#### b. Install Python Dependencies

Install all required Python libraries:

```bash
pip install -r requirements.txt
```

#### c. Set Up Environment Variables

Create a file named `.env` in the root directory of the project (where `requirements.txt` is located). Add your Google Gemini API Key to this file:

```
GEMINI_API_KEY=YOUR_GEMINI_API_KEY
```

*   You can get a Gemini API key from [Google AI Studio](https://aistudio.google.com/app/apikey).

#### d. Prepare Your Data

*   **Gorgias Tickets**:
    *   If you have a large dump of Gorgias tickets (e.g., `gorgias_tickets_dump.csv`), you can use the `gorgias_batch_fetch.py` script to extract a manageable batch of closed tickets. This script supports resuming from where it left off.
    *   Place your large CSV dump (e.g., `gorgias_tickets_dump.csv`) in the project root.
    *   Run the batch fetch script:
        ```bash
        python gorgias_batch_fetch.py
        ```
    *   This will create (or append to) `gorgias_tickets.csv` with the first 500 closed tickets. You can run it multiple times to process more batches.
*   **Knowledge Documents**: Create a directory `data/knowledge/` in the project root. Place any supplementary knowledge documents (e.g., FAQs, return policies) as `.txt` or `.md` files within this directory.

#### e. Ingest Your Data

Run the ingestion script to process your data and load it into the ChromaDB vector database. This step will also automatically categorize your tickets using an LLM.

```bash
python src/ingest.py
```

*   **Important**: This step must be completed successfully before starting the backend API, as the agents rely on the populated database.

#### f. Start the FastAPI Backend

Once data ingestion is complete, start the FastAPI application:

```bash
uvicorn src.api:app --reload --host 0.0.0.0 --port 8000
```

*   The `--reload` flag is useful for development, as it restarts the server automatically on code changes.

### 3. Frontend Setup (React)

This sets up the web-based chat interface.

#### a. Navigate to the Frontend Directory

```bash
cd frontend
```

#### b. Install Node.js Dependencies

```bash
npm install
```

#### c. Start the React Development Server

```bash
npm run dev
```

### 4. Access the User Interface

After both the backend and frontend servers are running, open your web browser and navigate to the address provided by the `npm run dev` command (usually `http://localhost:5173/`).

## Usage

Interact with the AI system through the chat interface. Here are some example prompts:

*   **Summarize a specific ticket**: `Can you summarize ticket 12345 for me?`
*   **Generate a manual section for a topic**: `Write a manual section for warranty claims.`
*   **Generate manuals for all categories**: `Generate all manuals.`

## Deployment

The project can be easily deployed using Docker.

### Deployment Requirements

*   **Docker Desktop**: Ensure Docker Desktop is installed and running on your system.

### 1. Build the Docker Image

Navigate back to the project root directory (where the `Dockerfile` is located) and build the Docker image:

```bash
docker build -t agentic-rag-system .
```

### 2. Run the Docker Container

Once the image is built, run the container. This will expose the FastAPI application on port 8000 of your host machine:

```bash
docker run -p 8000:8000 agentic-rag-system
```

*   The backend API will now be accessible at `http://localhost:8000`.

### 3. Test the API Endpoint (Optional)

With the Docker container running, you can test the `/handle-request` API endpoint using `curl`:

```bash
curl -X POST http://localhost:8000/handle-request -H "Content-Type: application/json" -d '{"prompt": "What is the return policy?"}'
```

Expected response (example):

```json
{"response":"The return policy states that..."}
```

## Project Structure

*   `.env`: Environment variables (e.g., API keys).
*   `gorgias_tickets.csv`: Your raw customer support ticket data.
*   `data/knowledge/`: Directory for supplementary knowledge documents.
*   `src/`: Contains the core Python backend logic.
    *   `src/api.py`: FastAPI application entry point.
    *   `src/agents.py`: Defines the multi-agent system (Orchestrator, TicketAnalysis, KnowledgeWriter).
    *   `src/db_utils.py`: Utilities for ChromaDB interaction.
    *   `src/ingest.py`: Script for data ingestion into ChromaDB.
    *   `src/llm_utils.py`: Utilities for LLM interaction.
    *   `src/ticket_processor_agent.py`: Agent for structured ticket data extraction and categorization.
*   `frontend/`: Contains the React web interface.
*   `vector_db/`: Directory where ChromaDB stores its data persistently.
*   `requirements.txt`: Python dependencies.
*   `Dockerfile`: Instructions for building the Docker image.

## Contributing

Contributions are welcome! Please feel free to open issues or submit pull requests.

## License

This project is licensed under the MIT License.
