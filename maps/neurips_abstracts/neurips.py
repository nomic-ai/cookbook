from nomic import AtlasClient
import jsonlines

atlas = AtlasClient()

documents = []
with jsonlines.open('maps/neurips_abstracts/neurips_87_21.jsonl') as reader:
    for idx, obj in enumerate(reader):
        obj['year'] = float(obj['year'])
        obj['id'] = str(idx)

        for key in list(obj.keys()):
            if not obj[key]:
                obj[key] = 'N/A'
            if key not in ['abstract', 'affiliations', 'authors', 'id', 'last_author', 'last_author_affiliation', 'link', 'title', 'year']:
                obj.pop(key)
        documents.append(obj)


response = atlas.map_text(data=documents,
                          indexed_field='abstract',
                          id_field='id',
                          is_public=True,
                          map_name='NeurIPS Proceedings 1987-2021',
                          map_description='All NeurIPS proceedings up to 2021 organized by abstract text.',
                          colorable_fields=['year'],
                          num_workers=10,
                          build_topic_model=True,
                          reset_project_if_exists=True)
print(response)
