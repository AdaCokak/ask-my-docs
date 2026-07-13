import boto3
import json
import sys

client = boto3.client("bedrock-runtime", region_name="us-east-1")
MODEL_ID = "us.anthropic.claude-sonnet-4-6"

def extract_intelligence(act_text):
    system_prompt = """You are a regulatory analyst. Extract structured intelligence 
from the legislation provided. Respond ONLY with a valid JSON object, no markdown, 
no explanation. Use exactly this structure:
{
  "act_title": "the official title",
  "what_it_regulates": "one clear sentence",
  "who_is_affected": ["list", "of", "affected", "parties"],
  "key_obligations": ["list", "of", "main", "duties", "it", "imposes"],
  "enforcement_body": "the body that enforces it, or null if not stated"
}
If a field isn't in the text, use null or an empty list. Do not invent facts."""

    body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 800,
        "temperature": 0,
        "system": system_prompt,
        "messages": [
            {"role": "user", "content": f"Extract intelligence from this legislation:\n\n{act_text}"}
        ],
    }

    response = client.invoke_model(modelId=MODEL_ID, body=json.dumps(body))
    result = json.loads(response["body"].read())
    return result["content"][0]["text"]

if __name__ == "__main__":
    import glob

    # Process every legislation .txt file
    act_files = sorted(glob.glob("*.txt"))
    # Skip non-legislation txt files if any
    act_files = [f for f in act_files if f not in ("cleaned_legislation.txt",)]

    all_intelligence = []

    for filepath in act_files:
        print(f"Processing {filepath}...")
        with open(filepath) as f:
            act_text = f.read()

        raw = extract_intelligence(act_text)
        try:
            data = json.loads(raw)
            data["source_file"] = filepath
            all_intelligence.append(data)
            print(f"  -> {data['act_title']}")
        except json.JSONDecodeError:
            print(f"  -> FAILED to parse JSON for {filepath}")

    # Save all extracted intelligence to one file
    with open("intelligence.json", "w") as f:
        json.dump(all_intelligence, f, indent=2)

    print(f"\nExtracted intelligence from {len(all_intelligence)} acts.")
    print("Saved to intelligence.json")