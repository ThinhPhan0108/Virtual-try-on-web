import os
import uuid
import logging
from flask import Flask, render_template, request, jsonify
import requests
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

# Tải biến môi trường từ file .env (nếu có)
load_dotenv()

# Lấy API Key từ biến môi trường
PIXELCUT_API_KEY = os.environ.get("PIXELCUT_API_KEY")
if not PIXELCUT_API_KEY:
    logging.error("PIXELCUT_API_KEY is not set in the environment variables.")
    raise ValueError("PIXELCUT_API_KEY is not set in the environment variables.")
NGROK_URL = os.environ.get("NGROK_URL", "127.0.0.1:5000")

# Kiểm tra giá trị API Key và URL ngrok
# print(f"PIXELCUT_API_KEY: {PIXELCUT_API_KEY}")
# print(f"NGROK_URL: {NGROK_URL}")

# Cấu hình logging
logging.basicConfig(filename='error.log', level=logging.DEBUG,
                    format='%(asctime)s %(levelname)s: %(message)s')

app = Flask(__name__)

# Thư mục lưu ảnh tải lên
UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Endpoint của Pixelcut API
PIXELCUT_API_ENDPOINT = "https://api.developer.pixelcut.ai/v1/try-on"

# Cho phép các định dạng ảnh cụ thể
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/try-on', methods=['POST'])
def try_on():
    try:
        person_image = request.files['person_image']
        garment_image = request.files['garment_image']

        if not person_image or not garment_image:
            return jsonify({'error': 'Cả hai ảnh đều cần phải được tải lên'}), 400

        if not allowed_file(person_image.filename) or not allowed_file(garment_image.filename):
            return jsonify({'error': 'Chỉ chấp nhận các tệp ảnh với định dạng: png, jpg, jpeg'}), 400

        person_filename = secure_filename(person_image.filename)
        person_data = person_image.read()

        garment_filename = secure_filename(garment_image.filename)
        garment_data = garment_image.read()

        files = {
            'person_image': (person_filename, person_data, person_image.content_type),
            'garment_image': (garment_filename, garment_data, garment_image.content_type)
        }

        headers = {'X-API-KEY': PIXELCUT_API_KEY}

        print("Request Headers:", request.headers)
        print("Files:", files)

        # Prepare the data for printing
        files_str = ""
        for k, v in files.items():
            files_str += f"{k}: filename={v[0]}, content_type={v[2]}\n"

        print(f"Files data:\n{files_str}")

        try:
            response = requests.post(PIXELCUT_API_ENDPOINT, headers=headers, files=files)
            response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
        except requests.exceptions.RequestException as req_err:
            logging.error(f"Lỗi khi gửi yêu cầu đến Pixelcut API: {str(req_err)}")
            return jsonify({'error': f'Lỗi khi gửi yêu cầu đến Pixelcut API: {str(req_err)}'}), 500

        if response.status_code == 200:
            result = response.json()

            # Nếu API trả về URL ảnh kết quả
            if 'result_url' in result:
                try:
                    # Tải ảnh từ URL kết quả
                    result_url = result['result_url']
                    img_response = requests.get(result_url, stream=True)
                    img_response.raise_for_status()

                    if img_response.status_code == 200:
                        # Tạo tên file duy nhất cho ảnh kết quả
                        result_filename = f"result_{uuid.uuid4()}.jpg"
                        result_path = os.path.join(app.config['UPLOAD_FOLDER'], result_filename)

                        # Lưu ảnh vào thư mục uploads
                        with open(result_path, 'wb') as f:
                            for chunk in img_response.iter_content(1024):
                                f.write(chunk)

                        # Trả về URL local của ảnh kết quả
                        local_result_url = f"/static/uploads/{result_filename}"
                        result['local_result_url'] = local_result_url
                except requests.exceptions.RequestException as img_err:
                    logging.error(f"Lỗi khi tải ảnh kết quả: {str(img_err)}")
                    result['local_result_url'] = None  # Set a default value
                except Exception as img_error:
                    logging.error(f"Lỗi khi xử lý ảnh kết quả: {str(img_error)}")
                    result['local_result_url'] = None  # Set a default value

            return jsonify(result)
        else:
            error_message = response.json().get('error', 'Không có thông báo lỗi từ API')
            logging.error(f"Lỗi từ API: {response.status_code} - {error_message}")
            return jsonify({'error': f'Lỗi từ API: {response.status_code} - {error_message}'}), 400

    except ValueError as ve:
        logging.error(f"Lỗi cấu hình: {str(ve)}")
        return jsonify({'error': f'Lỗi cấu hình: {str(ve)}'}), 400
    except Exception as e:
        logging.error(f"Có lỗi xảy ra: {str(e)}")
        print(f"Exception: {str(e)}")
        return jsonify({'error': f'Có lỗi xảy ra: {str(e)}'}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
