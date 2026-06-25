import boto3
import json

# Create a client that talks to Bedrock in your region
client = boto3.client("bedrock-runtime", region_name="us-east-1")

# The model we're calling (the affordable workhorse)
model_id = "us.anthropic.claude-sonnet-4-6"

# Build the message we're sending
body = {
    "anthropic_version": "bedrock-2023-05-31",
    "max_tokens": 300,
    "messages": [
        {"role": "user", "content": "Say hello and tell me one fact about Bristol."}
    ],
}

# Send it to the model
response = client.invoke_model(
    modelId=model_id,
    body=json.dumps(body),
)

# Read the reply back
result = json.loads(response["body"].read())
print(result["content"][0]["text"])