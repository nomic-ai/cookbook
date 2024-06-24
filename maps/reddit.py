import praw
import click
import pandas as pd
import pyarrow as pa
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
    
    # Convert comments to Apache Arrow table
    arrow_table = comments_to_arrow_table(comments)
    
    try:
        dataset = atlas.map_data(data=arrow_table,
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

def comments_to_arrow_table(comments):
    # Convert comments list to Pandas DataFrame
    df = pd.DataFrame(comments)
    
    # Convert Pandas DataFrame to Apache Arrow table
    arrow_table = pa.Table.from_pandas(df)
    
    return arrow_table

if __name__ == "__main__":
    main()
