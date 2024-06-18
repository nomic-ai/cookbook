#Abhi Somala
#06.18.2024
#Atlas Developer Advocate Training: https://www.notion.so/nomic-ai/Atlas-Developer-Advocation-a08d32223bf54ef0aabfadb97d0d71a7
#Github Commits - Given a url to a github repository, automatic create an AtlasDataset and AtlasMap of all commit messages to the repository.
import csv
import os
import requests
from pathlib import Path
from nomic import AtlasDataset

def getCommits(repoURL):
    # Gets the owner and repo from the URL
    parts = repoURL.rstrip('/').split('/')
    owner = parts[-2]
    repo = parts[-1]

    # Grabs info from general github template
    apiURL = f"https://api.github.com/repos/{owner}/{repo}/commits"

    # Requests to GitHub API
    response = requests.get(apiURL)
    
    # Makes sure it can get to the page successfully
    if response.status_code == 200:
        commits = response.json()
        return commits
    else: # Friendly output in case of error
        print(f"Failed to fetch commits: {response.status_code}")
        return None

def csvCommmit(commits, cvsName):
    with open(cvsName, 'w', newline='') as csvfile:
        fieldnames = ['id', 'message']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        for i, commit in enumerate(commits):
            writer.writerow({'id': i % 100000000, 'message': commit['commit']['message']})

def mapMaker(cvsName):
    # Read the CSV file and prepare data for AtlasDataset
    data = []
    with open(cvsName, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            data.append({'id': row['id'], 'text': row['message']})

    # Create AtlasDataset and adds data to created dataset
    dataset = AtlasDataset(
        "github-commit-dataset",
        unique_id_field="id",
    )

    dataset.add_data(data=data)

    # Creates the map
    map = dataset.create_index(
        indexed_field='text',
        topic_model=True,
        duplicate_detection=True,
        projection=None,
        embedding_model='NomicEmbed'
    )

    return map

if __name__ == "__main__":
    repoURL = input("URL of Github Repository: ")
    
    commits = getCommits(repoURL)
    if commits:
        # Get the path to the desktop
        desktop_path = str(Path.home() / "Desktop" / "commits.csv")
        cvsName = desktop_path
        
        #Calls the 'csvCommit' function which creates the csv file with the github commit comments
        csvCommmit(commits, cvsName)
        print(f"Commits have been saved to {cvsName}")
        
        # Opens the file created
        os.system(f"open {cvsName}")
        
        # Creates a map using the saved commit data
        commit_map = mapMaker(cvsName)
        print("Commit map has been created")
