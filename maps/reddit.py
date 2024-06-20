import praw
import click
import os
import csv
import requests
import nomic
from itertools import islice
from nomic import atlas
from prawcore.exceptions import PrawcoreException
import time

# Function to get Reddit instance using provided credentials
def get_reddit_instance(client_id, client_secret, user_agent):
    reddit = praw.Reddit(
        client_id=client_id,
        client_secret=client_secret,
        user_agent=user_agent
    )
    return reddit

@click.command()
@click.option('--client-id', prompt='Enter your Reddit client ID', help='Reddit client ID')
@click.option('--client-secret', prompt='Enter your Reddit client secret', hide_input=True, help='Reddit client secret')
@click.option('--user-agent', prompt='Enter your Reddit user agent', help='Reddit user agent')
@click.option('--reddit-url', prompt='Enter Reddit post URL', help='URL of the Reddit post')
@click.option('--nomic-api-key', prompt='Enter your Nomic API', help='Nomic API key')
def main(client_id, client_secret, user_agent, reddit_url, nomic_api_key):
    # Step 1: Get Reddit instance
    reddit = get_reddit_instance(client_id, client_secret, user_agent)
    
    # Step 2: Scrape comments from Reddit
    submission_id = reddit_url.split('/')[-3]
    submission = reddit.submission(id=submission_id)
    comments = scrape_reddit_comments(reddit, submission)

    csv_filename = 'reddit_comments.csv'
    save_to_csv(comments, csv_filename)  
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
                                 description='Reddit comments mapped via automation.',
                                 topic_model=True
                                )
        if dataset and 'id' in dataset:
            print("Map created on Atlas with ID:", dataset['id'])
            print("All done! Visit the map link to see the status of your map build.")
        else:
            print("Map creation failed. Dataset ID not found in response.")
    except Exception as e:
        print(f"An error occurred while building map on Atlas: {e}")

# Function to scrape Reddit comments with retry on rate limit
def scrape_reddit_comments(reddit, submission):
    max_attempts = 5  # Maximum retry attempts
    current_attempt = 0
    while current_attempt < max_attempts:
        try:
            submission.comments.replace_more(limit=None)
            comments = fetch_all_comments(submission)
            print(f"Number of comments fetched: {len(comments)}")
            return comments
        except PrawcoreException as e:
            if e.response and e.response.status_code == 429:
                delay = 2 ** current_attempt  # Exponential backoff
                print(f"Rate limit exceeded. Retrying in {delay} seconds...")
                time.sleep(delay)
                current_attempt += 1
            else:
                print(f"Error scraping comments: {e}")
                return []
    
    print("Max retry attempts reached. Could not fetch comments.")
    return []

# Function to fetch all comments (modified to fit)
def fetch_all_comments(submission):
    comments = []
    submission.comments.replace_more(limit=None)
    for comment in submission.comments.list():
        comment_data = {
            'text': comment.body,
            'author': comment.author.name if comment.author else '[deleted]',
            'score': comment.score
        }
        comments.append(comment_data)
        comments.extend(fetch_replies(comment))
    return comments
# Function to fetch replies recursively (modified to fit)
def fetch_replies(comment):
    replies = []
    if isinstance(comment, praw.models.reddit.comment.Comment):
        if hasattr(comment, 'replies') and isinstance(comment.replies, praw.models.comment_forest.CommentForest):
            comment.replies.replace_more(limit=None)
            for reply in comment.replies.list():
                reply_data = {
                    'text': reply.body,
                    'author': reply.author.name if reply.author else '[deleted]',
                    'score': reply.score
                }
                replies.append(reply_data)
                replies.extend(fetch_replies(reply))
    return replies

# Function to save comments to CSV file (modified to fit)
def save_to_csv(comments, filename):
    unique_comments = {comment['text']: comment for comment in comments}.values()  # Ensure unique comments by text
    fieldnames = ['text', 'author', 'score']  # Define fieldnames
    with open(filename, 'w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(unique_comments)

# Function to upload CSV to Nomic (modified to fit)
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
                    writer.writerow(['text', 'author', 'score'])  # Write header
                    writer.writerows(chunk)
                
                with open(temp_filename, 'rb') as temp_file:
                    files = {'file': temp_file}
                    # Replace with actual API endpoint for Nomic upload if available
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

if __name__ == "__main__":
    main()
