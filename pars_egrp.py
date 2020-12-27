import json
import requests
from sql_db import OpenDatabase
from sql_db import db_config as config


# extra_search('Татарстан', 'Казань', 'Петербургская', '1')
# extra_search('Татарстан Казань Петербургская 1')
def object_search(*string_search):

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
    if res_region.status_code != 200:
        return f'Response {res_region.status_code}'

    try:
        json_region = json.loads(res_region.text)
        data = json_region.get('data')
        if data:
            for region in data:
                if name_of_region in region['name']:
                    form_data['region'] = region['value']
                    form_data_db['macroRegionId'] = region['value']
                    break
    except json.decoder.JSONDecodeError:
        return 'JSON Error'

    if form_data.get('region'):
        res_state = requests.post(url, data=form_data)

        if res_state.status_code != 200:
            return f'Response {res_state.status_code}'

        try:
            json_state = json.loads(res_state.text)
            data_two = json_state.get('data')
            if data_two:
                for state in data_two:
                    if name_of_state in state['name']:
                        form_data_db['regionId'] = state['value']
                        break
        except json.decoder.JSONDecodeError:
            return 'JSON Error'

    res_data = requests.post(url, data=form_data_db)

    if res_data.status_code != 200:
        return f'Response {res_data.status_code}'

    try:
        json_data = json.loads(res_data.text)
        found = json_data.get('data')

        url = 'https://suggestions.dadata.ru/suggestions/api/4_1/rs/suggest/address'
        head = {
            'Authorization': 'Token e8e5282e003f9876d9a66e625d4b7cec5bbf9274',
            'Connection': 'keep-alive',
            'User-Agent': 'Mozilla/5.0'
        }
        res_json_total = requests.post(url, json={'query': one_string_query}, headers=head, verify=False)
        if res_json_total.status_code == 200:
            json_total = res_json_total.text
        else:
            json_total = ''

        url_geo = 'https://egrp365.ru/map_alpha/ajax/geocode_yandex2.php'
        if found:
            for tag in found:
                res_geodata = requests.post(url_geo, data={'obj_name': tag['address']})
                if res_geodata.status_code == 200:
                    geo_data = ', '.join(json.loads(res_geodata.text))
                else:
                    geo_data = ''

                res_other = requests.post(
                    'https://extra.egrp365.ru/api/mongo/index.php',
                    data={'number': tag['cn']}
                    )
                if res_other.status_code == 200:
                    other_data = json.loads(res_other.text).get('data')
                    if other_data:
                        floor = other_data[0].get('floor')
                        area = other_data[0].get('area')
                    else:
                        floor, area = '', ''
                else:
                    floor, area = '', ''
                # json_other = json.loads(res_other.text)['data'][0]

                data_to_sql = (
                    tag['cn'],
                    tag['address'],
                    f"https://egrp365.ru/map/?kadnum={tag['cn']}",
                    floor,
                    area,
                    geo_data,
                    tag['region'],  # not verified, server was overloaded
                    tag['place'],  # not verified, server was overloaded
                    tag['street'],  # not verified, server was overloaded
                    tag['house'],  # not verified, server was overloaded
                    tag['apartment'],  # not verified, server was overloaded
                    json_total,
                    res_data.text
                )
                yield data_to_sql
        else:
            return False

    except json.decoder.JSONDecodeError:
        return 'JSON Error'


def find_from_sql():
    with OpenDatabase(config) as cursor:
        def get_source():
            _sql = """
                SELECT
                    id,
                    string_search,
                    region,
                    city,
                    street,
                    house
                FROM
                    to_search;
                """
            cursor.execute(_sql)
            return cursor.fetchall()

        rows = get_source()
        while rows[0]:
            if rows[0][1]:
                # print('var1', rows[0][1])
                data = object_search(rows[0][1])
            else:
                # print('var2', rows[0][2:])
                data = object_search(rows[0][2:])

            if data:
                sql = """
                    INSERT INTO results_search (
                        kad_number,
                        address,
                        link,
                        floor,
                        area,
                        geo,
                        region,
                        city,
                        street,
                        house,
                        apartment,	
                        json_main,
                        json_extra
                        )
                    VALUES
                        (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
                    """

                cursor.execute(sql, data)

                sql = """
                    DELETE FROM to_search WHERE id = %s;
                    """
                cursor.execute(sql, rows[0][0])
            elif isinstance(data, str):
                print(data)
            elif not data:
                cursor.execute("""INSERT INTO not_found (id) VALUES (%s);""", (rows[0][0],))
