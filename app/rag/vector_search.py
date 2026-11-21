import os
import psycopg
from dotenv import load_dotenv
from langchain_postgres import PGVector
from ingest_documents import ingest_documents

load_dotenv(override=True)

def store_embeddings():
    """
    Generate embeddings for document chunks and store them in a PostgreSQL
    vector database using PGVector.

    Calls ingest_documents() to retrieve text chunks, their corresponding
    metadata, and the OpenAI embedding model. Initializes a PGVector store
    with the specified collection name and database connection, then
    generates and stores the document embeddings along with their metadata.

    Returns:
        PGVector: Initialized PGVector vector store containing the stored
        document embeddings and their associated metadata.
    """
    chunks, metadata, embeddings=ingest_documents()
    store= PGVector(
        embeddings=embeddings,
        collection_name="documents",
        connection=os.environ["DATABASE_URL"].replace("postgresql://", "postgresql+psycopg://")

    )
    store.add_texts(chunks,metadatas=metadata)
    return store


