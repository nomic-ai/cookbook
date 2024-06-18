import praw
import numpy as np
import json
import requests

def scrape_reddit_comments(url):
    reddit = praw.Reddit(client_id='g1B_Pdsfwszzw5xbUf3i3g',
                     client_secret='kZWNzy2Jje3gT32CHJrtf8p1Xdczow',
                     user_agent='test-script/1.0 by ak-gom')
    submission_id = url.split('/')[-3]
    submission = reddit.submission(id=submission_id)
    submission.comments.replace_more(limit=None)
    comments = submission.comments.list()
    comment_bodies = [comment.body for comment in comments]
    return comment_bodies

def create_embeddings(comments):
    num_comments = len(comments)
    embeddings = np.random.rand(num_comments, 256)
    return embeddings

# Function to save comments and embeddings to a JSONL file
def save_to_jsonl(comments, embeddings, filename):
    with open(filename, 'w', encoding='utf-8') as file:
        for comment, embedding in zip(comments, embeddings):
            data = {
                "comment": comment,
                "embedding": embedding.tolist() 
                }
            file.write(json.dumps(data) + '\n')

# Function to upload data to Nomic
def upload_to_nomic(jsonl_filename, nomic_api_key):
    headers = {
        'Authorization': f'Bearer {nomic_api_key}',
        'Content-Type': 'application/json',
        }
    url = 'https://atlas-next-prod.vercel.app/data/akanksha/org/new-project'
    
    with open(jsonl_filename, 'rb') as file:
        files = {
            'file': file
            }
        response = requests.post(url, headers=headers, files=files)
        return response.json()

# Main function to scrape comments and upload data to Nomic
def main():
    try:
        reddit_url = input("Enter Reddit post URL: ").strip()
        comments = scrape_reddit_comments(reddit_url)
        embeddings = create_embeddings(comments)
        jsonl_filename = 'reddit_comments.jsonl'
        save_to_jsonl(comments, embeddings, jsonl_filename)
        print(f"Comments and embeddings saved to '{jsonl_filename}'")
        
        nomic_api_key = 'nk-EqTA74FbBQug8an8wY4libvZX5wVkZ7pCCa36n4vOvU'
        
        response = upload_to_nomic(jsonl_filename, nomic_api_key)
        print("Map created on Nomic with ID:", response['id'])
    except KeyboardInterrupt:
        print("\nOperation aborted.")

if __name__ == "__main__":
    main()