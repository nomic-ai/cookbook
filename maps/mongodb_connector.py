import pymongo as pm
from nomic import atlas
from sentence_transformers import SentenceTransformer
import numpy as np
import pandas as pd
from pathlib import Path

# Replace with your MongoDB connection string and certificate file path
client = pm.MongoClient('mongodb+srv://<username>:<password>@cluster0.l3jhqfs.mongodb.net/testdb'
                        '?authSource=%24external&authMechanism=MONGODB-X509&retryWrites=true&w=majority',
                        tls=True,
                        tlsCertificateKeyFile='mongocert.pem')

collection = client.testdb.testcoll

# Delete current content of collection
collection.delete_many({})

# Load embedding data into MongoDB
mongo_so = pd.read_parquet(Path.cwd() / 'data' / 'mongo-so.parquet')

# Initialize SentenceTransformer model
model = SentenceTransformer('all-MiniLM-L6-v2')

# Encode titles into embeddings
title_embeds = model.encode(mongo_so['title'].tolist())

# Assign embeddings to DataFrame
mso_te = mongo_so.assign(title_embedding=list(title_embeds))

# Convert DataFrame to list of dictionaries for MongoDB insertion
data = mso_te.to_dict(orient='records')
for d in data:
    del d['Index']
    d['title_embedding'] = d['title_embedding'].tolist()

# Insert data into MongoDB collection
collection.insert_many(data)

# Read MongoDB collection with embeddings and map it using AtlasProject
project = AtlasProject(
    name='MongoDB Stack Overflow Questions',
    unique_id_field='mongo_id',
    reset_project_if_exists=True,
    is_public=True,
    modality='embedding',
)

# Retrieve all items from MongoDB collection
all_items = list(collection.find())

# Extract embeddings into numpy array
embs = np.array([d['title_embedding'] for d in all_items])

# Prepare items for AtlasProject by converting _id to mongo_id and removing embeddings
for d in all_items:
    d['mongo_id'] = str(d['_id'])
    del d['title_embedding']
    del d['_id']

# Add embeddings to AtlasProject
project.add_embeddings(all_items, embs)

# Rebuild maps and create index for topic modeling
project.rebuild_maps()
project.create_index(
    name='MongoDB Stack Overflow Questions',
    topic_label_field='body',  # Replace with appropriate field for topic modeling
    build_topic_model=True,
)

# Print information about the AtlasProject
print(project)
