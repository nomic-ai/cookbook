from nomic import atlas
import urllib.request, json

with urllib.request.urlopen("https://raw.githubusercontent.com/tloen/alpaca-lora/main/alpaca_data.json") as url:
    data = json.load(url)

project = atlas.map_text(data=data,
                         indexed_field='instruction',
                         name='Alpaca Training Data Instructions',
                         description='Alpaca Training Data Instructions Commit Hash: 26f64780ad7f18a6a0ec24be044f703b8d65d16f',
                         )

project = atlas.map_text(data=data,
                         indexed_field='output',
                         name='Alpaca Training Data Outputs',
                         description='Alpaca Training Data Outputs Commit Hash: 26f64780ad7f18a6a0ec24be044f703b8d65d16f',
                         )