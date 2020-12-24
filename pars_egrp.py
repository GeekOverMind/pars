import json
import requests


# search_macro_region('Татарстан', 'Казань', 'Петербургская', 1)
def search_macro_region(name_of_region, name_of_state, street, house):
    macro_region_id, state_id = None, None
    url_extra = 'https://extra.egrp365.ru/api/extra/index.php'
    form_data = {
        'method': 'getRegionsList'
        }

    post = requests.post(url_extra, data=form_data)
    _json = json.loads(post.text)
    data = _json['data']
    for region in data:
        if name_of_region in region['name']:
            macro_region_id = region['value']
            form_data['region'] = macro_region_id

    post_two = requests.post(url_extra, data=form_data)
    _json_two = json.loads(post_two.text)
    data_two = _json_two['data']
    for state in data_two:
        if name_of_state in state['name']:
            state_id = state['value']

    url_db = 'https://extra.egrp365.ru/api/mongo/index.php'
    form_data_db = {
        'macroRegionId': macro_region_id,
        'regionId': state_id,
        'street': street,
        'house': house,
        'method': 'searchByAddress'
        }
    post_db = requests.post(url_db, data=form_data_db)
    _json_db = post_db.text

    # for a test
    with open('content.txt', 'w') as file:
        print(_json_db, file=file)
