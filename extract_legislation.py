import xml.etree.ElementTree as ET
import sys
import json

NS = {
    "leg": "http://www.legislation.gov.uk/namespaces/legislation",
    "dc": "http://purl.org/dc/elements/1.1/",
    "dct": "http://purl.org/dc/terms/",
    "ukm": "http://www.legislation.gov.uk/namespaces/metadata",
}

def extract(filepath):
    tree = ET.parse(filepath)
    root = tree.getroot()

    def find_text(tag):
        el = root.find(f".//{tag}", NS)
        return el.text if el is not None else None

    metadata = {
        "title": find_text("dc:title"),
        "description": find_text("dc:description"),
        "modified": find_text("dc:modified"),
        "valid_from": find_text("dct:valid"),
        "num_provisions": root.get("NumberOfProvisions"),
    }

    # Extract only the BODY text, skipping the metadata block
    # The actual legal content lives inside the leg:Body element
	# Legal content lives under Primary (or Body, depending on the document)
    content_el = root.find(".//leg:Primary", NS)
    if content_el is None:
        content_el = root.find(".//leg:Body", NS)
    if content_el is not None:
        body_text = " ".join(content_el.itertext())
    else:
        body_text = " ".join(root.itertext())
    clean_text = " ".join(body_text.split())

    return metadata, clean_text

if __name__ == "__main__":
    filepath = sys.argv[1] if len(sys.argv) > 1 else "intro_only.xml"
    metadata, text = extract(filepath)

    print("=== METADATA ===")
    for k, v in metadata.items():
        print(f"{k}: {v}")
    print(f"\n=== BODY TEXT ===")
    print(f"Characters extracted: {len(text)}")
    print(f"First 400 chars:\n{text[:400]}")

    # Save the clean text + metadata for S3 upload
    output_name = "cleaned_legislation.txt"
    with open(output_name, "w") as f:
        f.write(f"TITLE: {metadata['title']}\n")
        f.write(f"MODIFIED: {metadata['modified']}\n")
        f.write(f"DESCRIPTION: {metadata['description']}\n\n")
        f.write(text)
    print(f"\nSaved to {output_name}")