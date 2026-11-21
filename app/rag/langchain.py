
import os
from langchain_postgres import PGVector
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

load_dotenv(override=True)

# Initialize the OpenAI embedding model used to convert text and questions
# into numerical vector representations for semantic similarity search.

embeddings = OpenAIEmbeddings(
    model="text-embedding-3-small"
)

# Connect to the PostgreSQL database containing document embeddings.
# PGVector manages the storage and retrieval of document vectors using
# the specified collection.

vector_store = PGVector(
    embeddings=embeddings,
    collection_name="documents",
    connection=os.environ["DATABASE_URL"]
)

# Convert the vector store into a retriever that performs semantic
# similarity search and returns the four most relevant document chunks
# for each user question.

retriever= vector_store.as_retriever(search_kwargs={"k":4})

# Define the instructions and message structure sent to the language model.
# The system message restricts answers to the retrieved context and requires
# source citations. The human message supplies the user's question.

prompt= ChatPromptTemplate.from_messages([
    ("system", "You answer questions using ONLY the provided context. "
     "If the answer is not in the context, say you don't know. "
     "Cite the source of each fact.\n\nContext:\n{context}"),
    ("human","{question}"),
])

# Initialize GPT-4o for context-based answer generation.
# Temperature 0 makes responses more deterministic, max_tokens limits
# response length, and streaming enables incremental response generation.

llm= ChatOpenAI(model="gpt-4o", max_tokens=1024,temperature=0,streaming=True)

def format_docs(docs):
    """
    Format retrieved documents into a single context string for the language
    model.

    Iterates through the retrieved documents, extracts their source metadata
    and page content, and combines them into a single string. Each document
    is prefixed with its source filename to preserve source attribution
    when the context is passed to the language model.

    Args:
        docs (list[Document]): Retrieved LangChain Document objects containing
            page content and associated metadata.

    Returns:
        str: A formatted context string containing all retrieved document
            chunks, separated by double newlines and prefixed with their
            source filenames.
    """   
    return "\n\n".join(
        f"[Source: {os.path.basename(d.metadata.get('source') or '')}] "
        f"{d.page_content}"
        for d in docs
    )


# Define the RAG chain using LangChain's LCEL (LangChain Expression Language).
# Maps the retrieved documents to a formatted context string and passes
# the user's question through unchanged.
# The prompt combines the context and question into structured messages,
# which are passed to GPT-4o for answer generation.
# StrOutputParser() extracts the generated text from the LLM response,
# returning the final answer as a string.
rag_chain=(
    {
        "context":lambda x:format_docs(x["docs"]),
        "question":lambda x: x["question"]
    }

    | prompt
    | llm
    | StrOutputParser()
)



    