import urllib.request
import boto3
import xml.etree.ElementTree as ET

BUCKET = "ask-my-docs-kb-863760760863"
KB_ID = "1TLSOWZMCU"
DATA_SOURCE_ID = "JKN6EFQCMG"

NS = {
    "leg": "http://www.legislation.gov.uk/namespaces/legislation",
    "dc": "http://purl.org/dc/elements/1.1/",
    "dct": "http://purl.org/dc/terms/",
}

# The acts this job keeps up to date
ACTS = [
    ("data_protection_2018", "ukpga/2018/12"),
    ("equality_2010", "ukpga/2010/15"),
    ("modern_slavery_2015", "ukpga/2015/30"),
    ("bribery_2010", "ukpga/2010/23"),
    ("health_safety_1974", "ukpga/1974/37"),
]

s3 = boto3.client("s3")
bedrock_agent = boto3.client("bedrock-agent")

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
    return title, modified, description, " ".join(body_text.split())

def lambda_handler(event, context):
    results = []

    for name, act_path in ACTS:
        url = f"https://www.legislation.gov.uk/{act_path}/introduction/data.xml"
        with urllib.request.urlopen(url) as response:
            xml_bytes = response.read()

        title, modified, description, text = extract_from_xml(xml_bytes)
        content = f"TITLE: {title}\nMODIFIED: {modified}\nDESCRIPTION: {description}\n\n{text}"

        key = f"legislation/{name}.txt"
        s3.put_object(Bucket=BUCKET, Key=key, Body=content.encode("utf-8"))
        results.append({"act": title, "modified": modified, "key": key})

    # After uploading all acts, trigger the KB to re-sync.
    # Gracefully handle the case where a sync is already running.
    try:
        sync = bedrock_agent.start_ingestion_job(
            knowledgeBaseId=KB_ID,
            dataSourceId=DATA_SOURCE_ID,
        )
        ingestion_job_id = sync["ingestionJob"]["ingestionJobId"]
        sync_status = "started"
    except bedrock_agent.exceptions.ConflictException:
        ingestion_job_id = None
        sync_status = "skipped - a sync was already in progress"

    return {
        "statusCode": 200,
        "acts_processed": len(results),
        "results": results,
        "sync_status": sync_status,
        "ingestion_job_id": ingestion_job_id,
    }