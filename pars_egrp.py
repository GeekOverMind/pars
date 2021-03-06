#!/usr/bin/python3.9

import json
import requests
import threading

from manage_module import db_config as config
from manage_module import OpenDatabase


def start_pars():
    find_from_sql()


def object_search(string_search):
    if len(string_search) == 4:
        name_of_region, name_of_state, street, house = string_search
        one_string_query = ' '.join(string_search)  # for total json
    else:
        name_of_region, name_of_state, street, house = string_search.split(' ')
        one_string_query = string_search  # for total json

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
        if not json_data.get('success'):
            return False

        url = 'https://suggestions.dadata.ru/suggestions/api/4_1/rs/suggest/address'
        head = {
            'Authorization': 'Token e8e5282e003f9876d9a66e625d4b7cec5bbf9274',
            'Connection': 'keep-alive',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:81.0) Gecko/20100101 Firefox/81.0'
            }
        res_json_total = requests.post(url, json={'query': one_string_query}, headers=head, verify=False)
        if res_json_total.status_code == 200:
            json_total = res_json_total.text
        else:
            json_total = ''

        url_geo = 'https://egrp365.ru/map_alpha/ajax/geocode_yandex2.php'

        found = json_data.get('data')
        if found:
            out_data = []
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

                data_to_sql = (
                    tag['cn'],
                    tag['address'],
                    f"https://egrp365.ru/map/?kadnum={tag['cn']}",
                    floor,
                    area,
                    geo_data,
                    name_of_region,
                    name_of_state,
                    street,
                    house,
                    tag['apartment'],  # not verified, server was overloaded
                    json_total,
                    res_data.text
                )
                out_data.append(data_to_sql)
            return out_data
        else:
            return False

    except json.decoder.JSONDecodeError:
        return 'JSON Error'


def find_from_sql():
    with OpenDatabase(config) as cursor:
        def delete_not_found():
            _sql = """DELETE FROM not_found"""
            cursor.execute(_sql)

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

        def found_objects():
            _sql = """
                SELECT COUNT(*) FROM results_search;
                """
            cursor.execute(_sql)
            return cursor.fetchone()[0]

        def not_found_object():
            _sql = """
                SELECT COUNT(DISTINCT id) FROM not_found;
                """
            cursor.execute(_sql)
            return cursor.fetchone()[0]

        def equal_address(string):
            _sql = """
                SELECT COUNT(*) FROM results_search r
                WHERE EXISTS
                    (SELECT * FROM to_search t
                    WHERE
                        r.region = t.region
                    AND
                        r.city = t.city
                    AND
                        r.street = t.street
                    AND
                        r.house = t.house
                    OR
                        CONCAT_WS(' ', r.region, r.city, r.street, r.house) = %s
                    );
                """
            cursor.execute(_sql, (string,))
            return cursor.fetchone()[0]

        def object_in_region():
            _sql = """
                SELECT count(*), region, low_area(area), high_area(area) FROM results_search
                GROUP BY region, low_area(area), high_area(area);
                """

            cursor.execute(_sql)
            result = cursor.fetchall()

            for row in result:
                print(f'Количество найденных объектов в регионе {row[1]}'
                      f'с площадью от {row[2]} до {row[3]} составляет {row[0]}')

        delete_not_found()
        while get_source():
            rows = get_source()
            if rows[0][1]:
                data = object_search(rows[0][1])  # string
                string_to_check = rows[0][1]
            else:
                data = object_search(rows[0][2:])  # tuple
                string_to_check = ' '.join(rows[0][2:])

            if data:
                if isinstance(data, str):
                    print(data)

                elif isinstance(data, list):
                    for line in data:
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
                        cursor.execute(sql, line)

                        object_in_region()

                        sql = """
                            INSERT INTO resume (
                                found,
                                not_found,
                                equal
                                )
                            VALUES (%s, %s, %s);
                        """
                        cursor.execute(sql, (
                            found_objects(),
                            not_found_object(),
                            equal_address(string_to_check)
                            )
                        )

                        sql = """
                            DELETE FROM to_search WHERE id = %s;
                            """
                        cursor.execute(sql, (rows[0][0],))
                else:
                    print('Oops...')

            elif not data:
                cursor.execute("""INSERT INTO not_found (id) VALUES (%s);""", (rows[0][0],))

        t = threading.Timer(600.00, start_pars)
        t.start()


if __name__ == '__main__':
    find_from_sql()
