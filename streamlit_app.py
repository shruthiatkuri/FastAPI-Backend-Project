import os
import json
import streamlit as st
import requests

st.set_page_config(
    page_title="RAG AI Assistence",
    layout="wide"
)

st.title("RAG AI Assistant")

st.caption(
    "Ask questions about projects in knowledge base "
    "and get answers from AI Agent"
)

question=st.text_input(
    "Enter your question",
    placeholder="Ask something ....."
)


API_URL= os.getenv(
    "API_URL",
    "http://127.0.0.1:8000/ask")

def stream_answer(question:str):
    """
    Send a question to the FastAPI endpoint and stream its response.

    Sends the question as a JSON payload using an HTTP POST request.
    Reads the Server-Sent Events (SSE) response line by line, parses
    each data event from JSON into a Python dictionary, and yields
    the event to the caller as soon as it is received.

    Args:
        question (str): The user's question to send to the API.

    Yields:
        dict: A parsed SSE event containing response data, such as
            generated tokens, source metadata, or completion status.

    Raises:
        requests.exceptions.HTTPError: If the API returns an unsuccessful
            HTTP status code.
        requests.exceptions.Timeout: If the connection or response
            exceeds the configured timeout.
        requests.exceptions.RequestException: If an HTTP request error
            occurs.
        json.JSONDecodeError: If an SSE data payload contains invalid JSON.
    """

    payload={"question":question}

    with requests.post(
        API_URL,
        json=payload,
        stream=True,
        timeout=(5,120)
    ) as response:

        response.raise_for_status()
        response.encoding= "utf-8"

        for line in response.iter_lines(decode_unicode=True):
            if line and line.startswith("data:"):
                event_data= line[len("data:"):].strip()

                event= json.loads(event_data)

                yield event
        

# Handle the user's question and display the streamed AI response.
# When the user clicks the Ask button and enters a non-empty question,
# this block:
# 1. Initializes placeholders for the generated answer and source metadata.
# 2. Calls the FastAPI backend through stream_answer().
# 3. Processes incoming SSE events based on their event type.
# 4. Displays generated tokens incrementally in the Streamlit interface.
# 5. Collects source metadata and displays it after generation.
# 6. Handles connection, timeout, HTTP, and request errors.

if st.button("Ask") and question.strip():
    st.subheader("Answer")

    answer=""
    source=[]

    try:
        with st.spinner("Generating answer..."):
            answer_placeholder= st.empty()
            for event in stream_answer(question):
                event_type = event.get("type")

                if event_type == "token":
                    answer += event.get("content","")
                    answer_placeholder.markdown(
                        answer + "▌"
                    )

                elif event_type == "source":
                    source= event.get("content",[])

                elif event_type == "done":
                    answer_placeholder.markdown(answer)

                elif event_type == "error":
                    st.error(event.get("content","Unknown error"))
                    break
            if source:
                st.markdown("source")
                for s in source:
                    st.markdown(f"{s['source']}")
    except requests.exceptions.ConnectionError:
         st.error(
            "Cannot connect to FastAPI."
            "Please check whether the backend is running."
        )

    except requests.exceptions.Timeout:
        st.error("The request timed out.")

    except requests.exceptions.HTTPError as e:
        st.error(f"FastaAPI returned an HTTP error:{e}")

    except requests.exceptions.RequestException as e:
        st.error(f"Request failed:{e}")
