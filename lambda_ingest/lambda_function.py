import urllib.request
import boto3
import xml.etree.ElementTree as ET

# --- Config ---
BUCKET = "ask-my-docs-kb-863760760863"
NS = {
    "leg": "http://www.legislation.gov.uk/namespaces/legislation",
    "dc": "http://purl.org/dc/elements/1.1/",
    "dct": "http://purl.org/dc/terms/",
}

s3 = boto3.client("s3")

def extract_from_xml(xml_bytes):
    root = ET.fromstring(xml_bytes)

    def find_text(tag):
        el = root.find(f".//{tag}", NS)
        return el.text if el is not None else None

    title = find_text("dc:title")
    modified = find_text("dc:modified")
    description = find_text("dc:description")

    content_el = root.find(".//leg:Primary", NS)
    if content_el is None:
        content_el = root.find(".//leg:Body", NS)
    body_text = " ".join(content_el.itertext()) if content_el is not None else ""
    clean_text = " ".join(body_text.split())

    return title, modified, description, clean_text

def lambda_handler(event, context):
    # Which act to fetch — can be passed in the event, or default
    act_path = event.get("act_path", "ukpga/2015/30")  # default: Modern Slavery Act
    name = event.get("name", "test_act")

    url = f"https://www.legislation.gov.uk/{act_path}/introduction/data.xml"

    # Fetch the legislation
    with urllib.request.urlopen(url) as response:
        xml_bytes = response.read()

    # Extract
    title, modified, description, text = extract_from_xml(xml_bytes)

    # Build the text file content
    content = f"TITLE: {title}\nMODIFIED: {modified}\nDESCRIPTION: {description}\n\n{text}"

    # Upload to S3
    key = f"legislation/{name}.txt"
    s3.put_object(Bucket=BUCKET, Key=key, Body=content.encode("utf-8"))

    return {
        "statusCode": 200,
        "act": title,
        "modified": modified,
        "uploaded_to": f"s3://{BUCKET}/{key}",
        "text_length": len(text),
    }