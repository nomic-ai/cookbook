from argparse import ArgumentParser
from datetime import date
import nomic
from nomic import AtlasDataset
import os
import requests

nomic.login(os.environ.get("NOMIC_API_KEY"))

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
    except requests.exceptions.RequestException:
        return []
    records_to_upload = []
    results = data.get('results', [])
    if isinstance(results, list) and results:
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
    if records:
        dataset = AtlasDataset("nomic/federal_register", unique_id_field="id")
        dataset.add_data(records)
        dataset.create_index(indexed_field="title")

if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--date")
    args = parser.parse_args()
    target_date_input = args.date
    date.fromisoformat(target_date_input)
    processed_records = process_data(target_date_input)
    upload_to_atlas(processed_records)
