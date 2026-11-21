import os
from langchain.tools import tool
from app.rag.langchain import rag_chain, retriever

@tool(response_format="content_and_artifact")
def search_documents(question:str):
    """Search the existing knowledge base to answer questions about its documents."""

    docs=retriever.invoke(question)
    
    answer= rag_chain.invoke({
        "docs":docs,
        "question": question
    })   
    metadata=[
        {
            "source":os.path.basename(doc.metadata.get("source") or "")
        }
        for doc in docs
    ]

    return answer, metadata