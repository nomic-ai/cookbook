import pymongo as pm
import nomic
from nomic import AtlasDataset
from sentence_transformers import SentenceTransformer
from pymongo.mongo_client import MongoClient
import numpy as np
import pandas as pd
from pathlib import Path

# MongoDB connection string 
client = MongoClient('mongodb+srv://<USERNAME>:<PASSWORD>@<APPNAME>.1fy6rp1.mongodb.net/?appName=<APPNAME>',
                     tls=True)

# Replace with your actual API key
nomic.login('YOUR_KEY_HERE')

# MongoDB collection
collection = client.sample_mflix.comments

# Delete current content of collection
collection.delete_many({})

# Load embedding data into MongoDB from parquet file
mongo_so = pd.read_parquet(Path.cwd() / 'data' / 'mongo-so.parquet')

# Initialize SentenceTransformer model
model = SentenceTransformer('all-MiniLM-L6-v2')

# Encode titles using SentenceTransformer
title_embeds = model.encode(mongo_so['title'].tolist())
mongo_so['title_embedding'] = list(title_embeds)

# Convert DataFrame to list of dictionaries for MongoDB insertion
data = mongo_so.to_dict(orient='records')

# Insert data into MongoDB collection
collection.insert_many(data)

# Fetch all items from MongoDB collection
all_items = list(collection.find())

# Extract embeddings into numpy array
embs = np.array([d['title_embedding'] for d in all_items])

# Remove 'title_embedding' field from each item, and convert '_id' to string
for d in all_items:
    d['_id'] = str(d['_id'])
    del d['title_embedding']

# Create an AtlasDataset instance
dataset = AtlasDataset(
    identifier='sample-mflix-comments',  # Unique identifier for your dataset
    description='MongoDB Movie Comments',
    unique_id_field='_id',
    is_public=True
)

# Add data and embeddings to the AtlasDataset
dataset.add_data(data=all_items, embeddings=embs)

# Create an index and map
dataset.create_index(
    name='MongoDB Movie Comments',
    indexed_field='body',  # Replace with your topic label field
    modality='embedding',
    topic_model={
        'build_topic_model': True,
        'topic_label_field': 'body'  # Replace with the field used for topic labeling
    },
    duplicate_detection={
        'tag_duplicates': True,
        'duplicate_cutoff': 0.95  # Adjust as needed
    },
    projection={
        'n_neighbors': 15,  # Example value, adjust as needed
        'n_epochs': 100,  # Example value, adjust as needed
        'model': 'nomic-project-v2',
        'local_neighborhood_size': 30,
        'spread': 1.0,
        'rho': 0.5
    },
    embedding_model='NomicEmbed'  # Specify the embedding model if needed
)

# Print the dataset to confirm
print(dataset)
