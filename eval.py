
from dotenv import load_dotenv
from langsmith import Client
from openevals.llm import create_llm_as_judge


CUSTOM_CORRECTNESS_PROMPT = """
You are an expert evaluator for a Retrieval-Augmented Generation (RAG) application.

Your task is to determine whether the actual answer is semantically correct
compared with the reference answer.

Evaluation rules:

1. Evaluate meaning, not exact wording.
   Different words and sentence structures are acceptable when they
   communicate the same meaning.

2. IMPORTANT: Handle unavailable-information responses correctly.
   If the reference answer indicates that the information is unavailable,
   responses such as the following are equivalent:
   - "I don't know."
   - "I couldn't find that information."
   - "The information is not available."
   - "No relevant information was found."

   These responses must receive a correct score when they communicate
   the same unavailable-information result.

3. If the reference answer contains factual information, the actual answer
   must communicate the correct facts.

4. An answer that says "I don't know" when the reference contains an
   available factual answer is incorrect.

5. An answer that invents information when the reference indicates
   that information is unavailable is incorrect.

6. Do not require exact wording or identical sentence structure.

7. Do not reward an answer that contradicts the reference answer.

Question:
{inputs}

Reference answer:
{reference_outputs}

Actual answer:
{outputs}

Return a correctness score:
- True: The actual answer is semantically correct.
- False: The actual answer is incorrect, incomplete in a materially
  important way, or contradicts the reference.

Provide a brief explanation for your decision.
"""


from app.rag.agent import agent

load_dotenv(override=True)

# Connect to LangSmith
client = Client()

# Create the correctness evaluator
correctness_evaluator = create_llm_as_judge(
    prompt=CUSTOM_CORRECTNESS_PROMPT,
    model="openai:gpt-4o",
    feedback_key="correctness"
)

DATASET_NAME = "rag-agent-evaluation-v1"


def target(inputs: dict) -> dict:
    question = inputs["question"]

    response = agent.invoke({
        "messages": [
            {
                "role": "user",
                "content": question
            }
        ]
    })

    answer = response["messages"][-1].content

    return {
        "answer": answer
    }

results = client.evaluate(
    target,
    data=DATASET_NAME,
    evaluators=[correctness_evaluator],
    experiment_prefix="rag-agent-correctness-v1"
)

