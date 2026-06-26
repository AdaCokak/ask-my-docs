import boto3
import json

client = boto3.client("bedrock-runtime", region_name="us-east-1")
model_id = "us.anthropic.claude-sonnet-4-6"

def call_claude(system_prompt, user_message, temperature=0.5):
    body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 150,
        "temperature": temperature,
        "system": system_prompt,
        "messages": [
            {"role": "user", "content": user_message}
        ],
    }
    response = client.invoke_model(
        modelId=model_id,
        body=json.dumps(body),
    )
    result = json.loads(response["body"].read())
    return result["content"][0]["text"]

system = """You are a creative writing assistant."""

question ="Write one sentence describing what it feels like when a new law comes into effect."

print("=== TEMPERATURE 0.0 — Run 1 (deterministic) ===")
print(call_claude(system, question, temperature=0.0))

print("\n=== TEMPERATURE 0.0 — Run 2 (should be identical) ===")
print(call_claude(system, question, temperature=0.0))

print("\n=== TEMPERATURE 1.0 — Run 1 (creative) ===")
print(call_claude(system, question, temperature=1.0))

print("\n=== TEMPERATURE 1.0 — Run 2 (should differ) ===")
print(call_claude(system, question, temperature=1.0))