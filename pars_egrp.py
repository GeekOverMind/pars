import json
import requests


# extra_search('Татарстан', 'Казань', 'Петербургская', '1')
def extra_search(name_of_region, name_of_state, street, house):
    url = 'https://extra.egrp365.ru/api/extra/index.php'

    form_data_db = {
        'street': street,
        'house': house,
        'method': 'searchByAddress'
        }

    form_data = {
        'method': 'getRegionsList'
        }

    post = requests.post(url, data=form_data)
    _json = json.loads(post.text)
    data = _json['data']
    for region in data:
        if name_of_region in region['name']:
            form_data['region'] = region['value']
            form_data_db['macroRegionId'] = region['value']

    post_two = requests.post(url, data=form_data)
    _json_two = json.loads(post_two.text)
    data_two = _json_two['data']
    for state in data_two:
        if name_of_state in state['name']:
            form_data_db['regionId'] = state['value']

    post_db = requests.post(url, data=form_data_db)
    _json_db = json.loads(post_db.text)
    funded = _json_db['data']

    # for a test
    url_geo = 'https://egrp365.ru/map_alpha/ajax/geocode_yandex2.php'
    with open('funded.txt', 'w') as file:
        for teg in funded:
            req = requests.post(url_geo, data={'obj_name': teg['address']})
            geo = json.loads(req.text)
            etc = requests.post('https://extra.egrp365.ru/api/mongo/index.php', data={'number': teg['cn']}).text
            etc_json = json.loads(etc)['data'][0]

            print(f"Кадастровый номер: {teg['cn']}\n"
                  f"Адрес: {teg['address']}\n"
                  f"Ссылка на кадастровую карту объекта: https://egrp365.ru/map/?kadnum={teg['cn']}\n"
                  f"Этаж: {etc_json['floor']}, Плошадь: {etc_json['area']}\n"
                  f"Географические координаты объекта: {geo}\n", file=file)
