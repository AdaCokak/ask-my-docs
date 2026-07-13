import boto3
from datetime import datetime, timedelta

BUCKET = "ask-my-docs-kb-863760760863"
s3 = boto3.client("s3")

def get_recent_changes(days=90):
    """Read each legislation file, parse its MODIFIED date, return those changed within `days`."""
    cutoff = datetime.now() - timedelta(days=days)
    changed = []

    # List all legislation files
    objects = s3.list_objects_v2(Bucket=BUCKET, Prefix="legislation/")
    for obj in objects.get("Contents", []):
        key = obj["Key"]
        if not key.endswith(".txt"):
            continue
        body = s3.get_object(Bucket=BUCKET, Key=key)["Body"].read().decode("utf-8")

        # Parse the MODIFIED and TITLE lines we wrote at the top of each file
        title, modified = None, None
        for line in body.split("\n"):
            if line.startswith("TITLE:"):
                title = line.replace("TITLE:", "").strip()
            elif line.startswith("MODIFIED:"):
                modified = line.replace("MODIFIED:", "").strip()
            if title and modified:
                break

        if modified:
            try:
                mod_date = datetime.strptime(modified, "%Y-%m-%d")
                if mod_date >= cutoff:
                    changed.append({"act": title, "modified": modified})
            except ValueError:
                pass

    return changed

def lambda_handler(event, context):
    # Bedrock agent passes parameters in a specific structure; handle both direct + agent calls
    days = 90
    # If called by the agent, parameters come in event["parameters"]
    if "parameters" in event:
        for p in event.get("parameters", []):
            if p.get("name") == "days":
                days = int(p.get("value", 90))

    changes = get_recent_changes(days)

    result_text = (
        f"{len(changes)} act(s) changed in the last {days} days: " +
        "; ".join(f"{c['act']} (modified {c['modified']})" for c in changes)
        if changes else f"No acts changed in the last {days} days."
    )

    # Bedrock Agents expect a specific response format
    return {
        "messageVersion": "1.0",
        "response": {
            "actionGroup": event.get("actionGroup", ""),
            "function": event.get("function", ""),
            "functionResponse": {
                "responseBody": {
                    "TEXT": {"body": result_text}
                }
            }
        }
    }