import os
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter


def ingest_documents():
    """
    Load Markdown documents, split them into smaller chunks, and initialize
    the embedding model.

    Reads the specified Markdown files from the corpus directory, splits their
    contents into overlapping text chunks, and attaches source information
    to each chunk through metadata.

    Returns:
        tuple:
            - chunks (list[str]): Text chunks generated from the Markdown
              documents.
            - metadata (list[dict]): Metadata dictionaries containing the
              source file path for each corresponding chunk.
            - embeddings (OpenAIEmbeddings): Initialized OpenAI embedding
              model using text-embedding-3-small.
    """
    md_files=[
        "corpus/ForensicsUI_Study_Guide.md",
        "corpus/Heart_Disease_Project_Study_Guide.md"
    ]

    documents=[]
    for md_file in md_files:
        with open(md_file,"r") as file:
            documents.append(file.read())
        

    splitter=RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50
    )

    chunks=[]
    metadata=[]

    for i,document in enumerate(documents):
        document_chunks=splitter.split_text(document)
        chunks.extend(document_chunks)
        metadata.extend([{"source":md_files[i]}]*len(document_chunks))
    embeddings= OpenAIEmbeddings(model="text-embedding-3-small")
    return chunks,metadata,embeddings


      


    


