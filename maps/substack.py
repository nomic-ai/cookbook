from nomic import atlas, AtlasProject
import pandas as pd
df = pd.read_csv('https://gist.githubusercontent.com/haljpeg/ba5a768257b76aa03c724c5be7558b12/raw/7693aeefbfd970da8c2f37c37f241ac559b2a4e7/substack_data.csv')

substacks = {}

for index, row in df.iterrows():
    substack_slug = row[0].split("//")[1].split(".")[0].strip()
    substack_url = row[0].strip()
    substack_name = str(row[5]).strip()

    post1_url, post1_title, post1_subtitle = row[2], row[3], row[4]

    post2_url, post2_title, post2_subtitle = row[6], row[7], row[8]

    post3_url, post3_title, post3_subtitle = row[10], row[11], row[12]

    post4_url, post4_title, post4_subtitle = row[14], row[15], row[16]

    post5_url, post5_title, post5_subtitle = row[18], row[19], row[20]

    # check if post1_url is not null
    # add all posts in the list of dictionaries
    posts = []
    if not pd.isnull(post1_url):
        posts.append({
            'url': post1_url.strip(),
            'title': post1_title.strip() if not pd.isnull(post1_title) else '',
            'subtitle': post1_subtitle.strip() if not pd.isnull(post1_subtitle) else ''
        })
    if not pd.isnull(post2_url):
        posts.append({
            'url': post2_url.strip(),
            'title': post2_title.strip() if not pd.isnull(post2_title) else '',
            'subtitle': post2_subtitle.strip() if not pd.isnull(post2_subtitle) else ''
        })
    if not pd.isnull(post3_url):
        posts.append({
            'url': post3_url.strip(),
            'title': post3_title.strip() if not pd.isnull(post3_title) else '',
            'subtitle': post3_subtitle.strip() if not pd.isnull(post3_subtitle) else ''
        })
    if not pd.isnull(post4_url):
        posts.append({
            'url': post4_url.strip(),
            'title': post4_title.strip() if not pd.isnull(post4_title) else '',
            'subtitle': post4_subtitle.strip() if not pd.isnull(post4_subtitle) else ''
        })
    if not pd.isnull(post5_url):
        posts.append({
            'url': post5_url.strip(),
            'title': post5_title.strip() if not pd.isnull(post5_title) else '',
            'subtitle': post5_subtitle.strip() if not pd.isnull(post5_subtitle) else ''
        })

    substacks[substack_slug] = {
        'name': substack_name,
        'url': substack_url,
        'posts': posts
    }

print(len(list(substacks.keys())))

documents = []
for item in substacks.values():
    posts = item.pop('posts')
    for post in posts:
        document = {**item, **post}
        documents.append(document)


project = atlas.map_text(data=documents, indexed_field='title', name='Substack', description='Map of substack posts.')

