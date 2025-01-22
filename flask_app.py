import json
import base64
import requests
from flask import Flask,render_template, request, send_file, Response

app = Flask(__name__)
# Mapping for dropdown options
kalakurichi_data = {'Chinnasalem': '09', 'Kallakurichi': '07', 'Kalvarayan Hills': '10', 'Sankarapuram': '08', 'Tirukkoilur': '05', 'Ulundurpet': '06', 'Vanapuram': '11'}
cuddalore_data = {'Bhuvanagiri': '09', 'Chidambaram': '03', 'Cuddalore': '01', 'Kattumannarkoil': '04', 'Kurinjipadi': '07', 'Panruti': '02', 'Srimushnam': '10', 'Titagudi': '06', 'Veppur': '08', 'Vridhachalam': '05'}
villupuram_data = {'Gingee': '04', 'Kandacheepuram': '12', 'Marakkanam': '11', 'Melmalaiyanoor': '13', 'Thiruvennainallur': '14', 'Tindivanamm': '03', 'Vanur': '02', 'Vikravandi': '10', 'Villupuram': '01'}


master_data = {
    'Villuppuram': villupuram_data,
    'Kalakurichi': kalakurichi_data,
    'Cuddalore': cuddalore_data
}

TALUK_MAPPING = {
    "villupuram": [k for k in villupuram_data.keys()],
    "kalakurichi": [k for k in kalakurichi_data.keys()],
    "cuddalore": [k for k in cuddalore_data.keys()]
}

DISTRICT_CODES = {'villupuram':'07','kalakurichi':'33','cuddalore':'18'}

TALUK_CODES = {}
TALUK_CODES.update(kalakurichi_data)
TALUK_CODES.update(cuddalore_data)
TALUK_CODES.update(villupuram_data)


def generate_pdf(gis):
  URL = "https://collabland-tn.gov.in/APIServices/rest/Collabland/FMBMapServicePDF"

  payload ={
  "state": 33,
  "giscode": gis,
  "scale": -999,
  "width": 210,
  "height": 297,
  }

  tn_r = requests.post(url=URL,data=payload,verify=False)

  if tn_r.status_code == 200:
    j_data = tn_r.json()
    base64string = j_data['success']
    return base64string
  else:
    return 'Error'

@app.route('/')
def index():
    return render_template('index.html', districts=TALUK_MAPPING)

@app.route('/download', methods=['POST'])
def download():
    # Get data from the form
    district = request.form.get('dropdown1')
    taluk = request.form.get('dropdown2')
    village_code = request.form.get('input1')
    survey_number = request.form.get('input2')

    # Generate the unique code

    district_code = DISTRICT_CODES.get(district, "00")
    taluk_code = TALUK_CODES.get(taluk, "000")
    output_code = f"S{district_code}{taluk_code}{village_code}{survey_number}"

    extracted = generate_pdf(output_code)
    
    if extracted !='Error':
      base64_pdf = extracted
      pdf_data = base64.b64decode(base64_pdf)
      response = Response(pdf_data, mimetype='application/pdf')
      f_name = f"{village_code} FMB {survey_number}"
      response.headers['Content-Disposition'] = f'inline; filename={f_name}.pdf'
    else:
      return 'Error'

    return response

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)