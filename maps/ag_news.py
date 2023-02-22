from nomic import atlas
import pandas

news_articles = pandas.read_csv('https://raw.githubusercontent.com/nomic-ai/maps/main/data/ag_news_25k.csv').to_dict('records')

project = atlas.map_text(data=news_articles,
                         indexed_field='text',
                         id_field='id',
                         name='News Articles 25k',
                         description='25k News articles.',
                         colorable_fields=['label'],
                         )