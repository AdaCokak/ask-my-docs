import requests
from extract_legislation import extract  # reuse your existing extractor

# Acts to fetch: (friendly_name, legislation.gov.uk path)
ACTS = [
    ("equality_act_2010", "ukpga/2010/15"),
    ("modern_slavery_act_2015", "ukpga/2015/30"),
    ("bribery_act_2010", "ukpga/2010/23"),
    ("health_safety_work_1974", "ukpga/1974/37"),
]

for name, path in ACTS:
    url = f"https://www.legislation.gov.uk/{path}/introduction/data.xml"
    xml_file = f"{name}.xml"
    txt_file = f"{name}.txt"

    print(f"Fetching {name}...")
    resp = requests.get(url)
    with open(xml_file, "wb") as f:
        f.write(resp.content)

    metadata, text = extract(xml_file)

    with open(txt_file, "w") as f:
        f.write(f"TITLE: {metadata['title']}\n")
        f.write(f"MODIFIED: {metadata['modified']}\n")
        f.write(f"DESCRIPTION: {metadata['description']}\n\n")
        f.write(text)

    print(f"  -> {metadata['title']}")
    print(f"     modified: {metadata['modified']}, text chars: {len(text)}")

print("\nDone. All acts fetched and extracted.")