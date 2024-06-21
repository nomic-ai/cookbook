import csv
import os
import subprocess
from pathlib import Path
from nomic import AtlasDataset

# UPDATES: Additional Columns, Responsive Title, Map Label Tags
#use tmpdirectory
#Clones git repo if it isnt cloned already 
#where temp files goes, using the temp directory gives me the path use the path to clone and download cleans ups after using it
# doesnt matter what os 
def clone_repo(repo_url, repo_path):
    if not os.path.exists(repo_path):
        subprocess.run(['git', 'clone', '--mirror', repo_url, repo_path])
    else:
        subprocess.run(['git', '-C', repo_path, 'fetch', '--all'])

# gets commit messages from the cloned repo
def fetch_commits_from_local_repo(repo_path):
    commit_list = []
    result = subprocess.run(
        ['git', '-C', repo_path, 'log', '--format=%H;%an;%ae;%ad;%s'],
        capture_output=True,
        text=True,
        encoding='latin1',
    )
    commits = result.stdout.strip().split('\n')
#6 columns that are made in csv file
    for i, commit in enumerate(commits, start=1):
        try:
            hash, author, email, date, message = commit.split(';', 4)
            commit_list.append({
                'id': i,
                'hash': hash,
                'author': author,
                'email': email,
                'date': date,
                'message': message
            })
        except ValueError as e:
            print(f"ValueError occurred on commit {i}: {e}. Skipping this commit.")
        #skips comment fit ehre are characters that breaksthe code
    return commit_list

#saves file to a csv file
def save_commits_to_csv(commits, csv_filename):
    with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['id', 'hash', 'author', 'email', 'date', 'message']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for commit in commits:
            writer.writerow(commit)

#creates a map on atlas
def create_commit_map(csv_filename, map_name):
    data = []
    with open(csv_filename, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            data.append({'id': row['id'], 'text': row['message']})

    if not data:
        raise ValueError("No data found in CSV file.")

    dataset = AtlasDataset(
        map_name, #responsive map name
        unique_id_field="id",
    )
    dataset.add_data(data=data)

    map = dataset.create_index(
        indexed_field='text',
        topic_model=True,
        embedding_model='NomicEmbed'
    )

    return map

#attempt at letting it take in multiple repos, does not work for some reason - saying that datsets have to have at least 20 pts but it does
if __name__ == "__main__":
    repo_urls = input("Enter GitHub Repository URLs separated by commas: ").split(',')
    all_commits = []
    repo_names = []
    base_path = str(Path.home() / "repos")

    for repo_url in repo_urls:
        repo_name = repo_url.rstrip('/').split('/')[-1].strip() # collects repo name from url to make map name
        repo_names.append(repo_name)
        repo_path = os.path.join(base_path, repo_name)

        clone_repo(repo_url.strip(), repo_path)
        commits = fetch_commits_from_local_repo(repo_path)

        if commits:
            all_commits.extend(commits)

    if all_commits:
        combined_repo_names = '_'.join(repo_names)  # Combines repo names with underscores
        desktop_path = str(Path.home() / "Desktop" / f"{combined_repo_names}_commits.csv")
        csv_filename = desktop_path

        save_commits_to_csv(all_commits, csv_filename)
        print(f"Combined commits have been saved to {csv_filename}")

        if os.name == 'posix':
            os.system(f"open {csv_filename}")

        map_name = os.path.splitext(os.path.basename(csv_filename))[0]
        
        try:
            commit_map = create_commit_map(csv_filename, map_name)
            print(f"Commit map '{map_name}' has been created")
        except ValueError as e:
            print(f"Error creating commit map: {e}")



