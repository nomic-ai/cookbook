from nomic import atlas
from datasets import load_dataset

hf_dataset = load_dataset("PatronusAI/hallucination-evaluation-benchmark")


dataset = atlas.map_data(
    identifier='patronus-ai/hallucination-evaluation-benchmark',
    data=hf_dataset['test'].to_pandas(),
    is_public=False,
    id_field='id',
    indexed_field='answer'
)
