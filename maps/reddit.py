import praw
import csv
import requests
import os
import nomic
from itertools import islice
from nomic import atlas
from prawcore.exceptions import PrawcoreException

# Function to scrape Reddit comments with pagination handling
def scrape_reddit_comments(url):
    reddit = praw.Reddit(
        client_id='g1B_Pdsfwszzw5xbUf3i3g',
        client_secret='kZWNzy2Jje3gT32CHJrtf8p1Xdczow',
        user_agent='test-script/1.0 by ak-gom'
    )
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

# Function to save comments to CSV file
def save_to_csv(comments, filename):
    with open(filename, 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(['text'])  # Write header
        for comment in comments:
            writer.writerow([comment])

# Function to upload CSV to Nomic in chunks
def upload_to_nomic(csv_filename, nomic_api_key):
    url = 'https://atlas-next-prod.vercel.app/data/akanksha/my-second-map'
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
        nomic_api_key = 'nk-ffr2ynLSry7yzuot4AEaEGJdUW8Sc7YCk2Cc87yKdn0'
        
        # Step 1: Scrape comments from Reddit
        reddit_url = input("Enter Reddit post URL: ").strip()
        comments = scrape_reddit_comments(reddit_url)
        
        # Step 2: Save comments to CSV file
        csv_filename = 'reddit_comments.csv'
        save_to_csv(comments, csv_filename)
        print(f"Comments saved to '{csv_filename}'")
        
        # Step 3: Upload data to Nomic
        response_text = upload_to_nomic(csv_filename, nomic_api_key)
        
        if response_text is not None:
            print("Response from Nomic:", response_text)  # Debug print response
            # Example: response_data = parse_response(response_text)
            # Step 4: Convert response to list of dicts (assuming CSV data)
            try:
                response_lines = response_text.strip().split('\n')
                response_data = [{'text': line} for line in response_lines]
            except Exception as e:
                print(f"Error converting Nomic response to list of dicts: {e}")
                return
            
            # Step 5: Build a map on Atlas
            try:
                dataset = atlas.map_data(data=response_data,
                                         indexed_field='text',
                                         identifier='akanksha/my-test3-map',  # Adjust identifier if needed
                                         description='Reddit comments mapped via automation.'
                                        )
                if 'id' in dataset.maps[0]:
                    print("Map created on Atlas with ID:", dataset.maps[0]['id'])
                    print("All done! Visit the map link to see the status of your map build.")
                else:
                    print("Map creation failed. Dataset ID not found in response.")
            except Exception as e:
                print(f"An error occurred while building map on Atlas: {e}")
        
    except Exception as e:
        print("An error occurred:", e)

if __name__ == "__main__":
    main()
