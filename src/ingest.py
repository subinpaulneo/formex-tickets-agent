import sys
import os
import pandas as pd
import glob
from itertools import chain
import time
import argparse

# Add the project root to sys.path for module discovery
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.db_utils import get_db_collection, clear_db_collection
from src.ticket_processor_agent import TicketProcessorAgent

# --- Constants ---
CSV_PATH = os.path.join(os.path.dirname(__file__), '..', 'gorgias_tickets.csv')
KNOWLEDGE_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'knowledge')
CHUNK_SIZE_ROWS = 1000  # Number of rows to read from CSV at a time
CHUNK_SIZE_CHARS = 1000 # Target size of each text chunk in characters
CHUNK_OVERLAP = 200   # Number of characters to overlap between chunks
DB_BATCH_SIZE = 100   # Number of items to batch before upserting to ChromaDB

# --- Document Processing Functions ---

def process_ticket_group(group, ticket_processor_agent):
    """Processes a group of messages for a single ticket into one document."""
    group = group.sort_values(by='sent_datetime')
    conversation = []
    for _, row in group.iterrows():
        sender = (row.get('sender') or 'N/A')
        body = (row.get('body') or 'N/A')
        conversation.append(f"From: {sender}\nDate: {row.get('sent_datetime')}\n\n{body}\n")
    
    full_conversation = "---\
".join(conversation)
    ticket_data = group.iloc[-1]

    # Process the ticket conversation with the TicketProcessorAgent
    processed_ticket_data = ticket_processor_agent.process_ticket(full_conversation)

    if processed_ticket_data is None:
        print(f"Skipping ticket {int(ticket_data['ticket_id'])} due to processing error.")
        return None

    # Prepare metadata, merging original with processed data
    metadata = {
        "ticket_id": int(ticket_data['ticket_id']),
        "subject": str(ticket_data['subject']),
        "channel": str(ticket_data['channel']),
        "status": "closed",
        "source": os.path.basename(CSV_PATH),
        **processed_ticket_data # Merge extracted data
    }

    return {
        "id": f"ticket_{int(ticket_data['ticket_id'])}",
        "text": full_conversation,
        "metadata": metadata
    }

def process_tickets_in_chunks(ticket_processor_agent):
    """Reads the ticket CSV in chunks and yields processed ticket documents."""
    print("Processing tickets from CSV...")
    try:
        csv_iterator = pd.read_csv(CSV_PATH, chunksize=CHUNK_SIZE_ROWS, iterator=True)
        processed_tickets = 0
        for chunk in csv_iterator:
            closed_tickets_chunk = chunk[chunk['status'] == 'closed'].copy()
            if closed_tickets_chunk.empty:
                continue
            for _, group in closed_tickets_chunk.groupby('ticket_id'):
                processed_group = process_ticket_group(group, ticket_processor_agent)
                if processed_group:
                    yield processed_group
                    processed_tickets += 1
                time.sleep(1) # Add a 1-second delay to avoid hitting rate limits
        print(f"  - Found and processed {processed_tickets} closed tickets.")
    except FileNotFoundError:
        print(f"Error: The file was not found at {CSV_PATH}")
        return

def process_knowledge_files(specific_file=None):
    """Scans the knowledge directory or a specific file and yields documents."""
    print("\nProcessing knowledge files...")
    
    files_to_process = []
    if specific_file:
        if os.path.exists(specific_file):
            files_to_process.append(specific_file)
            print(f"Processing specific file: {specific_file}")
        else:
            print(f"Error: The file was not found at {specific_file}")
            return
    else:
        print("Scanning knowledge directory for .txt and .md files...")
        path_pattern = os.path.join(KNOWLEDGE_PATH, '**')
        files_to_process = glob.glob(os.path.join(path_pattern, '*.txt'), recursive=True) + \
                         glob.glob(os.path.join(path_pattern, '*.md'), recursive=True)

    for file_path in files_to_process:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            file_name = os.path.basename(file_path)
            yield {
                "id": f"knowledge_{file_name}",
                "text": content,
                "metadata": {"source": file_name, "type": "knowledge"}
            }
            print(f"  - Processed {file_name}")
        except Exception as e:
            print(f"Error processing file {file_path}: {e}")


