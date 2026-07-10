import boto3
import textwrap

KB_ID = "1TLSOWZMCU"
REGION = "us-east-1"
MODEL_ID = "us.anthropic.claude-sonnet-4-6"

kb_client = boto3.client("bedrock-agent-runtime", region_name=REGION)
llm_client = boto3.client("bedrock-runtime", region_name=REGION)


EVAL_QUESTIONS = [
    {
        "question": "Who created Python?",
        "expected_keywords": ["Guido", "van Rossum"],
        "expected_sources": ["Python"],
        "type": "in_scope",
    },
    {
        "question": "When did Python first appear?",
        "expected_keywords": ["1991"],
        "expected_sources": ["Python"],
        "type": "in_scope",
    },
    {
        "question": "Who created JavaScript?",
        "expected_keywords": ["Brendan", "Eich"],
        "expected_sources": ["JavaScript"],
        "type": "in_scope",
    },
    {
        "question": "When did JavaScript first appear?",
        "expected_keywords": ["1995"],
        "expected_sources": ["JavaScript"],
        "type": "in_scope",
    },
    {
        "question": "Who designed Go?",
        "expected_keywords": ["Robert Griesemer", "Rob Pike", "Ken Thompson"],
        "expected_sources": ["Go"],
        "type": "in_scope",
    },
    {
        "question": "When did Go first appear?",
        "expected_keywords": ["2009"],
        "expected_sources": ["Go"],
        "type": "in_scope",
    },
    {
        "question": "Which of Python, JavaScript, and Go appeared earliest, and which appeared latest?",
        "expected_keywords": ["Python", "earliest", "Go", "latest"],
        "expected_sources": ["Python", "JavaScript", "Go"],
        "type": "multi_doc",
    },
    {
        "question": "Compare Python and JavaScript by creator and first appearance.",
        "expected_keywords": ["Guido", "van Rossum", "Brendan", "Eich", "1991", "1995"],
        "expected_sources": ["Python", "JavaScript"],
        "type": "multi_doc",
    },
    {
        "question": "What is the capital of Turkey?",
        "expected_keywords": ["I don't know based on the provided documents"],
        "expected_sources": [],
        "type": "out_of_scope",
    },
]


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


def source_uri(result) -> str:
    location = result.get("location", {})

    if location.get("type") == "S3":
        return location.get("s3Location", {}).get("uri", "Unknown S3 URI")

    return str(location)


def build_context(results):
    context_blocks = []

    for i, result in enumerate(results, start=1):
        text = result.get("content", {}).get("text", "")
        source = source_uri(result)

        context_blocks.append(
            f"[Source {i}]\n"
            f"Document: {source}\n"
            f"Text:\n{text}"
        )

    return "\n\n".join(context_blocks)


def generate_answer(query: str, results):
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
        system=[{"text": system_prompt}],
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

    return response["output"]["message"]["content"][0]["text"]


def keyword_check(answer: str, expected_keywords):
    answer_lower = answer.lower()
    missing = []

    for keyword in expected_keywords:
        if keyword.lower() not in answer_lower:
            missing.append(keyword)

    return missing


def source_check(results, expected_sources):
    sources = [source_uri(result) for result in results]
    joined_sources = " ".join(sources).lower()

    missing_sources = []

    for expected in expected_sources:
        if expected.lower() not in joined_sources:
            missing_sources.append(expected)

    return missing_sources, sources


def evaluate():
    passed = 0
    total = len(EVAL_QUESTIONS)

    print("\nBedrock Knowledge Base Evaluation")
    print("=" * 100)
    print(f"KB_ID: {KB_ID}")
    print(f"Model: {MODEL_ID}")
    print(f"Questions: {total}")
    print("=" * 100)

    for index, item in enumerate(EVAL_QUESTIONS, start=1):
        question = item["question"]
        expected_keywords = item["expected_keywords"]
        expected_sources = item["expected_sources"]

        print("\n" + "=" * 100)
        print(f"QUESTION {index}: {question}")
        print(f"TYPE: {item['type']}")
        print("=" * 100)

        results = retrieve_chunks(question)
        answer = generate_answer(question, results)

        missing_keywords = keyword_check(answer, expected_keywords)
        missing_sources, sources = source_check(results, expected_sources)

        keyword_pass = len(missing_keywords) == 0
        source_pass = len(missing_sources) == 0

        final_pass = keyword_pass and source_pass

        if final_pass:
            passed += 1

        print("\nANSWER:")
        print(textwrap.fill(answer, width=100))

        print("\nEXPECTED KEYWORDS:")
        print(expected_keywords)

        print("\nMISSING KEYWORDS:")
        print(missing_keywords if missing_keywords else "None")

        print("\nEXPECTED SOURCES:")
        print(expected_sources if expected_sources else "No required source for out-of-scope question")

        print("\nMISSING SOURCES:")
        print(missing_sources if missing_sources else "None")

        print("\nRETRIEVED SOURCES:")
        unique_sources = []
        for source in sources:
            if source not in unique_sources:
                unique_sources.append(source)

        for source in unique_sources:
            print(f"- {source}")

        print("\nRESULT:")
        print("PASS" if final_pass else "FAIL")

    print("\n" + "=" * 100)
    print("FINAL SCORE")
    print("=" * 100)
    print(f"{passed}/{total} passed ({round((passed / total) * 100)}%)")


if __name__ == "__main__":
    evaluate()
