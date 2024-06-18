import praw

def scrape_reddit_comments(url):
    # Initialize praw with your credentials (create an app on Reddit to get these)
    reddit = praw.Reddit(
        client_id='your_client_id',
        client_secret='your_client_secret',
        user_agent='your_user_agent',
    )

    # Extract submission ID from the URL
    submission_id = url.split('/')[-3]

    # Fetch the submission (post) using its ID
    submission = reddit.submission(id=submission_id)

    # Load all comments recursively
    submission.comments.replace_more(limit=None)
    comments = submission.comments.list()

    # Extract and return all comment bodies
    comment_bodies = [comment.body for comment in comments]

    return comment_bodies

# Function to save comments to a file
def save_comments_to_file(comments, filename):
    with open(filename, 'w', encoding='utf-8') as file:
        for comment in comments:
            file.write(comment + '\n')

# Example usage:
if __name__ == "__main__":
    # Prompt user to input Reddit post URL
    reddit_url = input("Enter Reddit post URL: ").strip()

    # Call function to scrape comments
    comments = scrape_reddit_comments(reddit_url)
   
    # Print all comment bodies
    for comment in comments:
        print(comment)
   
    # Save comments to a file
    save_comments_to_file(comments, 'reddit_comments.txt')
    print(f"Comments saved to 'reddit_comments.txt'")