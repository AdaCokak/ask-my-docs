import sys
import os
import json
from unittest.mock import patch, MagicMock

import boto3
from moto import mock_aws

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lambda_ingest"))

BUCKET = "ask-my-docs-kb-863760760863"


def _agent_event(act_value):
    """Build a fake Bedrock-agent event, the shape the real agent sends."""
    return {
        "parameters": [{"name": "act", "value": act_value}],
        "actionGroup": "extract-intelligence",
        "function": "extractIntelligence",
    }


@mock_aws
def test_handler_reads_s3_and_returns_envelope():
    # 1. moto gives us a fake S3. Create the bucket and put a fake act file in it.
    s3 = boto3.client("s3", region_name="us-east-1")
    s3.create_bucket(Bucket=BUCKET)
    s3.put_object(
        Bucket=BUCKET,
        Key="legislation/modern_slavery_2015.txt",
        Body=b"An Act to make provision about slavery, servitude and forced labour.",
    )

    # 2. Import the handler AFTER moto is active, so its module-level
    #    boto3 clients bind to the mocked AWS, not real AWS.
    import extract_intelligence_tool as tool

    # 3. Bedrock can't be simulated by moto, so mock the model response.
    fake_bedrock_response = {
        "body": MagicMock(
            read=lambda: json.dumps(
                {"content": [{"text": '{"act_title": "Modern Slavery Act 2015"}'}]}
            ).encode("utf-8")
        )
    }

    fake_bedrock_client = MagicMock()
    fake_bedrock_client.invoke_model.return_value = fake_bedrock_response

    with patch.object(tool, "get_bedrock", return_value=fake_bedrock_client):
        result = tool.lambda_handler(_agent_event("modern slavery"), None)

    # 4. Assert the handler returned the correct Bedrock-agent envelope.
    assert result["messageVersion"] == "1.0"
    body = result["response"]["functionResponse"]["responseBody"]["TEXT"]["body"]
    assert "Modern Slavery Act 2015" in body


@mock_aws
def test_handler_unknown_act_returns_helpful_message():
    s3 = boto3.client("s3", region_name="us-east-1")
    s3.create_bucket(Bucket=BUCKET)

    import extract_intelligence_tool as tool

    # No S3 read or Bedrock call should happen for an unknown act,
    # so we don't even need to mock Bedrock here.
    result = tool.lambda_handler(_agent_event("nonsense act"), None)

    body = result["response"]["functionResponse"]["responseBody"]["TEXT"]["body"]
    assert "Could not find" in body
