import requests
from requests.auth import HTTPBasicAuth
from flask import Flask, render_template, redirect, Response, send_file

app = Flask(__name__)

IMAGE_ORIGIN = 'http://caltech.powerflex.com:8510'
images = ['acc5cam0%s' % i for i in range(5, 8)]


@app.route('/')
def main():
    return render_template('index.html', chargers=list(get_chargers()), images=images)


@app.route('/healthcheck')
def healthcheck():
    return 'OK'


@app.route('/images/<image_id>')
def image(image_id):
    if image_id in images:
        url = '%s/%s' % (IMAGE_ORIGIN, image_id)
        try:
            resp = requests.get(url, timeout=5)
        except requests.exceptions.Timeout:
            return Response(status=503)
        excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
        headers = [(name, value) for (name, value) in resp.raw.headers.items() if name.lower() not in excluded_headers]
        response = Response(resp.content, resp.status_code, headers)
        return response
    elif image_id == 'favicon.ico':
        return send_file('images/favicon.gif')


def get_plugshare(location_id=352230):
    location_template = 'https://api.plugshare.com/v3/locations/%s'
    basic = HTTPBasicAuth('basic', 'd2ViX3YyOkVOanNuUE54NHhXeHVkODU=')
    s = requests.Session()
    rsp = s.get('https://plugshare.com', auth=basic)
    print(s.cookies.get_dict())
    print(rsp.content)


def get_chargers_ev_api():
    try:
        r = requests.get(
            'https://ev.caltech.edu/api/v1/sessions/caltech',
            auth=('VDd2diw1r5ek7sPGmx4PvNVLaWeUXew2YPZw4SHyH5k', '')
        )
        print(r.json())
    except Exception as e:
        print(e)


def get_chargers():
    try:
        r = requests.get(
            'https://caltech.powerflex.com/api/datasources/proxy/20/query?db=exload&q=SELECT%20last(%22mamps_last%22)%20%20%2F%201000%20AS%20%22Measured%22%2C%20last(%22mamps_offered%22)%20%20%2F%201000%20AS%20%22Allocated%22%2C%20last(%22SoC%22)%20*100%20AS%20%22SoC%22%2C%20last(%22current_energy_delivered%22)%20AS%20%22Current%20Energy%20Delivered%22%20FROM%20%22DCFC_Session%22%20WHERE%20(%22evse_type%22%20%3D%20%27Tritium%20DCFC%27%20AND%20%22space_number%22%20!%3D%20%27veefil-11900390%27%20AND%20%22space_number%22%20!%3D%20%27veefil-11900388%27)%20AND%20time%20%3E%3D%20now()%20-%2010m%20GROUP%20BY%20%22space_number%22&epoch=ms').json()
        data = r['results'][0]['series']
        for c in data:
            result = dict(zip(c['columns'], c['values'][0]))
            result['name'] = c['tags']['space_number']
            yield result
    except Exception as e:
        print(e)
        return []
