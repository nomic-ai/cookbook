import pymongo as pm
from nomic import AtlasProject
from sentence_transformers import SentenceTransformer
import numpy as np
import pandas as pd
from pathlib import Path
import nomic

# replace with your mongodb connect string / cert
client = pm.MongoClient('mongodb+srv://cluster0.l3jhqfs.mongodb.net/'
                        '?authSource=%24external&authMechanism=MONGODB-X509&retryWrites=true&w=majority',
                        tls=True,
                        tlsCertificateKeyFile='mongocert.pem')

collection = client.testdb.testcoll

# Delete current content of collection
collection.delete_many({})

# Load embedding data into mongodb
mongo_so = pd.read_parquet(Path.cwd() / 'data' / 'mongo-so.parquet')
model = SentenceTransformer('all-MiniLM-L6-v2')
title_embeds = model.encode(mongo_so['title'])
mso_te = mongo_so.assign(title_embedding=list(title_embeds))

data = list(r._asdict() for r in mso_te.itertuples())
for d in data:
    del d['Index']
    d['title_embedding'] = d['title_embedding'].tolist()
data[0]
collection.insert_many(data)

# Read a mongodb collection with embeddings in it and map it:
project = AtlasProject(
    name='MongoDB Stack Overflow Questions',
    unique_id_field='mongo_id',
    reset_project_if_exists=True,
    is_public=True,
    modality='embedding',
)

all_items = list(collection.find())
embs = np.array([d['title_embedding'] for d in all_items])
for d in all_items:
    d['mongo_id'] = str(d['_id'])
    del d['title_embedding']
    del d['_id']

project.add_embeddings(all_items, embs)

project.rebuild_maps()
project.create_index(
    name='MongoDB Stack Overflow Questions',
    topic_label_field='body',
    build_topic_model=True,
)

print(project)
