import boto3
import json

KB_ID = "1TLSOWZMCU"

_agent_runtime = None

def get_agent_runtime():
    global _agent_runtime
    if _agent_runtime is None:
        _agent_runtime = boto3.client("bedrock-agent-runtime")
    return _agent_runtime

def lambda_handler(event, context):
    # Pull the search query the agent passes
    query = ""
    for p in event.get("parameters", []):
        if p.get("name") == "query":
            query = p.get("value", "")

    if not query:
        result_text = "No query provided. Provide a 'query' describing what to search for in the legislation."
        return _respond(event, result_text)

    # Retrieve relevant chunks from the knowledge base
    response = get_agent_runtime().retrieve(
        knowledgeBaseId=KB_ID,
        retrievalQuery={"text": query},
        retrievalConfiguration={
            "managedSearchConfiguration": {"numberOfResults": 5}
        },
    )

    # Format the retrieved chunks into readable text for the agent
    chunks = response.get("retrievalResults", [])
    if not chunks:
        result_text = f"No relevant legislation found for: {query}"
    else:
        parts = []
        for i, chunk in enumerate(chunks, 1):
            text = chunk.get("content", {}).get("text", "")
            source = chunk.get("location", {}).get("s3Location", {}).get("uri", "unknown")
            parts.append(f"[Result {i} | source: {source}]\n{text}")
        result_text = "\n\n".join(parts)

    return _respond(event, result_text)

def _respond(event, text):
    return {
        "messageVersion": "1.0",
        "response": {
            "actionGroup": event.get("actionGroup", ""),
            "function": event.get("function", ""),
            "functionResponse": {
                "responseBody": {"TEXT": {"body": text}}
            }
        }
    }
