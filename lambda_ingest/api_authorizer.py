import os

# The shared secret. Set as a Lambda environment variable, never hard-coded.
EXPECTED_KEY = os.environ.get("API_KEY", "")

def lambda_handler(event, context):
    # HTTP API passes headers lowercased in event["headers"]
    headers = event.get("headers", {})
    provided_key = headers.get("x-api-key", "")

    authorized = bool(EXPECTED_KEY) and provided_key == EXPECTED_KEY

    return {"isAuthorized": authorized}
