import praw
import click
import os
import csv
import requests
from itertools import islice
from nomic import atlas
from prawcore.exceptions import PrawcoreException
import time

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
    reddit = get_reddit_instance(client_id, client_secret, user_agent)
    
    submission_id = reddit_url.split('/')[-3]
    submission = reddit.submission(id=submission_id)
    comments = scrape_reddit_comments(reddit, submission)

    csv_filename = 'reddit_comments.csv'
    save_to_csv(comments, csv_filename)  
    print(f"Comments saved to '{csv_filename}'")
        
    my_data = []
    with open(csv_filename, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            my_data.append(row)
    
    print(f"Number of comments saved: {len(my_data)}")  # Debugging print
    
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

def scrape_reddit_comments(reddit, submission):
    max_attempts = 5  
    current_attempt = 0
    while current_attempt < max_attempts:
        try:
            submission.comments.replace_more(limit=None)
            comments = fetch_all_comments(submission)
            print(f"Number of comments fetched: {len(comments)}")
            return comments
        except PrawcoreException as e:
            if e.response and e.response.status_code == 429:
                delay = 2 ** current_attempt  
                print(f"Rate limit exceeded. Retrying in {delay} seconds...")
                time.sleep(delay)
                current_attempt += 1
            else:
                print(f"Error scraping comments: {e}")
                return []
    
    print("Max retry attempts reached. Could not fetch comments.")
    return []


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


def save_to_csv(comments, filename):
    unique_comments = {comment['text']: comment for comment in comments}.values()  
    fieldnames = ['text', 'author', 'score']  
    with open(filename, 'w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(unique_comments)


if __name__ == "__main__":
    main()
