# process_data_modal.py
import modal
from datetime import date, timedelta
import os
import requests

app = modal.App(name="federal-register-job")
image = modal.Image.debian_slim(python_version="3.10").pip_install(
    "requests", "nomic"
)

def fetch_data(target_date_str):
    """Fetches data from Federal Register API for a specific date."""
    api_url = 'https://www.federalregister.gov/api/v1/documents.json'
    params = {
        'per_page': 1000,
        'order': 'newest',
        'conditions[publication_date][is]': target_date_str
    }
    response = requests.get(api_url, params=params, timeout=10)
    response.raise_for_status()
    return response.json()

def process_data(target_date_str: str):
    """Fetches and processes federal register data for a specific date."""
    try:
        data = fetch_data(target_date_str)
        if not data:
            return []
    except requests.exceptions.RequestException as e:
        print(f"Failed to fetch data for {target_date_str}: {e}")
        return []
    
    records_to_upload = []
    results = data.get('results', [])
    for doc in results:
        doc_abstract = doc.get('abstract')
        doc_title = doc.get('title')
        if doc_abstract and isinstance(doc_abstract, str) and doc_abstract.strip():
            text_content = doc_abstract.strip()
        elif doc_title and isinstance(doc_title, str) and doc_title.strip():
            text_content = doc_title.strip()
        else:
            continue
        record = {
            'id': doc.get('document_number', str(doc.get('id'))),
            'text': text_content,
            'publication_date': date.fromisoformat(doc.get('publication_date')) if doc.get('publication_date') else None,
            'title': doc_title,
            'type': doc.get('type'),
            'agency_names': ", ".join([a.get('name', '') for a in doc.get('agencies', [])]),
            'topics': ", ".join(doc.get('topics', [])),
            'html_url': doc.get('html_url')
        }
        records_to_upload.append(record)
    return records_to_upload

def upload_to_atlas(records):
    """Uploads processed records to Nomic Atlas."""
    from nomic import AtlasDataset
    if records:
        dataset = AtlasDataset("nomic/federal_register", unique_id_field="id")
        dataset.add_data(records)
        dataset.create_index(indexed_field="title")

@app.function(
    image=image, 
    secrets=[modal.Secret.from_name("nomic-api-key")], 
    schedule=modal.Cron("30 20 * * *")
)
def daily_job():
    """Modal function that runs daily to fetch and upload Federal Register data."""
    import nomic 
    nomic.login(os.environ["NOMIC_API_KEY"])

    yesterday = date.today() - timedelta(days=1)
    target_date_str = yesterday.strftime('%Y-%m-%d')
    print(f"Fetching data for: {target_date_str}")
    processed_records = process_data(target_date_str)
    upload_to_atlas(processed_records)
