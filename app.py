import os
import io
from flask import Flask, render_template, request, jsonify
import requests
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from PIL import Image
import base64
import logging

load_dotenv()

def resize_image(image_data, max_size=(800, 800)):
    image = Image.open(io.BytesIO(image_data))
    image.thumbnail(max_size)
    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format='JPEG', quality=85)
    img_byte_arr = img_byte_arr.getvalue()
    return img_byte_arr

PIXELCUT_API_KEY = os.environ.get("PIXELCUT_API_KEY")
if not PIXELCUT_API_KEY:
    raise ValueError("PIXELCUT_API_KEY is not set in the environment variables.")

app = Flask(__name__)

PIXELCUT_API_ENDPOINT = "https://api.developer.pixelcut.ai/v1/try-on"

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

        person_filename = "person_image.jpg"
        person_data = person_image.read()

        garment_filename = "garment_image.jpg"
        garment_data = garment_image.read()

        person_image_obj = Image.open(io.BytesIO(person_data))
        person_format = person_image_obj.format
        person_size = person_image_obj.size
        logging.info(f"Person image format: {person_format}, size: {person_size}")

        garment_image_obj = Image.open(io.BytesIO(garment_data))
        garment_format = garment_image_obj.format
        garment_size = garment_image_obj.size
        logging.info(f"Garment image format: {garment_format}, size: {garment_size}")

        person_data = resize_image(person_data)
        garment_data = resize_image(garment_data)

        files = {
            'person_image': (person_filename, person_data),
            'garment_image': (garment_filename, garment_data)
        }

        headers = {'X-API-KEY': PIXELCUT_API_KEY}
        logging.info(f"Using Pixelcut API key: {PIXELCUT_API_KEY}")

        try:
            response = requests.post(PIXELCUT_API_ENDPOINT, headers=headers, files=files)
            response.raise_for_status()
        except requests.exceptions.RequestException as req_err:
            logging.error(f"Error sending request to Pixelcut API: {str(req_err)}")
            return jsonify({'error': f'Error sending request to Pixelcut API: {str(req_err)}'}), 500

        if response.status_code == 200:
            result = response.json()

            if 'result_url' in result:
                try:
                    result_url = result['result_url']
                    img_response = requests.get(result_url, stream=True)
                    img_response.raise_for_status()

                    if img_response.status_code == 200:
                        img_byte_arr = io.BytesIO()
                        for chunk in img_response.iter_content(1024):
                            img_byte_arr.write(chunk)
                        img_byte_arr = img_byte_arr.getvalue()

                        # Save the image to the static/uploads directory
                        filename = secure_filename(os.urandom(16).hex() + '.jpg')
                        filepath = 'static/uploads/' + filename
                        with open(filepath, 'wb') as f:
                            f.write(img_byte_arr)

                        result_url =  '/' + filepath  # Construct the URL
                        result['result_url'] = result_url
                except requests.exceptions.RequestException as img_err:
                    logging.error(f"Error downloading result image: {str(img_err)}")
                    return jsonify({'error': f'Error downloading result image: {str(img_err)}'}), 500
                except Exception as img_error:
                    logging.error(f"Error processing result image: {str(img_error)}")
                    return jsonify({'error': f'Error processing result image: {str(img_error)}'}), 500

            return jsonify(result)
        else:
            error_message = response.json().get('error', 'No error message from API')
            logging.error(f"API Error: {response.status_code} - {error_message}")
            return jsonify({'error': f'API Error: {response.status_code} - {error_message}'}), 400

    except ValueError as ve:
        logging.error(f"Configuration error: {str(ve)}")
        return jsonify({'error': f'Configuration error: {str(ve)}'}), 400
    except Exception as e:
        logging.exception("An unexpected error occurred:")
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
    logging.info(f"Flask app running on port {port}")
