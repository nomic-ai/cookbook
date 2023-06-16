import weaviate
from nomic import atlas
import numpy as np

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
    response = get_batch_with_cursor(client, c, p, 1000)
    count = 0
    cursor = response["data"]["Get"][c][-1]["_additional"]["id"]
    while True:
        temp = get_batch_with_cursor(client, c, p, 1000, cursor)
        count += 1
        if len(temp["data"]["Get"][c]) == 0:
            break
        cursor = temp["data"]["Get"][c][-1]["_additional"]["id"]
        response["data"]["Get"][c] += temp["data"]["Get"][c]

    vectors = []
    for i in response["data"]["Get"][c]:
        vectors.append(i["_additional"]["vector"])

    embeddings = np.array(vectors)
    data = []
    not_data = ["_additional", "vector", "id"]
    for i in response["data"]["Get"][c]:
        j = {key: value for key, value in i.items() if key not in not_data}
        data.append(j)

    if len(data) > 10000:
        project = atlas.map_embeddings(
            embeddings=embeddings[0:10000],
            data=data[0:10000],
            colorable_fields=p,
        )
        count = 10000
        while count < len(data):
            with project.wait_for_project_lock():
                project.add_embeddings(
                    embeddings=embeddings[count : count + min(len(data), 10000)],
                    data=data[count : count + min(len(data), 10000)],
                )
            count += 10000

    else:
        project = atlas.map_embeddings(
            embeddings=embeddings,
            data=data,
            colorable_fields=p,
        )
