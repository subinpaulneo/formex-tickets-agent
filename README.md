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

Run the ingestion script to process your data and load it into the ChromaDB vector database. This step is crucial as it populates the database that the agents rely on.

**Running the Ingestion Script**

The ingestion script, `src/ingest.py`, processes your data and then chunks the documents, generates embeddings, and stores them in the ChromaDB database.

To run the script, use the following command:

```bash
python src/ingest.py
```

**Optional: Ingestion Options**

By default, the ingestion script will process both ticket data from `gorgias_tickets.csv` and knowledge documents from `data/knowledge/`. It will also add new data to the existing collection and use the Gemini API for ticket processing.

You can use the following flags to customize the ingestion behavior:

*   `--clear-db`: Clears the existing database collection before ingesting new data.
*   `--use-local-llm`: Uses a local Gemma model for ticket processing instead of the Gemini API.
*   `--ingest-tickets`: Ingests only ticket data. If this flag is used, knowledge documents will be skipped.
*   `--ingest-knowledge`: Ingests only knowledge base data. If this flag is used, ticket data will be skipped.
*   `--file <path_to_file>`: Ingests only a single, specified knowledge file. This is useful for adding new documents without re-processing the entire knowledge base. When this flag is used, `--ingest-knowledge` is implicitly enabled.

You can use these flags separately or together. For example:

```bash
# Clear the database and ingest only knowledge base data
python src/ingest.py --clear-db --ingest-knowledge

# Ingest only ticket data using the local LLM
python src/ingest.py --ingest-tickets --use-local-llm

# Ingest a single new knowledge file
python src/ingest.py --file data/knowledge/macros.md
```

*   **Important**: The first time you run the ingestion script, it is recommended to use the `--clear-db` flag to ensure a clean database.

#### f. Start the FastAPI Backend

Once data ingestion is complete, you can start the FastAPI application. You have two options:

**Option 1: Use the Gemini API (Default)**

This option uses the Google Gemini API for the agentic tasks. Make sure you have your `GEMINI_API_KEY` set in your `.env` file.

```bash
python src/api.py
```

**Option 2: Use a Local LLM (Gemma)**

This option uses a local Gemma model for the agentic tasks. This is useful for offline development or to avoid hitting API rate limits.

```bash
python src/api.py --use-local-llm
```

*   **Important**: The first time you run this command, it will download the Gemma model from Hugging Face, which may take a few minutes.

By default, the application will run on `http://localhost:8000`. The `--reload` flag is useful for development, as it restarts the server automatically on code changes. If you want to use it, you can run `uvicorn src.api:app --reload --host 0.0.0.0 --port 8000`.

#### g. Authenticate with Hugging Face

To use the local Gemma model, you need to authenticate with a Hugging Face API token. This is because the Gemma models are "gated" and require you to agree to the terms of use.

1.  **Request Access to the Model:**
    *   Go to the Hugging Face model page for `google/gemma-3-270m-it`: [https://huggingface.co/google/gemma-3-270m-it](https://huggingface.co/google/gemma-3-270m-it)
    *   Click on the "Access repository" button. You will need to be logged in to your Hugging Face account.
    *   You will be asked to agree to the terms of use. Once you agree, you will be granted access to the model.

2.  **Authenticate Your Environment:**
    *   Once you have been granted access to the model, you need to authenticate your environment with a Hugging Face API token.
    *   You can find your Hugging Face API token in your Hugging Face account settings: [https://huggingface.co/settings/tokens](https://huggingface.co/settings/tokens)
    *   There are two ways to authenticate:
        *   **Using the Hugging Face CLI:**
            ```bash
            huggingface-cli login
            ```
            This will prompt you to enter your Hugging Face API token.
        *   **Setting an environment variable:**
            You can set the `HUGGING_FACE_HUB_TOKEN` environment variable to your Hugging Face API token. You can add this to your `.env` file:
            ```
            HUGGING_FACE_HUB_TOKEN=YOUR_HUGGING_FACE_API_TOKEN
            ```

Once you have authenticated, you will be able to download and use the local Gemma model.

Once data ingestion is complete, you can start the FastAPI application. You have two options:

**Option 1: Use the Gemini API (Default)**

This option uses the Google Gemini API for the agentic tasks. Make sure you have your `GEMINI_API_KEY` set in your `.env` file.

```bash
python src/api.py
```

**Option 2: Use a Local LLM (Gemma)**

This option uses a local Gemma model for the agentic tasks. This is useful for offline development or to avoid hitting API rate limits.

```bash
python src/api.py --use-local-llm
```

*   **Important**: The first time you run this command, it will download the Gemma model from Hugging Face, which may take a few minutes.

By default, the application will run on `http://localhost:8000`. The `--reload` flag is useful for development, as it restarts the server automatically on code changes. If you want to use it, you can run `uvicorn src.api:app --reload --host 0.0.0.0 --port 8000`.

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

Once the image is built, you can run the container. You have two options:

**Option 1: Use the Gemini API (Default)**

This option runs the application with the Gemini API for the agentic tasks.

```bash
docker run -p 8000:8000 agentic-rag-system
```

**Option 2: Use a Local LLM (Gemma)**

This option runs the application with the local Gemma model for the agentic tasks.

```bash
docker run -p 8000:8000 agentic-rag-system python src/api.py --use-local-llm
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
