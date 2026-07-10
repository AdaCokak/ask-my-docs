import boto3
import textwrap

KB_ID = "1TLSOWZMCU"
REGION = "us-east-1"

client = boto3.client("bedrock-agent-runtime", region_name=REGION)


def retrieve_from_kb(query: str, number_of_results: int = 8) -> None:
    print("\n" + "=" * 100)
    print(f"QUERY: {query}")
    print("=" * 100)

    response = client.retrieve(
        knowledgeBaseId=KB_ID,
        retrievalQuery={"text": query},
        retrievalConfiguration={
            "managedSearchConfiguration": {
                "numberOfResults": number_of_results,
                "rerankingModelType": "NONE"
            }
        }
    )

    results = response.get("retrievalResults", [])

    print(f"\nRetrieved chunks: {len(results)}")

    if not results:
        print("No chunks retrieved.")
        return

    for i, result in enumerate(results, start=1):
        text = result.get("content", {}).get("text", "")
        score = result.get("score", "No score shown")

        location = result.get("location", {})
        source = "Unknown source"

        if location.get("type") == "S3":
            source = location.get("s3Location", {}).get("uri", "Unknown S3 URI")
        else:
            source = str(location)

        print(f"\n--- RESULT {i} ---")
        print(f"Score: {score}")
        print(f"Source: {source}")
        print("Text:")
        print(textwrap.fill(text[:1200], width=100))


if __name__ == "__main__":
    questions = [
        "Who created Python?",
        "What is the capital of Turkey?",
        "Which of Python, JavaScript, and Go appeared earliest, and which appeared latest?"
    ]

    for question in questions:
        retrieve_from_kb(question)
