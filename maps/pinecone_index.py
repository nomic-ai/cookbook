"""
Visualizing your pinecone vector database index in Atlas
"""
import pinecone
import numpy as np
from nomic import atlas
import nomic
pinecone.init(api_key='YOUR PINECONE API KEY', environment='us-east1-gcp')
nomic.login('YOUR NOMIC API KEY')

#create and insert embeddings into your pinecone index
pinecone.create_index("quickstart", dimension=128, metric="euclidean", pod_type="p1")

index = pinecone.Index("quickstart")

num_embeddings = 999
embeddings_for_pinecone = np.random.rand(num_embeddings, 128)
index.upsert([(str(i), embeddings_for_pinecone[i].tolist()) for i in range(num_embeddings)])

#now pull the embeddings out of pinecone by id
vectors = index.fetch(ids=[str(i) for i in range(num_embeddings)])

ids = []
embeddings = []
for id, vector in vectors['vectors'].items():
    ids.append(id)
    embeddings.append(vector['values'])

embeddings = np.array(embeddings)

atlas.map_embeddings(embeddings=embeddings, data=[{'id': id} for id in ids], id_field='id')