def chunk_document(doc):
    """Splits a document's text into overlapping chunks."""
    text = doc['text']
    if not text or not isinstance(text, str):
        return
    start = 0
    chunk_num = 0
    while start < len(text):
        end = start + CHUNK_SIZE_CHARS
        chunk_text = text[start:end]
        yield {
            "id": f"{doc['id']}_chunk_{chunk_num}",
            "text": chunk_text,
            "metadata": doc['metadata']
        }
        start += CHUNK_SIZE_CHARS - CHUNK_OVERLAP
        chunk_num += 1

# --- Main Execution Logic ---
def main():
    """
    Main function to orchestrate the full ETL pipeline:
    Extract -> Transform (process, group, chunk) -> Load (embed, store).
    """
    parser = argparse.ArgumentParser(description="Data ingestion pipeline for the Agentic RAG System.")
    parser.add_argument("--clear-db", action="store_true", help="Clear the existing database collection before ingesting new data.")
    parser.add_argument("--use-local-llm", action="store_true", help="Use the local LLM for ticket processing instead of the Gemini API.")
    parser.add_argument("--ingest-tickets", action="store_true", help="Ingest only ticket data.")
    parser.add_argument("--ingest-knowledge", action="store_true", help="Ingest only knowledge base data.")
    parser.add_argument("--file", type=str, default=None, help="Path to a specific knowledge file to ingest. Overrides the default behavior of scanning the whole knowledge directory.")
    args = parser.parse_args()

    print("Starting data ingestion pipeline...")
    if args.clear_db:
        clear_db_collection()
    
    collection = get_db_collection()
    ticket_processor_agent = TicketProcessorAgent(use_local_llm=args.use_local_llm) # Instantiate the agent

    # E+T: Create a single generator for all documents, then chunk them
    # Determine what to ingest based on arguments
    ingest_tickets = args.ingest_tickets
    ingest_knowledge = args.ingest_knowledge

    # If a specific file is provided, ensure knowledge ingestion is enabled
    if args.file:
        ingest_knowledge = True

    # If neither is specified, ingest both by default
    if not ingest_tickets and not ingest_knowledge:
        ingest_tickets = True
        ingest_knowledge = True

    all_docs_generators = []
    if ingest_tickets:
        print("Ingesting ticket data...")
        all_docs_generators.append(process_tickets_in_chunks(ticket_processor_agent))
    if ingest_knowledge:
        print("Ingesting knowledge base data...")
        all_docs_generators.append(process_knowledge_files(specific_file=args.file))

    if not all_docs_generators:
        print("No data type selected for ingestion. Please specify --ingest-tickets or --ingest-knowledge.")
        return

    all_docs = chain(*all_docs_generators)
    chunked_docs = (chunk for doc in all_docs for chunk in chunk_document(doc))

    # L: Load into ChromaDB in batches
    batch = []
    total_chunks_loaded = 0
    print("\nEmbedding and loading documents into the vector database...")
    for chunk in chunked_docs:
        batch.append(chunk)
        if len(batch) >= DB_BATCH_SIZE:
            ids = [item['id'] for item in batch]
            documents = [item['text'] for item in batch]
            metadatas = [item['metadata'] for item in batch]
            collection.upsert(ids=ids, documents=documents, metadatas=metadatas)
            total_chunks_loaded += len(batch)
            print(f"  - Upserted batch of {len(batch)}. Total chunks loaded: {total_chunks_loaded}")
            batch = []
    
    # Upsert any remaining items in the last batch
    if batch:
        ids = [item['id'] for item in batch]
        documents = [item['text'] for item in batch]
        metadatas = [item['metadata'] for item in batch]
        collection.upsert(ids=ids, documents=documents, metadatas=metadatas)
        total_chunks_loaded += len(batch)
        print(f"  - Upserted final batch of {len(batch)}. Total chunks loaded: {total_chunks_loaded}")

    print(f"\nData ingestion complete. Total items in collection: {collection.count()}")

if __name__ == "__main__":
    main()