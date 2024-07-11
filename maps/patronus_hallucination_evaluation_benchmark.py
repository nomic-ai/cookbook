from nomic import atlas
from datasets import load_dataset

hf_dataset = load_dataset("PatronusAI/halubench")


dataset = atlas.map_data(
    identifier='patronus-ai/halubench',
    data=hf_dataset['test'].to_pandas(),
    is_public=True,
    id_field='id',
    indexed_field='answer'
)
