import json
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

def get_links(url, base_url):
    """Fetch the content of the web page and extract links."""
    response = requests.get(url)
    response.raise_for_status()

    soup = BeautifulSoup(response.content, 'html.parser')
    a_tags = soup.find_all('a')
    
    # Resolve relative links
    links = [urljoin(base_url, a['href']) for a in a_tags if a.has_attr('href')]
    
    return links

def extract_paper_details(target_url):
    # Fetch the content of the URL
    response = requests.get(target_url)
    response.raise_for_status()

    soup = BeautifulSoup(response.content, 'html.parser')

    # Extracting Title
    title = soup.find('h2', id="title").a.text

    # Extracting Authors
    authors_tags = soup.select("p.lead a")
    authors = [author.text for author in authors_tags]

    # Extracting Publication Year
    year_tag = soup.find('dt', text='Year:')
    year = year_tag.find_next_sibling('dd').text if year_tag else None

    # Extracting URL
    url_tag = soup.find('dt', text='URL:')
    url = url_tag.find_next_sibling('dd').a['href'] if url_tag else None

    # Creating a dictionary to store the extracted details
    details = {
        "Title": title,
        "Authors": authors,
        "Publication Year": year,
        "URL": url
    }

    return details

def get_strong_links(url):
    """Fetch the content of the web page and extract links within <strong> tags."""
    response = requests.get(url)
    response.raise_for_status()

    soup = BeautifulSoup(response.content, 'html.parser')

    # Find all <strong> tags that contain <a> tags
    strong_tags = soup.find_all('strong')

    links = []
    for strong in strong_tags:
        a_tags = strong.find_all('a')
        for a in a_tags:
            if a.has_attr('href'):
                # Resolve relative links
                links.append(urljoin(url, a['href']))

    return links

def save_to_jsonl(data, filename="emnlp.jsonl"):
    """Appends data to a JSONL file."""
    with open(filename, "a", encoding="utf-8") as f:
        json_string = json.dumps(data, ensure_ascii=False)
        f.write(json_string + "\n")

def process_page(url):
    """A function to process each fetched page."""
    # For demonstration, just print the URL, but you can do more complex actions here
    if 'emnlp' in url and 'event' in url:
        sl = get_strong_links(url)
        for l in sl:
            print(f"Processing page: {l}")
            try:
                d = extract_paper_details(l)
                save_to_jsonl(d)
            except Exception as e:
                print('\t', 'failed on: ', l)



    # E.g., extract data, save content, etc.

def crawl_website(start_url, limit=10):
    """Crawl the website starting from the given URL."""
    visited = set()
    to_visit = [start_url]

    while to_visit:
        current_url = to_visit.pop(0)
        
        if current_url not in visited:
            process_page(current_url)
            visited.add(current_url)

            for link in get_links(current_url, current_url):
                if link not in visited:
                    to_visit.append(link)

if __name__ == "__main__":
    crawl_website(start_url='https://aclanthology.org/venues/emnlp/')
