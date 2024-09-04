"""
Generates a table with the following columns from a Gong export:

call_id, call_url, call_start_time, call_duration, call_title
utterance, speaker_name, speaker_email, speaker_affiliation, percentage_into_call

"""
import os, requests, jsonlines, csv

GONG_ACCESS_KEY = 'L266QYQI3TM3HU7J4XBDWUFDOTHAXO5P'
GONG_ACCESS_KEY_SECRET = os.environ['GONG_ACCESS_KEY_SECRET']

GONG_API_PATH = 'https://us-71666.api.gong.io'



def get_all_call_transcripts():
    print("Extracting all historical call transcripts from Gong.")
    all_call_transcripts = []
    cursor = None
    while True:

        body = {'filter':{}}
        if cursor:
            body = {'cursor':cursor, **body}
        response = requests.post(GONG_API_PATH + '/v2/calls/transcript',
                                 json=body,
                                 headers={'Content-type': 'application/json'},
                                 auth=(GONG_ACCESS_KEY, GONG_ACCESS_KEY_SECRET)
                                 )
        assert response.status_code == 200
        response = response.json()
        cursor = response['records'].get('cursor', None)
        all_call_transcripts += response['callTranscripts']

        if cursor is None:
            break

    return all_call_transcripts


def get_all_calls():
    print("Extracting all historical calls from Gong.")
    all_calls = []
    cursor = None
    while True:
        body = {'filter':{}, 'contentSelector': {"exposedFields": {'parties': True}}}
        if cursor:
            body = {'cursor':cursor, **body}
        response = requests.post(GONG_API_PATH + f'/v2/calls/extensive',
                                 json=body,
                                 headers={'Content-type': 'application/json'},
                                 auth=(GONG_ACCESS_KEY, GONG_ACCESS_KEY_SECRET)
                                 )
        print(response.json())
        assert response.status_code == 200
        response = response.json()
        cursor = response['records'].get('cursor', None)
        all_calls += response['calls']
        if cursor is None:
            break

    return all_calls

def get_all_gong_users():
    print("Extracting all users from Gong.")
    all_users = []
    cursor = None
    while True:
        query_params="?"
        if cursor:
            query_params+=f'cursor={cursor}'
        response = requests.get(GONG_API_PATH + f'/v2/users{query_params}',
                                 headers={'Content-type': 'application/json'},
                                 auth=(GONG_ACCESS_KEY, GONG_ACCESS_KEY_SECRET)
                                 )
        assert response.status_code == 200
        response = response.json()
        cursor = response['records'].get('cursor', None)
        all_users += response['users']
        if cursor is None:
            break

    return all_users

def prepare_utterance_dataset(call_transcripts):

    utterance_level = []
    for call in call_transcripts:
        call_id = call['callId']

        call_utterances = []
        call_topics = set()

        for utterance in call['transcript']:
            speaker_id = utterance['speakerId']
            topic = utterance['topic']
            utterance_text = "\n".join([sentence['text'] for sentence in utterance['sentences']])

            # print(utterance)
            utterance_start = utterance['sentences'][0]['start']
            utterance_end = utterance['sentences'][-1]['end']

            # print(utterance_start, utterance_end)
            if topic:
                call_topics.add(topic)
            call_utterances.append({
                'call_id': call_id,
                'speaker_id': speaker_id,
                'utterance_topic': topic,
                'utterance': utterance_text,
                'utterance_start': utterance_start,
                'utterence_end': utterance_end
            })

        if call_utterances:
            # normalize utterance timestamps by
            max = call_utterances[-1]['utterence_end']
            for item in call_utterances:
                item['utterance_start'] = item['utterance_start'] / max
                item['utterence_end'] = item['utterence_end'] / max

            utterance_level += call_utterances

    return utterance_level


#cache all call transcripts
if os.path.exists('all_call_transcripts.jsonl'):
    all_call_transcripts = []
    with jsonlines.open('all_call_transcripts.jsonl') as reader:
        for obj in reader:
            all_call_transcripts.append(obj)
else:
    all_call_transcripts = get_all_call_transcripts()
    with jsonlines.open('all_call_transcripts.jsonl', mode='w') as writer:
        writer.write_all(all_call_transcripts)

#cache all calls
if os.path.exists('all_calls.jsonl'):
    all_calls = []
    with jsonlines.open('all_calls.jsonl') as reader:
        for obj in reader:
            all_calls.append(obj)
else:
    all_calls = get_all_calls()
    with jsonlines.open('all_calls.jsonl', mode='w') as writer:
        writer.write_all(all_calls)

#cache all gong users
if os.path.exists('all_gong_users.jsonl'):
    all_gong_users = []
    with jsonlines.open('all_gong_users.jsonl') as reader:
        for obj in reader:
            all_calls.append(obj)
else:
    all_gong_users = get_all_gong_users()
    with jsonlines.open('all_gong_users.jsonl', mode='w') as writer:
        writer.write_all(all_gong_users)

call_transcripts = all_call_transcripts
gong_call_by_id = {}
gong_speakers_by_id = {}

for call in all_calls:
    if 'metaData' in call:
        gong_call_by_id[call['metaData']['id']] = call['metaData']
        for speaker in call['parties']:
            if speaker['speakerId']:
                gong_speakers_by_id[speaker['speakerId']] = speaker



call_uterrances = prepare_utterance_dataset(call_transcripts=call_transcripts)


for utterance in call_uterrances:
    speaker = gong_speakers_by_id[utterance['speaker_id']]
    call = gong_call_by_id[utterance['call_id']]
    utterance['speaker_name'] = speaker['name']
    utterance['speaker_email'] = speaker.get('emailAddress', None)
    utterance['speaker_affiliation'] = speaker['affiliation']


    utterance['call_title'] = call['title']
    utterance['call_start_time'] = call['started']
    utterance['call_url'] = call['url']


keys = call_uterrances[0].keys()
with open('nomic_gong_calls_utterance_level.csv', 'w', newline='') as output_file:
    dict_writer = csv.DictWriter(output_file, keys)
    dict_writer.writeheader()
    dict_writer.writerows(call_uterrances)
