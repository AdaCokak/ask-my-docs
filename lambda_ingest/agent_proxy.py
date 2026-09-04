import boto3
import json
import uuid

AGENT_ID = "OOSH346M8R"
AGENT_ALIAS_ID = "LNFGA7IN8E"

agent_runtime = boto3.client("bedrock-agent-runtime")

def lambda_handler(event, context):
    # Pull the user's question from the incoming request
    body = event.get("body")
    if isinstance(body, str):
        body = json.loads(body)
    elif body is None:
        body = event  # allows direct testing without API Gateway wrapping

    prompt = body.get("prompt", "")

    if not prompt:
        return {
            "statusCode": 400,
            "body": json.dumps({"error": "Missing 'prompt' in request."})
        }

    # Call the agent
    response = agent_runtime.invoke_agent(
        agentId=AGENT_ID,
        agentAliasId=AGENT_ALIAS_ID,
        sessionId=str(uuid.uuid4()),
        inputText=prompt,
    )

    # The response streams back as chunks; concatenate them into one answer
    completion = ""
    for chunk_event in response.get("completion"):
        chunk = chunk_event["chunk"]
        completion += chunk["bytes"].decode("utf-8")

    return {
        "statusCode": 200,
        "body": json.dumps({"answer": completion})
    }
