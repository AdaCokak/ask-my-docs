import boto3
import textwrap

KB_ID = "1TLSOWZMCU"
REGION = "us-east-1"
MODEL_ID = "us.anthropic.claude-sonnet-4-6"

kb_client = boto3.client("bedrock-agent-runtime", region_name=REGION)
llm_client = boto3.client("bedrock-runtime", region_name=REGION)


def retrieve_chunks(query: str, number_of_results: int = 8):
    response = kb_client.retrieve(
        knowledgeBaseId=KB_ID,
        retrievalQuery={"text": query},
        retrievalConfiguration={
            "managedSearchConfiguration": {
                "numberOfResults": number_of_results,
                "rerankingModelType": "NONE"
            }
        }
    )

    return response.get("retrievalResults", [])


def build_context(results):
    context_blocks = []

    for i, result in enumerate(results, start=1):
        text = result.get("content", {}).get("text", "")

        location = result.get("location", {})
        source = "Unknown source"

        if location.get("type") == "S3":
            source = location.get("s3Location", {}).get("uri", "Unknown S3 URI")

        context_blocks.append(
            f"[Source {i}]\n"
            f"Document: {source}\n"
            f"Text:\n{text}"
        )

    return "\n\n".join(context_blocks)


def answer_question(query: str):
    results = retrieve_chunks(query)
    context = build_context(results)

    system_prompt = (
        "You are a strict RAG assistant. "
        "Answer only using the provided CONTEXT. "
        "If the CONTEXT does not directly contain the answer, respond exactly: "
        "\"I don't know based on the provided documents.\" "
        "Do not use outside knowledge. Do not guess."
    )

    user_prompt = f"""
QUESTION:
{query}

CONTEXT:
{context}

Answer the QUESTION using only the CONTEXT.
"""

    response = llm_client.converse(
        modelId=MODEL_ID,
        system=[
            {"text": system_prompt}
        ],
        messages=[
            {
                "role": "user",
                "content": [{"text": user_prompt}]
            }
        ],
        inferenceConfig={
            "temperature": 0,
            "maxTokens": 700
        }
    )

    answer = response["output"]["message"]["content"][0]["text"]

    print("\n" + "=" * 100)
    print(f"QUESTION: {query}")
    print("=" * 100)
    print("\nANSWER:")
    print(textwrap.fill(answer, width=100))

    print("\nSOURCES RETRIEVED:")
    for i, result in enumerate(results, start=1):
        location = result.get("location", {})
        source = "Unknown source"

        if location.get("type") == "S3":
            source = location.get("s3Location", {}).get("uri", "Unknown S3 URI")

        print(f"{i}. {source}")


if __name__ == "__main__":
    questions = [
        "Who created Python?",
        "What is the capital of Turkey?",
        "Which of Python, JavaScript, and Go appeared earliest, and which appeared latest?"
    ]

    for question in questions:
        answer_question(question)
