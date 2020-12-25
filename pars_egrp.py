import json
import requests


# extra_search('Татарстан', 'Казань', 'Петербургская', '1')
# extra_search('Татарстан Казань Петербургская 1')
def extra_search(*string_search):
    if len(string_search) == 4:
        name_of_region, name_of_state, street, house = map(str, string_search)
        one_string_query = ' '.join(string_search)  # for total json
    else:
        name_of_region, name_of_state, street, house = ' '.join(string_search).split(' ')
        one_string_query = ''.join(string_search)  # for total json

    url = 'https://extra.egrp365.ru/api/extra/index.php'

    form_data_db = {
        'street': street,
        'house': house,
        'method': 'searchByAddress'
        }

    form_data = {
        'method': 'getRegionsList'
        }

    res_region = requests.post(url, data=form_data)
    json_region = json.loads(res_region.text)
    data = json_region['data']
    for region in data:
        if name_of_region in region['name']:
            form_data['region'] = region['value']
            form_data_db['macroRegionId'] = region['value']
            break

    res_state = requests.post(url, data=form_data)
    json_state = json.loads(res_state.text)
    data_two = json_state['data']
    for state in data_two:
        if name_of_state in state['name']:
            form_data_db['regionId'] = state['value']
            break

    res_data = requests.post(url, data=form_data_db)
    json_data = json.loads(res_data.text)
    found = json_data['data']

    # for a test
    url_geo = 'https://egrp365.ru/map_alpha/ajax/geocode_yandex2.php'
    with open('found.txt', 'w') as file:
        for tag in found:
            res_geodata = requests.post(url_geo, data={'obj_name': tag['address']})
            geo_data = json.loads(res_geodata.text)
            res_other = requests.post('https://extra.egrp365.ru/api/mongo/index.php', data={'number': tag['cn']}).text
            json_other = json.loads(res_other)['data'][0]

            print(
                f"Кадастровый номер: {tag['cn']}\n"
                f"Адрес: {tag['address']}\n"
                f"Ссылка на кадастровую карту объекта: https://egrp365.ru/map/?kadnum={tag['cn']}\n"
                f"Этаж: {json_other['floor']}, Плошадь: {json_other['area']}\n"
                f"Географические координаты объекта: {geo_data}\n",
                file=file
                )

    url = 'https://suggestions.dadata.ru/suggestions/api/4_1/rs/suggest/address'
    head = {
        'Authorization': 'Token e8e5282e003f9876d9a66e625d4b7cec5bbf9274',
        'Connection': 'keep-alive',
        'User-Agent': 'Mozilla/5.0'
    }
    json_total = requests.post(url, json={'query': one_string_query}, headers=head, verify=False).text
    with open('json_total.txt', 'w') as file:
        print(json_total, file=file)


if __name__ == '__main__':
    extra_search('Татарстан Казань Петербургская 1')
