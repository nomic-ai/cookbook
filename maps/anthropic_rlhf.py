from nomic import atlas
import numpy as np
from datasets import load_dataset

dataset = load_dataset('Anthropic/hh-rlhf')['train']

documents = [document for document in dataset]

project = atlas.map_text(data=documents,
                          indexed_field='chosen',
                          name='Anthropic RLHF',
                          description="What do people plan to finetune GPT's on?"
                          )
print(project.maps)
