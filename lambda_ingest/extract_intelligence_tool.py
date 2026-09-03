import boto3
import json

BUCKET = "ask-my-docs-kb-863760760863"
MODEL_ID = "us.anthropic.claude-sonnet-4-6"

s3 = boto3.client("s3")
bedrock_runtime = boto3.client("bedrock-runtime")

# Map friendly act names the agent might use to their S3 filenames
ACT_FILES = {
    "data protection": "legislation/data_protection_2018.txt",
    "equality": "legislation/equality_2010.txt",
    "modern slavery": "legislation/modern_slavery_2015.txt",
    "bribery": "legislation/bribery_2010.txt",
    "health and safety": "legislation/health_safety_1974.txt",
}

def find_act_file(act_name):
    """Match the agent's act name to a file, tolerant of partial names."""
    if not act_name or not act_name.strip():
        return None

    act_lower = act_name.strip().lower()
    for key, filepath in ACT_FILES.items():
        if key in act_lower or act_lower in key:
            return filepath

    return None

def extract_intelligence(act_text):
    system_prompt = """You are a regulatory analyst. Extract structured intelligence
from the legislation. Respond ONLY with a valid JSON object, no markdown. Structure:
{"act_title": "", "what_it_regulates": "", "who_is_affected": [], "key_obligations": [], "enforcement_body": null}
Do not invent facts; use null or empty lists if a field isn't in the text."""

    body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 800,
        "temperature": 0,
        "system": system_prompt,
        "messages": [{"role": "user", "content": f"Extract intelligence from:\n\n{act_text}"}],
    }
    response = bedrock_runtime.invoke_model(modelId=MODEL_ID, body=json.dumps(body))
    result = json.loads(response["body"].read())
    return result["content"][0]["text"]

def lambda_handler(event, context):
    # Pull the 'act' parameter the agent passes
    act_name = ""
    for p in event.get("parameters", []):
        if p.get("name") == "act":
            act_name = p.get("value", "")

    filepath = find_act_file(act_name)

    if filepath is None:
        result_text = f"Could not find an act matching '{act_name}'. Available acts: Data Protection, Equality, Modern Slavery, Bribery, Health and Safety."
    else:
        act_text = s3.get_object(Bucket=BUCKET, Key=filepath)["Body"].read().decode("utf-8")
        intelligence = extract_intelligence(act_text)
        result_text = intelligence

    return {
        "messageVersion": "1.0",
        "response": {
            "actionGroup": event.get("actionGroup", ""),
            "function": event.get("function", ""),
            "functionResponse": {
                "responseBody": {"TEXT": {"body": result_text}}
            }
        }
    }
