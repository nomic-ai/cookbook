import csv
import os
import subprocess
from pathlib import Path
from nomic import AtlasDataset

#clones repo locally
def clone_repo(repo_url, repo_path):
    if not os.path.exists(repo_path):
        subprocess.run(['git', 'clone', '--mirror', repo_url, repo_path])
    else:
        subprocess.run(['git', '-C', repo_path, 'fetch', '--all'])

#gets commit messages from local repository
def fetch_commits_from_local_repo(repo_path, encoding='utf-8'):
    commit_list = []
    result = subprocess.run(['git', '-C', repo_path, 'log', '--format=%B'], capture_output=True, text=True)
    commit_messages = result.stdout.split('\n\n')


    for i, commit_message in enumerate(commit_messages, start=1):
        try:
            commit_message = commit_message.strip()
            if commit_message:
                commit_list.append({'id': i, 'message': commit_message})
        except UnicodeDecodeError:
            print(f"UnicodeDecodeError occurred on commit {i}. Skipping this commit.")


    return commit_list

#saves commits to a csv file
def save_commits_to_csv(commits, csv_filename):
    with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['id', 'message']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for commit in commits:
            writer.writerow(commit)

#creates atlas map after making it an atlas dataset
def create_commit_map(csv_filename):
    data = []
    with open(csv_filename, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            data.append({'id': row['id'], 'text': row['message']})


    dataset = AtlasDataset(
        "github-commit-dataset",
        unique_id_field="id",
    )
    dataset.add_data(data=data)


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
    repo_name = repo_url.rstrip('/').split('/')[-1]
    repo_path = str(Path.home() / "repos" / repo_name)


    clone_repo(repo_url, repo_path)


    commits = fetch_commits_from_local_repo(repo_path)
    if commits:
        desktop_path = str(Path.home() / "Desktop" / f"{repo_name}_commits.csv")
        csv_filename = desktop_path
        
        save_commits_to_csv(commits, csv_filename)
        print(f"Commits have been saved to {csv_filename}")
        
        if os.name == 'posix':  
            os.system(f"open {csv_filename}")
        
        
        commit_map = create_commit_map(csv_filename)
        print("Commit map has been created")





