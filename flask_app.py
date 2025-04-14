from flask import Flask, render_template, request, jsonify, Response
import requests
import base64
import json
import pymupdf


headers = {
    'accept': '*/*',
    'accept-language': 'en-US,en;q=0.6',
    # 'content-length': '0',
    'cookie': 'httpsonly; Path=/tmp; httpsonly; Path=/tmp; JSESSIONID=6A3F93064B8612F377BC36BC337BF04D',
    'origin': 'https://eservices.tn.gov.in',
    'priority': 'u=1, i',
    'referer': 'https://eservices.tn.gov.in/',
    'sec-ch-ua': '"Not A(Brand";v="8", "Chromium";v="132", "Brave";v="132"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-origin',
    'sec-gpc': '1',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36',
}


app = Flask(__name__)

def base64_to_pdf_bytes(base64_string):
    return base64.b64decode(base64_string)

def pdf_bytes_to_base64(pdf_bytes):
    return base64.b64encode(pdf_bytes).decode("utf-8")

def edit_pdf(pdf_bytes):
  doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")
  page = doc.load_page(0)
  content = page.get_drawings()
  rect = content[-17]['rect']
  page.add_redact_annot(rect,fill=(0,0,0,0))
  page.apply_redactions()
  return doc.write()

def process_pdf(base64_string):
    pdf_bytes = base64_to_pdf_bytes(base64_string)
    edited_pdf_bytes = edit_pdf(pdf_bytes)
    return pdf_bytes_to_base64(edited_pdf_bytes)



def generate_pdf(gis,size_list,scale):
  URL_1 = "https://collabland-tn.gov.in/APIServices/rest/Collabland/FMBMapServicePDF"

  payload ={
  "state": 33,
  "giscode": gis,
  "scale": scale,
  "width": size_list[0],
  "height": size_list[1],
  }

  tn_r = requests.post(url=URL_1,data=payload,verify=False)
  if tn_r.status_code == 200:
    j_data = tn_r.json()
    base64string = j_data['success']
    return base64string
  else:
    return 'Error'

URL = 'https://eservices.tn.gov.in/eservicesnew/land/ajax.html'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get-districts', methods=['GET'])
def get_districts():
    payload ={
      'page': 'ruralservice',
      'ser': 'dist',
      'lang': 'en',
      'type': 'rur',
      'call_type': 'ser',
    }
    response = requests.post(URL,data=payload,headers=headers)
    if response.status_code == 200:
        districts = response.json()
        return jsonify(districts)
    else:
        return jsonify({'error': 'Failed to fetch districts'}), 500


@app.route('/get-taluks', methods=['POST'])
def get_taluks():
    # district = request.json.get('district')
    data = request.get_json()  # Parse JSON data from the request
    if not data or 'district' not in data:
        return jsonify({'error': 'Missing district parameter'}), 400

    district = data['district']
    payload = {
      'page': 'ruralservice',
      'ser': 'tlk',
      'distcode': district,
      'lang': 'en',
      'type': 'rur',
      'call_type': 'ser',
    }
    response = requests.post(URL, params=payload,headers=headers)
    if response.status_code == 200:
        taluks = response.json()
        return jsonify(taluks)
    else:
        return jsonify({'error': 'Failed to fetch taluks'}), 500


@app.route('/get-villages', methods=['POST'])
def get_villages():
    district = request.json.get('district')
    taluk = request.json.get('taluk')
    payload ={
      'page': 'ruralservice',
      'ser': 'vill',
      'distcode': district,
      'talukcode': taluk,
      'lang': 'en',
      'type': 'rur',
      'call_type': 'ser',
    }
    response = requests.post(URL, params=payload,headers=headers)
    if response.status_code == 200:
        villages = response.json()  # Expected to return {"villages": [{"name": "X", "code": "Y"}, ...]}
        return jsonify(villages)
    else:
        return jsonify({'error': 'Failed to fetch villages'}), 500


@app.route('/download', methods=['POST'])
def download():
    size = {
      "A4":[210,297],
      "A3":[297,420],
      "Legal":[216,356]
    }
    district_code = request.form.get('DISTRICT_DD')
    taluk_code = request.form.get('TALUK_DD')
    village_code = request.form.get('VILLAGE_DD')
    survey_number = request.form.get('input2')
    paper_size = request.form.get('SIZE_DD')
    scale = request.form.get('SCALE_DD')

    output_code = f"S{district_code}{taluk_code}{village_code}{survey_number}"

    extracted = generate_pdf(output_code,size[paper_size],scale)

    if extracted != 'Error':
        base64_pdf = extracted

        edited_base64_pdf = process_pdf(base64_pdf)

        pdf_data = base64.b64decode(edited_base64_pdf)
        response = Response(pdf_data, mimetype='application/pdf')
        f_name = f"{village_code} FMB {survey_number}"
        response.headers['Content-Disposition'] = f'inline; filename={f_name}.pdf'
    else:
        return 'Error in function'

    return response

