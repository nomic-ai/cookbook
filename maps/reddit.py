import praw
import csv
import requests
import os
from itertools import islice
from prawcore.exceptions import PrawcoreException
from nomic import atlas
import modal

app = modal.App("reddit-comments-app")

# Function to scrape Reddit comments with pagination handling
@app.function()
def scrape_reddit_comments(url):
    reddit = praw.Reddit(client_id='g1B_Pdsfwszzw5xbUf3i3g',
                         client_secret='kZWNzy2Jje3gT32CHJrtf8p1Xdczow',
                         user_agent='test-script/1.0 by ak-gom')
    
    submission_id = url.split('/')[-3]
    submission = reddit.submission(id=submission_id)
    
    try:
        submission.comments.replace_more(limit=None)
    except PrawcoreException as e:
        print(f"Error replacing more comments: {e}")
        return []
    
    comments = fetch_all_comments(submission)
    print(f"Number of comments fetched: {len(comments)}")
    
    return comments

# Recursive function to fetch all comments
def fetch_all_comments(submission):
    comments = []
    submission.comments.replace_more(limit=None)
    for comment in submission.comments.list():
        comments.append(comment.body)
        comments.extend(fetch_replies(comment))
    return comments

# Function to fetch replies recursively
def fetch_replies(comment):
    replies = []
    if isinstance(comment, praw.models.reddit.comment.Comment):
        if hasattr(comment, 'replies') and isinstance(comment.replies, praw.models.comment_forest.CommentForest):
            comment.replies.replace_more(limit=None)
            for reply in comment.replies.list():
                replies.append(reply.body)
                replies.extend(fetch_replies(reply))
    return replies

# Function to save comments to CSV file in dataset format
@app.function()
def save_to_csv(comments, filename):
    with open(filename, 'w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=['text'])  # Specify fieldnames for the CSV
        writer.writeheader()  # Write header
        for comment in comments:
            writer.writerow({'text': comment})  # Write each comment as a dictionary with 'text' key

# Function to upload CSV to Nomic in chunks
@app.function()
def upload_to_nomic(csv_filename, nomic_api_key):
    headers = {
        'Authorization': f'Bearer {nomic_api_key}',
    }
    try:
        with open(csv_filename, 'r', encoding='utf-8') as file:
            reader = csv.reader(file)
            next(reader)  # Skip header
            
            chunk_size = 1000  # Adjust chunk size as needed
            chunk_number = 1
            while True:
                chunk = list(islice(reader, chunk_size))
                if not chunk:
                    break
                
                temp_filename = f'temp_chunk_{chunk_number}.csv'
                with open(temp_filename, 'w', newline='', encoding='utf-8') as temp_file:
                    writer = csv.writer(temp_file)
                    writer.writerow(['text'])
                    writer.writerows(chunk)
                
                with open(temp_filename, 'rb') as temp_file:
                    files = {'file': temp_file}
                    response = requests.post(url, headers=headers, files=files)
                    
                    # Check response status
                    if response.status_code == 200:
                        print(f"Uploaded chunk {chunk_number} successfully.")
                    else:
                        print(f"Failed to upload chunk {chunk_number}. Status code: {response.status_code}")
                        return None  # Exit if upload fails
                    
                chunk_number += 1
                os.remove(temp_filename)
            
            print("All chunks uploaded successfully.")
            return "All chunks uploaded successfully."
    
    except IOError as e:
        print(f"Error opening or reading file '{csv_filename}': {e}")
        return None
    except Exception as e:
        print(f"An error occurred during upload to Nomic: {e}")
        return None

def main():
    try:
        # Step 0: Log into Nomic with API token
        nomic_api_key = input("Enter your Nomic API: ")
        
        # Step 1: Scrape comments from Reddit
        reddit_url = input("Enter Reddit post URL: ").strip()
        comments = scrape_reddit_comments.remote(reddit_url)
        
        # Step 2: Save comments to CSV file
        csv_filename = 'reddit_comments.csv'
        save_to_csv.remote(comments, csv_filename)
        print(f"Comments saved to '{csv_filename}'")
        
        # Step 3: Read CSV and format data for Atlas
        my_data = []
        with open(csv_filename, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                my_data.append(row)
        
        # Step 4: Build a map on Atlas
        try:
            dataset = atlas.map_data(data=my_data,
                                     indexed_field='text',
                                     description='Reddit comments mapped via automation.'
                                    )
            if dataset and 'id' in dataset:
                print("Map created on Atlas with ID:", dataset['id'])
                print("All done! Visit the map link to see the status of your map build.")
            else:
                print("Map creation failed. Dataset ID not found in response.")
        except Exception as e:
            print(f"An error occurred while building map on Atlas: {e}")
    
    except Exception as e:
        print("An error occurred:", e)

if __name__ == "__main__":
    main()
