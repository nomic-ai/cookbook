import requests
import csv
import os
import platform
import subprocess
from nomic import atlas

def fetch_commits(repo_url):
    # Extract owner and repo name from the GitHub URL
    
    owner, repo = repo_url.rstrip('/').split('/')[-2:]
    

    commits_url = f"https://api.github.com/repos/{owner}/{repo}/commits"

    commits = []
    page = 1

    while True:
        response = requests.get(commits_url, params={'page': page, 'per_page': 100})
        if response.status_code != 200:
            print(f"Error fetching commits: {response.status_code}")
            break
        
        page_commits = response.json()
        if not page_commits:
            break

        for commit in page_commits:
            commit_message = commit['commit']['message']
            commits.append(commit_message)
        
        page += 1

    return commits

def save_commits_to_csv(commits, filename):
    with open(filename, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(['ID', 'Commit Message'])
        for idx, commit in enumerate(commits, start=1):
            writer.writerow([idx, commit])
    print(f"Commit messages have been saved to {filename}")

def open_file(filepath):
    if platform.system() == "Darwin":       # macOS
        subprocess.call(('open', filepath))
    elif platform.system() == "Windows":    # Windows
        os.startfile(filepath)
    elif platform.system() == "Linux":      # Linux
        subprocess.call(('xdg-open', filepath))


def main():
    repo_url = input("Please enter the GitHub Repository URL: ")
    commits = fetch_commits(repo_url)
    
    if commits:
        desktop_path = os.path.join(os.path.join(os.path.expanduser('~')), 'Desktop')
        filename = os.path.join(desktop_path, 'commits.csv')
        save_commits_to_csv(commits, filename)
        open_file(filename)
        

if __name__ == "__main__":
    main()