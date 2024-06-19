import csv
import os
import requests
from pathlib import Path
from nomic import AtlasDataset

def fetch_commits(repo_url):
    # Get the owner and repo from the URL
    parts = repo_url.rstrip('/').split('/')
    owner = parts[-2]
    repo = parts[-1]

    # GitHub API endpoint 
    api_url = f"https://api.github.com/repos/{owner}/{repo}/commits"

    # Requests to GitHub API with pagination
    commits = []
    page = 1
    while True:
        response = requests.get(api_url, params={'page': page, 'per_page': 100})
        if response.status_code == 200:
            page_commits = response.json()
            if not page_commits:
                break
            commits.extend(page_commits)
            page += 1
        else:
            print(f"Failed to fetch commits: {response.status_code}")
            break

    return commits

def save_commits_to_csv(commits, csv_filename):
    with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['id', 'message']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        for i, commit in enumerate(commits):
            try:
                commit_message = commit['commit']['message']
                writer.writerow({'id': i, 'message': commit_message})
            except (KeyError, TypeError) as e:
                print(f"Error processing commit {i}: {e}")
                print(f"Commit data: {commit}")

def create_commit_map(csv_filename):
    # Read the CSV file and prepare data for AtlasDataset
    data = []
    with open(csv_filename, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            data.append({'id': row['id'], 'text': row['message']})

    # Create AtlasDataset and add data
    dataset = AtlasDataset(
        "github-commit-dataset",
        unique_id_field="id",
    )

    dataset.add_data(data=data)

    # Create the map
    map = dataset.create_index(
        indexed_field='text',
        topic_model=True,
        duplicate_detection=True,
        projection=None,
        embedding_model='NomicEmbed'
    )

    return map

if __name__ == "__main__":
    repo_url = input("URL of Github Repository: ")
    
    commits = fetch_commits(repo_url)
    if commits:
        # Get the path to the desktop
        desktop_path = str(Path.home() / "Desktop" / "commits.csv")
        csv_filename = desktop_path
        
        save_commits_to_csv(commits, csv_filename)
        print(f"Commits have been saved to {csv_filename}")
        
        # Open the CSV file automatically
        if os.name == 'nt':  # For Windows
            os.startfile(csv_filename)
        elif os.name == 'posix':  # For macOS and Linux
            os.system(f"open {csv_filename}")
        
        # Create a map using the saved commit data
        commit_map = create_commit_map(csv_filename)
        print("Commit map has been created")