import pymongo as pm
import pandas as pd
from pathlib import Path
from nomic import AtlasDataset, embed
import numpy as np

# Replace with your MongoDB connection string and certificate file path
client = pm.MongoClient(
    'mongodb+srv://<username>:<password>@cluster0.l3jhqfs.mongodb.net/testdb'
    '?authSource=%24external&authMechanism=MONGODB-X509&retryWrites=true&w=majority',
    tls=True,
    tlsCertificateKeyFile='mongocert.pem'
)

# Access or create MongoDB collection
db = client.testdb
collection = db.mongo_so

# Clear existing content in collection
collection.delete_many({})

# Load data into DataFrame
mongo_so = pd.read_parquet(Path.cwd() / 'data' / 'mongo-so.parquet')

# Initialize Nomic text embedding model
output = embed.text(
    texts=mongo_so['title'].tolist(),
    model='nomic-embed-text-v1.5',
    inference_mode='local',  # Use local inference
)

# Extract embeddings
title_embeds = output['embeddings']

# Assign embeddings to DataFrame
mongo_so['title_embedding'] = title_embeds

# Convert DataFrame to list of dictionaries for MongoDB insertion
data = mongo_so.to_dict(orient='records')

# Insert data into MongoDB collection
collection.insert_many(data)

# Initialize AtlasDataset for mapped data
dataset = AtlasDataset(
    "MongoDB_StackOverflow_Questions",
    unique_id_field="mongo_id",  # Replace with appropriate unique identifier field
    is_public=True,
)

# Retrieve all items from MongoDB collection
all_items = list(collection.find())

# Extract embeddings into numpy array
embs = np.array([d['title_embedding'] for d in all_items])

# Prepare items for AtlasDataset by converting _id to mongo_id and removing embeddings
for d in all_items:
    d['mongo_id'] = str(d['_id'])
    del d['title_embedding']
    del d['_id']

# Add data and embeddings to AtlasDataset
dataset.add_data(data=all_items, embeddings=embs)

# Create index in the dataset
index_options = {
    "indexed_field": "title",  # Replace with appropriate field for indexing
    "modality": "embedding",
    "topic_model": True,
    "duplicate_detection": True,
    "embedding_model": "nomic-embed-text-v1.5",  # Specify Nomic embedding model
}
dataset.create_index(**index_options)

# Print information about the AtlasDataset
print(dataset)
