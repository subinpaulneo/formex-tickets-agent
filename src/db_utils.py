import chromadb
import os
from dotenv import load_dotenv
from chromadb.utils import embedding_functions # Import embedding_functions module

# Load environment variables from .env file
load_dotenv()

# Define the path for the persistent database storage
DB_PATH = "vector_db"
# Define the name of the collection we will use
COLLECTION_NAME = "tickets_and_knowledge"
# Define the embedding model we'll use for embeddings (Gemini Embedding)
EMBEDDING_MODEL = "models/embedding-001" # This is the model name for Gemini embeddings

def get_db_collection():
    """
    Initializes a persistent ChromaDB client, configures the embedding model,
    and returns the specified collection.
    """
    # Define the embedding function using the specified model
    # For Gemini Embedding, use ChromaDB's GoogleGenerativeAiEmbeddingFunction
    embedding_function = embedding_functions.GoogleGenerativeAiEmbeddingFunction(
        api_key=os.getenv("GEMINI_API_KEY"), # Pass the API key directly
        model_name=EMBEDDING_MODEL
    )
    
    # Initialize the persistent client
    client = chromadb.PersistentClient(path=DB_PATH)
    
    # Get or create the collection, now with the embedding function configured
    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=embedding_function,
        metadata={"hnsw:space": "cosine"}
    )
    
    print(f"Successfully connected to ChromaDB. Collection '{COLLECTION_NAME}' is ready.")
    return collection

def clear_db_collection():
    """Clears all data from the specified collection."""
    print(f"Clearing all data from collection '{COLLECTION_NAME}'...")
    client = chromadb.PersistentClient(path=DB_PATH)
    client.delete_collection(name=COLLECTION_NAME)
    # Recreate the collection after deleting it
    get_db_collection()
    print("Collection cleared and recreated.")

if __name__ == '__main__':
    # This allows for testing the connection directly
    print("Testing database connection...")
    collection = get_db_collection()
    print(f"Collection embedding function: {collection.embedding_function.model_name}")
    print(f"Total items in collection: {collection.count()}")