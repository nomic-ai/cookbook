import weaviate
from nomic import AtlasDataset
import numpy as np
import nomic

nomic.login("YOUR NOMIC API KEY")

client = weaviate.Client(
    url="WEAVIATE DATABASE URL",
)

schema = client.schema.get()

classes = []
props = []
for c in schema["classes"]:
    classes.append(c["class"])
    temp = []
    for p in c["properties"]:
        if p["dataType"] == ["text"]:
            temp.append(p["name"])
    props.append(temp)


def get_batch_with_cursor(
    client, class_name, class_properties, batch_size, cursor=None
):
    query = (
        client.query.get(class_name, class_properties)
        .with_additional(["vector", "id"])
        .with_limit(batch_size)
    )

    if cursor is not None:
        return query.with_after(cursor).do()
    else:
        return query.do()


for c, p in zip(classes, props):
    dataset = AtlasDataset(identifier=c, unique_id_field="id")  # Initialize AtlasDataset

    count = 0
    cursor = None
    while True:
        response = get_batch_with_cursor(client, c, p, 10000, cursor)
        count += 1
        if len(response["data"]["Get"][c]) == 0:
            break
        cursor = response["data"]["Get"][c][-1]["_additional"]["id"]
        vectors = []
        data = []
        for i in response["data"]["Get"][c]:
            vectors.append(i["_additional"]["vector"])

            metadata = {key: value for key, value in i.items() if key != "_additional"}
            data.append(metadata)

        embeddings = np.array(vectors)
        
        # Add data to the dataset
        dataset.add_data(data=data, embeddings=embeddings)

    # Create index in the dataset
    index_options = {
        "indexed_field": p,
        "modality": "embedding",
        "topic_model": True,
        "duplicate_detection": True,
        "embedding_model": "NomicEmbed",
    }
    dataset.create_index(name=c, **index_options)
