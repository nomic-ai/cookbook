from nomic import atlas, atlastdataset
import pandas as pd

# Read the CSV file into a DataFrame
df = pd.read_csv('https://gist.githubusercontent.com/haljpeg/ba5a768257b76aa03c724c5be7558b12/raw/7693aeefbfd970da8c2f37c37f241ac559b2a4e7/substack_data.csv')

substacks = {}

# Iterate over each row in the DataFrame
for index, row in df.iterrows():
    substack_slug = row[0].split("//")[1].split(".")[0].strip()
    substack_url = row[0].strip()
    substack_name = str(row[5]).strip()

    # Extract posts from each row
    posts = []
    for i in range(2, 21, 4):  # Assuming posts are in columns 2, 6, 10, 14, 18
        post_url = row[i].strip()
        post_title = row[i + 1].strip() if not pd.isnull(row[i + 1]) else ''
        post_subtitle = row[i + 2].strip() if not pd.isnull(row[i + 2]) else ''

        if post_url:
            posts.append({
                'url': post_url,
                'title': post_title,
                'subtitle': post_subtitle
            })

    substacks[substack_slug] = {
        'name': substack_name,
        'url': substack_url,
        'posts': posts
    }

# Create documents for mapping
documents = []
id = 0
for item in substacks.values():
    posts = item.pop('posts')
    for post in posts:
        document = {**item, **post}
        document['text'] = f"{document['title']} \n {document['subtitle']}"
        document['id'] = id
        id += 1
        documents.append(document)

# Map text to Atlas
project = atlas.map_text(data=documents, id_field='id', indexed_field='text', name='Map of Substack', description='Map of substack posts.')

print(f"Documents mapped to project: {project}")
