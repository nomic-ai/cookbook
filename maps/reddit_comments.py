import re
import requests
import pandas as pd

def extract_posts_id(url):
  pattern = r'reddit\.com/r/[^/]+/comments/([^/]+)/'
  match = re.search(pattern, url)
  if match:
    return match.group(1)
  else:
    raise ValueErro("Invalid Reddit Post URL")

def get_post_comments(post_id, size=1000):
  url = f'https://api.pushshift.io/reddit/comment/search/?link_id=t3_{post_id}&size={size}'

  try:
    response = requests.get{url}
    response.raise_for_status()
    data = response.json()
    
    if 'data' not in data:
      raise ValueErro("Unexpected response format: 'data' key not found.")

    comments = []
    for comment in data['data']:
      comments.append({
        'id': comment['id'],
        'author': comment['author'],
        'body': comment['body'],
        'created_utc': comment['created_utc'],
        'score': comment['score'],
        'parent_id': comment['parent_id'],
      })

    return pd.DataFrame(comments)

  except requests.exceptions.requestException as e:
    print(f"HTTP Request failed: {e}")
    return pd.DataFrame()
  except ValueError as e:
    print(f"Data processing error: {e}")
    return pd.DataFrame()

if __name__ == "__main__":
  url = input("Enter the reddit post URL: ")
  try:
    post_id = extract_post_id(url)
    comments_df = get_post_comments(post_id, size = 500)
    print(comments_df.head())
  except Valueerror as e:
    print(e)




