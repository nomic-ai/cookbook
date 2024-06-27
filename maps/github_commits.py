import csv
import os
import subprocess
from pathlib import Path
from datetime import datetime
from nomic import AtlasDataset
import tempfile


# Clones repo
def clone_repo(repo_url, repo_path):
    if not os.path.exists(repo_path):
        subprocess.run(['git', 'clone', '--mirror', repo_url, repo_path])
    else:
        subprocess.run(['git', '-C', repo_path, 'fetch', '--all'])

# Gets commit messages and metadata along with it
def fetch_commits_from_local_repo(repo_path):
    commit_list = []
    result = subprocess.run(
        ['git', '-C', repo_path, 'log', '--format=%H;%an;%ae;%ad;%s'],
        capture_output=True,
        text=True,
        encoding='latin1',
    )
    commits = result.stdout.strip().split('\n')
    for i, commit in enumerate(commits, start=1):
        try:
            hash, author, email, date, message = commit.split(';', 4)
            # Formats date so it can be filtered
            date_obj = datetime.strptime(date, '%a %b %d %H:%M:%S %Y %z')
            formatted_date = date_obj.strftime('%Y-%m-%d')
            commit_list.append({
                'id': i,
                'hash': hash,
                'author': author,
                'email': email,
                'date': formatted_date,
                'message': message
            })
        except ValueError as e:
            print(f"ValueError occurred on commit {i}: {e}. Skipping this commit.")
    return commit_list

# Saves commits to a CSV file
def save_commits_to_csv(commits, csv_filename):
    with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['id', 'hash', 'author', 'email', 'date', 'message']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for commit in commits:
            writer.writerow(commit)

# Creates map from a list of commits
def create_commit_map_from_commits(commits, map_name):
    if not commits:
        raise ValueError("No commits found.")

    dataset = AtlasDataset(
        map_name,
        unique_id_field="id",
    )
    dataset.add_data(data=commits)

    map = dataset.create_index(
         # Indexes by message
        indexed_field='message', 
        topic_model=True,
        embedding_model='NomicEmbed'
    )

    return map

# Creates map from a CSV file
def create_commit_map_from_csv(csv_filename, map_name):
    data = []
    with open(csv_filename, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            data.append(row)  

    if not data:
        raise ValueError("No data found in CSV file.")

    dataset = AtlasDataset(
        map_name,
        unique_id_field="id",
    )
    dataset.add_data(data=data)

    map = dataset.create_index(
        # Indexes by message
        indexed_field='message',  
        topic_model=True,
        embedding_model='NomicEmbed'
    )

    return map

if __name__ == "__main__":
    repo_urls = input("Enter GitHub Repository URLs separated by commas: ").split(',')
    #Optional choice to make it a csv file
    save_to_csv = input("Do you want to save commits to CSV? (yes/no): ").strip().lower() == 'yes' 
    all_commits = [] 
    repo_names = [] 

    # Create a temp directory
    with tempfile.TemporaryDirectory() as temp_dir:
        for repo_url in repo_urls:
             # Grabs info from git repo to make map name
            repo_name = repo_url.rstrip('/').split('/')[-1].strip() 
            repo_names.append(repo_name)
            repo_path = os.path.join(temp_dir, repo_name)

            clone_repo(repo_url.strip(), repo_path)
            commits = fetch_commits_from_local_repo(repo_path)

            if commits:
                all_commits.extend(commits)

        if all_commits:
            # Combines repo names with underscores
            combined_repo_names = '_'.join(repo_names)  

            if save_to_csv:
                csv_filename = os.path.join(temp_dir, f"{combined_repo_names}_commits.csv")
                save_commits_to_csv(all_commits, csv_filename)
                print(f"Combined commits have been saved to {csv_filename}")

                map_name = os.path.splitext(os.path.basename(csv_filename))[0]
                try:
                    commit_map = create_commit_map_from_csv(csv_filename, map_name)
                    print(f"Commit map '{map_name}' has been created")
                except ValueError as e:
                    print(f"Error creating commit map: {e}")
            else:
                map_name = combined_repo_names
                try:
                    commit_map = create_commit_map_from_commits(all_commits, map_name)
                    print(f"Commit map '{map_name}' has been created")
                except ValueError as e:
                    print(f"Error creating commit map: {e}")
        else:
            print("No commits were found for the provided repositories.")



