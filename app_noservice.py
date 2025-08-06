from flask import Flask, render_template, request, jsonify
import json
import os
import time
from google import genai
from google.genai import types
from flask_sqlalchemy import SQLAlchemy
import threading
import datetime
import io
from PIL import Image
import requests
import base64
import google.auth
import google.auth.transport.requests
from google.cloud import storage
import vertexai
from vertexai.preview.vision_models import ImageGenerationModel
from google.protobuf.json_format import MessageToDict
from segmentation import segment_image as segment_image_internal, initialize_segmentation_model
from vto import get_vto_client, call_virtual_try_on, prediction_to_pil_image
from prism import call_product_recontext, prediction_to_pil_image as prism_prediction_to_pil_image
from veo_editing import generate_video as generate_veo_video, upload_to_gcs as upload_veo_to_gcs
import imagenedit


app = Flask(__name__)

# --- Configuration ---
PROJECT_ID = os.environ.get("GCP_PROJECT", "vital-octagon-19612")
LOCATION = "us-central1"
VIDEO_DIR = "static/videos"
GCS_BUCKET_NAME = os.environ.get("GCS_BUCKET_NAME", "gk-test-veo")
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///history.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

os.makedirs(VIDEO_DIR, exist_ok=True)
os.makedirs(os.path.join('static', 'uploads'), exist_ok=True)

client = None
GEMINI_MODEL = "gemini-2.5-flash"
segmentation_model = None
imagen_client = None

def init_clients(project_id, location):
    global client, segmentation_model, vto_client, imagen_client
    try:
        vertexai.init(project=project_id, location=location)
        client = genai.Client(vertexai=True, project=project_id, location=location)
        segmentation_model = initialize_segmentation_model()
        if not segmentation_model:
            print("Warning: Segmentation model failed to initialize.")
        vto_client = get_vto_client()
        imagen_client = imagenedit.initialize_imagen_client(project_id, location)
        return True
    except Exception as e:
        print(f"Error during Google GenAI client initialization: {e}")
        client = None
        segmentation_model = None
        vto_client = None
        imagen_client = None
        return False

init_clients(PROJECT_ID, LOCATION)

# --- Database Model ---
class GenerationHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    operation_id = db.Column(db.String(80), unique=True, nullable=False)
    prompt = db.Column(db.String(500), nullable=False)
    status = db.Column(db.String(20), nullable=False, default='queued')
    video_path = db.Column(db.String(500), nullable=True)
    image_path = db.Column(db.String(500), nullable=True)
    error_message = db.Column(db.String(500), nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    input_payload = db.Column(db.Text, nullable=True)
    output_payload = db.Column(db.Text, nullable=True)
    operation_type = db.Column(db.String(50), nullable=True)

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

class SystemInstruction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    content = db.Column(db.Text, nullable=False)

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

# --- Helper Functions ---

def upload_to_gcs(file_bytes, destination_blob_name):
    """Uploads a file to the bucket."""
    try:
        storage_client = storage.Client(project=PROJECT_ID)
        bucket = storage_client.bucket(GCS_BUCKET_NAME)
        blob = bucket.blob(destination_blob_name)
        blob.upload_from_string(file_bytes)
        return f"gs://{GCS_BUCKET_NAME}/{destination_blob_name}"
    except Exception as e:
        print(f"Error uploading to GCS: {e}")
        return None

def download_from_gcs(bucket_name, source_blob_name, destination_file_name):
    """Downloads a file from the bucket."""
    try:
        storage_client = storage.Client(project=PROJECT_ID)
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(source_blob_name)
        blob.download_to_filename(destination_file_name)
        return destination_file_name
    except Exception as e:
        print(f"Error downloading from GCS: {e}")
        return None

def generate_veo_prompt_internal(user_prompt, system_instructions, image_data=None):
    print(f"--- [DEBUG] Starting VEO Prompt Generation ---")
    if not client or not GEMINI_MODEL:
        print(f"[DEBUG] VEO prompt generation failed: Gemini model not initialized.")
        return "Error: Gemini model not initialized."
    try:
        print(f"[DEBUG] Generating VEO prompt with model: {GEMINI_MODEL}")
        content = [
            f"{system_instructions}\n\nUser Prompt: {user_prompt}\n\nGenerate the final prompt in a valid JSON format."
        ]
        if image_data:
            image_bytes = base64.b64decode(image_data)
            
            # Create a unique name for the GCS blob
            blob_name = f"prompt-images/{int(time.time() * 1000)}.png"
            gcs_uri = upload_to_gcs(image_bytes, blob_name)

            if gcs_uri:
                img = Image.open(io.BytesIO(image_bytes))
                mime_type = Image.MIME.get(img.format)
                if not mime_type:
                    mime_type = f"image/{img.format.lower()}"
                
                content.insert(0, types.Part.from_uri(file_uri=gcs_uri, mime_type=mime_type))
            else:
                return "Error: Failed to upload image to Google Cloud Storage."

        print(f"[DEBUG] Sending request to Vertex AI with content: {content}")
        response = client.models.generate_content(model=GEMINI_MODEL, contents=content)
        print(f"[DEBUG] Received response from Vertex AI.")
        return response.text
    except Exception as e:
        print(f"--- [DEBUG] ERROR during VEO prompt generation: {e} ---")
        return f"Error generating prompt: {e}"

def generate_video_internal(app_context, prompt, operation_id, model_name, seed, aspect_ratio, negative_prompt):
    with app_context:
        history_item = GenerationHistory.query.filter_by(operation_id=operation_id).first()
        if not client:
            history_item.status = 'failed'
            history_item.error_message = "Vertex AI client not initialized."
            db.session.commit()
            return
        try:
            history_item.status = 'running'
            db.session.commit()
            operation = client.models.generate_videos(
                model=model_name, prompt=prompt,
                config=types.GenerateVideosConfig(
                    aspect_ratio=aspect_ratio,
                    resolution="1080p",
                    number_of_videos=1,
                    seed=seed,
                    negative_prompt=negative_prompt
                )
            )
            while not operation.done:
                time.sleep(15)
                operation = client.operations.get(operation)

            if hasattr(operation, 'error') and operation.error:
                history_item.status = 'failed'
                error_info = operation.error
                history_item.error_message = f"Code: {error_info.code}, Message: {error_info.message}"
            elif operation.result and operation.result.generated_videos:
                generated_video = operation.result.generated_videos[0]
                # For Vertex AI, the video bytes are returned directly in the response.
                video_bytes = generated_video.video.video_bytes
                local_path = os.path.join(VIDEO_DIR, f"{operation_id}.mp4")
                with open(local_path, "wb") as f:
                    f.write(video_bytes)
                history_item.status = 'completed'
                history_item.video_path = f"/{local_path}"
            else:
                history_item.status = 'failed'
                history_item.error_message = "Operation finished with no error but no video was generated."
        except Exception as e:
            history_item.status = 'failed'
            history_item.error_message = str(e)
        db.session.commit()

def generate_image_video_internal(app_context, prompt, operation_id, image_bytes, model_name, seed, aspect_ratio, negative_prompt):
    with app_context:
        history_item = GenerationHistory.query.filter_by(operation_id=operation_id).first()
        
        try:
            creds, _ = google.auth.default(scopes=['httpshttps://www.googleapis.com/auth/cloud-platform'])
            auth_req = google.auth.transport.requests.Request()
            creds.refresh(auth_req)
            token = creds.token
        except Exception as e:
            history_item.status = 'failed'
            history_item.error_message = f"Failed to get authentication token: {e}"
            db.session.commit()
            return

        try:
            history_item.status = 'running'
            db.session.commit()

            try:
                img = Image.open(io.BytesIO(image_bytes))
                mime_type = Image.MIME.get(img.format)
                if not mime_type:
                    mime_type = f"image/{img.format.lower()}"
            except Exception as img_e:
                history_item.status = 'failed'
                history_item.error_message = f"Could not identify image format: {img_e}"
                db.session.commit()
                return

            encoded_image = base64.b64encode(image_bytes).decode('utf-8')

            api_endpoint = "us-central1-aiplatform.googleapis.com"
            url = f"https://{api_endpoint}/v1/projects/{PROJECT_ID}/locations/{LOCATION}/publishers/google/models/{model_name}:predictLongRunning"

            request_body = {
                "instances": [{"prompt": prompt, "image": {"bytesBase64Encoded": encoded_image, "mimeType": mime_type}}],
                "parameters": {
                    "aspectRatio": aspect_ratio, "sampleCount": 1, "durationSeconds": "8",
                    "personGeneration": "allow_all", "addWatermark": True, "includeRaiReason": True,
                    "generateAudio": True, "resolution": "1080p", "seed": seed, "negativePrompt": negative_prompt
                }
            }

            headers = {"Content-Type": "application/json", "Authorization": f"Bearer {token}"}

            response = requests.post(url, json=request_body, headers=headers)
            response.raise_for_status()

            operation_data = response.json()
            operation_name = operation_data.get('name')
            if not operation_name:
                history_item.status = 'failed'
                history_item.error_message = f"Failed to start operation: {response.text}"
                db.session.commit()
                return
            
            fetch_url = f"https://{api_endpoint}/v1/projects/{PROJECT_ID}/locations/{LOCATION}/publishers/google/models/{model_name}:fetchPredictOperation"
            fetch_body = {"operationName": operation_name}

            while True:
                time.sleep(20)
                op_response = requests.post(fetch_url, json=fetch_body, headers=headers)
                op_response.raise_for_status()
                op_data = op_response.json()
                if op_data.get('done'):
                    break
            
            if 'error' in op_data and op_data['error']:
                history_item.status = 'failed'
                error_info = op_data['error']
                history_item.error_message = f"Code: {error_info.get('code')}, Message: {error_info.get('message')}"
            elif 'response' in op_data and op_data['response']:
                videos = op_data['response'].get('videos', [])
                if videos and isinstance(videos, list) and len(videos) > 0 and 'bytesBase64Encoded' in videos[0]:
                    video_data_base64 = videos[0]['bytesBase64Encoded']
                    video_bytes = base64.b64decode(video_data_base64)
                    local_path = os.path.join(VIDEO_DIR, f"{operation_id}.mp4")
                    with open(local_path, "wb") as f:
                        f.write(video_bytes)
                    history_item.status = 'completed'
                    history_item.video_path = f"/{local_path}"
                else:
                    history_item.status = 'failed'
                    # Log the full response to help debug the structure
                    history_item.error_message = f"No video data in response. Full response: {json.dumps(op_data.get('response'))}"
            else:
                history_item.status = 'failed'
                history_item.error_message = f"Operation finished with an unknown state: {op_data}"

        except requests.exceptions.RequestException as req_e:
            history_item.status = 'failed'
            history_item.error_message = f"HTTP Request failed: {req_e}. Response: {req_e.response.text if req_e.response else 'No response'}"
        except Exception as e:
            history_item.status = 'failed'
            history_item.error_message = str(e)
        db.session.commit()

# --- Routes ---
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate-prompt', methods=['POST'])
def generate_prompt():
    data = request.json
    user_prompt = data.get('user_prompt', '')
    system_instructions = data.get('system_instructions', '')
    image_data = data.get('image_data') # This will be base64 encoded

    if not user_prompt or not system_instructions:
        return jsonify({'error': 'User prompt and system instructions are required.'}), 400
    
    final_prompt = generate_veo_prompt_internal(user_prompt, system_instructions, image_data)
    return jsonify({'final_prompt': final_prompt})

@app.route('/refine-prompt', methods=['POST'])
def refine_prompt():
    data = request.json
    current_prompt, refine_instruction = data.get('current_prompt', ''), data.get('refine_instruction', '')
    if not current_prompt or not refine_instruction:
        return jsonify({'error': 'Current prompt and refinement instruction are required.'}), 400
    system_instruction = f"Refine the following video prompt based on the instruction. Output only the new prompt.\n\nInstruction: {refine_instruction}"
    refined_prompt = generate_veo_prompt_internal(current_prompt, system_instruction)
    return jsonify({'refined_prompt': refined_prompt})

@app.route('/generate-videos', methods=['POST'])
def generate_videos():
    data = request.json
    prompts = data.get('prompts', [])
    model_name = data.get('model', 'veo-3.0-fast-generate-001')
    seed = data.get('seed', 42)
    aspect_ratio = data.get('aspect_ratio', '16:9')
    negative_prompt = data.get('negative_prompt', '')
    if not prompts:
        return jsonify({'error': 'No prompts provided.'}), 400
    operation_ids = []
    for i, prompt in enumerate(prompts):
        operation_id = f"op_{int(time.time() * 1000)}_{i}"
        new_history = GenerationHistory(operation_id=operation_id, prompt=prompt, status='queued')
        db.session.add(new_history)
        db.session.commit()
        operation_ids.append(operation_id)
        thread = threading.Thread(target=generate_video_internal, args=(app.app_context(), prompt, operation_id, model_name, seed, aspect_ratio, negative_prompt))
        thread.start()
    return jsonify({'operation_ids': operation_ids})

@app.route('/generate-image-video', methods=['POST'])
def generate_image_video():
    if 'image' not in request.files:
        return jsonify({'error': 'No image file provided.'}), 400
    file = request.files['image']
    prompt = request.form.get('prompt', '')
    model_name = request.form.get('model', 'veo-3.0-fast-generate-preview')
    seed = int(request.form.get('seed', 42))
    aspect_ratio = request.form.get('aspect_ratio', '16:9')
    negative_prompt = request.form.get('negative_prompt', '')

    if file.filename == '' or not prompt:
        return jsonify({'error': 'Image and prompt are required.'}), 400
    
    image_bytes = file.read()
    operation_id = f"img_op_{int(time.time() * 1000)}"
    
    # Save the uploaded image to serve it in the history
    _, f_ext = os.path.splitext(file.filename)
    image_filename = f"{operation_id}{f_ext}"
    image_save_path = os.path.join('static', 'uploads', image_filename)
    with open(image_save_path, 'wb') as f:
        f.write(image_bytes)
    
    relative_image_path = f"/{image_save_path}"

    new_history = GenerationHistory(operation_id=operation_id, prompt=prompt, status='queued', image_path=relative_image_path)
    db.session.add(new_history)
    db.session.commit()
    
    thread = threading.Thread(target=generate_image_video_internal, args=(app.app_context(), prompt, operation_id, image_bytes, model_name, seed, aspect_ratio, negative_prompt))
    thread.start()
    return jsonify({'operation_id': operation_id})

@app.route('/video-status/<operation_id>', methods=['GET'])
def video_status(operation_id):
    history_item = GenerationHistory.query.filter_by(operation_id=operation_id).first_or_404()
    return jsonify(history_item.to_dict())

@app.route('/get-generation-history', methods=['GET'])
def get_generation_history():
    history = GenerationHistory.query.order_by(GenerationHistory.timestamp.desc()).all()
    return jsonify({'history': [item.to_dict() for item in history]})

@app.route('/get-system-instructions', methods=['GET'])
def get_system_instructions():
    instructions = SystemInstruction.query.all()
    return jsonify({'instructions': [item.to_dict() for item in instructions]})

@app.route('/save-system-instruction', methods=['POST'])
def save_system_instruction():
    data = request.json
    name = data.get('name')
    content = data.get('content')
    if not name or not content:
        return jsonify({'error': 'Name and content are required.'}), 400
    
    new_instruction = SystemInstruction(name=name, content=content)
    db.session.add(new_instruction)
    db.session.commit()
    return jsonify({'success': True, 'instruction': new_instruction.to_dict()})

@app.route('/delete-system-instruction/<int:instruction_id>', methods=['DELETE'])
def delete_system_instruction(instruction_id):
    instruction = SystemInstruction.query.get(instruction_id)
    if instruction:
        db.session.delete(instruction)
        db.session.commit()
        return jsonify({'success': True})
    return jsonify({'error': 'Instruction not found.'}), 404

@app.route('/generate-editor-image', methods=['POST'])
def generate_editor_image():
    data = request.json
    prompt = data.get('prompt')
    negative_prompt = data.get('negative_prompt')
    seed = data.get('seed')
    aspect_ratio = data.get('aspect_ratio', '16:9')
    
    operation_id = f"img_op_{int(time.time() * 1000)}"
    new_history = GenerationHistory(operation_id=operation_id, prompt=prompt, status='running')
    db.session.add(new_history)
    db.session.commit()

    print(f"--- Generating Editor Image (Operation ID: {operation_id}) ---")
    print(f"Received Prompt: {prompt}")
    print(f"Received Negative Prompt: {negative_prompt}")
    print(f"Received Seed: {seed}")
    print(f"Received Aspect Ratio: {aspect_ratio}")

    try:
        print("Step 1: Initializing ImageGenerationModel...")
        generation_model = ImageGenerationModel.from_pretrained("imagen-4.0-generate-preview-06-06")
        print("Step 2: Model Initialized. Preparing to generate images...")

        generation_params = {
            "prompt": prompt,
            "number_of_images": 1,
            "aspect_ratio": aspect_ratio,
            "negative_prompt": negative_prompt,
            "person_generation": "allow_all",
            "safety_filter_level": "block_few",
            "add_watermark": False,
            "seed": seed
        }
        print(f"Generation Parameters: {generation_params}")

        images = generation_model.generate_images(**generation_params)
        print("Step 3: Images generated. Response received.")
        
        image_bytes = images[0]._image_bytes
        print("Step 4: Image bytes extracted. Saving locally...")
        
        # Save the generated image locally to be displayed in the history
        image_filename = f"{operation_id}.png"
        image_save_path = os.path.join('static', 'uploads', image_filename)
        with open(image_save_path, 'wb') as f:
            f.write(image_bytes)
        print(f"Step 5: Image saved to {image_save_path}. Updating history.")
        
        relative_image_path = f"/{image_save_path}"
        
        new_history.status = 'completed'
        new_history.image_path = relative_image_path
        db.session.commit()
        print("Step 6: History updated. Encoding and returning image data.")

        return jsonify({'image_data': base64.b64encode(image_bytes).decode('utf-8')})

    except Exception as e:
        print(f"--- ERROR during image generation: {e} ---")
        new_history.status = 'failed'
        new_history.error_message = str(e)
        db.session.commit()
        return jsonify({'error': str(e)}), 500

@app.route('/get-settings', methods=['GET'])
def get_settings():
    return jsonify({'project_id': PROJECT_ID, 'gcs_bucket': GCS_BUCKET_NAME})

@app.route('/save-settings', methods=['POST'])
def save_settings():
    global PROJECT_ID, GCS_BUCKET_NAME
    data = request.json
    PROJECT_ID = data.get('project_id', PROJECT_ID)
    GCS_BUCKET_NAME = data.get('gcs_bucket', GCS_BUCKET_NAME)

    # Re-initialize and validate clients
    if init_clients(PROJECT_ID, LOCATION):
        try:
            # Validate GCS bucket access
            storage.Client(project=PROJECT_ID).get_bucket(GCS_BUCKET_NAME)
            return jsonify({'success': True, 'message': 'Settings saved and validated successfully.'})
        except Exception as e:
            return jsonify({'success': False, 'message': f'GCS Bucket validation failed: {e}'})
    else:
        return jsonify({'success': False, 'message': 'Vertex AI client initialization failed.'})

@app.route('/segment-image', methods=['POST'])
def segment_image_route():
    if not segmentation_model:
        return jsonify({'error': 'Segmentation model not initialized.'}), 500

    if 'image' not in request.files:
        return jsonify({'error': 'No image file provided.'}), 400
    
    file = request.files['image']
    if file.filename == '':
        return jsonify({'error': 'No selected file.'}), 400

    mode = request.form.get('mode', 'foreground')
    prompt = request.form.get('prompt', None)
    
    # Save the uploaded file temporarily
    temp_path = os.path.join('static', 'uploads', file.filename)
    file.save(temp_path)

    result = segment_image_internal(
        model=segmentation_model,
        input_file=temp_path,
        segmentation_mode=mode,
        prompt=prompt
    )

    # Clean up the temporary file
    os.remove(temp_path)

    if 'error' in result:
        return jsonify(result), 500
    
    mask_urls = []
    for i, mask_data in enumerate(result.get('masks', [])):
        mask_bytes = base64.b64decode(mask_data)
        mask_filename = f"mask_{int(time.time() * 1000)}_{i}.png"
        mask_save_path = os.path.join('static', 'uploads', mask_filename)
        with open(mask_save_path, 'wb') as f:
            f.write(mask_bytes)
        mask_urls.append(f"/{mask_save_path}")

    operation_id = f"seg_op_{int(time.time() * 1000)}"
    input_payload = {'mode': mode, 'prompt': prompt, 'image': file.filename}
    output_payload = {'masks': mask_urls}
    new_history = GenerationHistory(
        operation_id=operation_id,
        prompt=f"Segmentation: {prompt or mode}",
        status='completed',
        input_payload=json.dumps(input_payload),
        output_payload=json.dumps(output_payload),
        operation_type='segmentation'
    )
    db.session.add(new_history)
    db.session.commit()

    return jsonify({'masks': mask_urls})


@app.route('/vto', methods=['POST'])
def vto_route():
    operation_id = f"vto_op_{int(time.time() * 1000)}"
    person_image_file = request.files.get('person_image')
    product_image_file = request.files.get('product_image')
    mask_image_file = request.files.get('mask_image')

    person_image_uri = request.form.get('person_image_uri')
    product_image_uri = request.form.get('product_image_uri')

    if not (person_image_file or person_image_uri) or not (product_image_file or product_image_uri):
        return jsonify({'error': 'Person and product images (either file or URI) are required.'}), 400

    person_image_bytes = person_image_file.read() if person_image_file else None
    product_image_bytes = product_image_file.read() if product_image_file else None
    mask_image_bytes = mask_image_file.read() if mask_image_file else None

    prompt = request.form.get('prompt')
    person_description = request.form.get('person_description')
    product_description = request.form.get('product_description')
    model_endpoint_name = request.form.get('model_endpoint_name', 'virtual-try-on-exp-05-31')
    sample_count = request.form.get('sample_count', type=int)
    base_steps = request.form.get('base_steps', type=int)
    seed = request.form.get('seed', type=int)

    try:
        vto_project_id = "cloud-lvm-training-nonprod"
        response = call_virtual_try_on(
            client=vto_client,
            project_id=vto_project_id,
            location=LOCATION,
            model_endpoint_name=model_endpoint_name,
            person_image_bytes=person_image_bytes,
            product_image_bytes=product_image_bytes,
            mask_image_bytes=mask_image_bytes,
            person_image_uri=person_image_uri,
            product_image_uri=product_image_uri,
            prompt=prompt,
            person_description=person_description,
            product_description=product_description,
            sample_count=sample_count,
            base_steps=base_steps,
            seed=seed,
        )

        generated_image_pil = prediction_to_pil_image(response.predictions[0])
        
        # Save the generated image locally to be displayed in the history
        image_filename = f"{operation_id}.png"
        image_save_path = os.path.join('static', 'uploads', image_filename)
        generated_image_pil.save(image_save_path)
        
        relative_image_path = f"/{image_save_path}"

        # Save the generated image to a bytes buffer for the response
        buf = io.BytesIO()
        generated_image_pil.save(buf, format='PNG')
        img_str = base64.b64encode(buf.getvalue()).decode('utf-8')

        input_payload = {
            'prompt': prompt,
            'person_description': person_description,
            'product_description': product_description,
            'model_endpoint_name': model_endpoint_name,
            'sample_count': sample_count,
            'base_steps': base_steps,
            'person_image_uri': person_image_uri,
            'product_image_uri': product_image_uri,
        }
        output_payload = {'generated_image': '...'} # Don't save the full image string
        new_history = GenerationHistory(
            operation_id=operation_id,
            prompt=prompt or "VTO Generation",
            status='completed',
            input_payload=json.dumps(input_payload),
            output_payload=json.dumps(output_payload),
            operation_type='vto',
            image_path=relative_image_path
        )
        db.session.add(new_history)
        db.session.commit()

        return jsonify({'generated_image': img_str})

    except Exception as e:
        new_history = GenerationHistory(
            operation_id=operation_id,
            prompt=request.form.get('prompt') or "VTO Generation",
            status='failed',
            error_message=str(e),
            operation_type='vto'
        )
        db.session.add(new_history)
        db.session.commit()
        return jsonify({'error': str(e)}), 500

@app.route('/product-recontext', methods=['POST'])
def product_recontext():
    operation_id = f"recontext_op_{int(time.time() * 1000)}"
    image_files = request.files.getlist('images')
    image_uris = request.form.getlist('image_uris')
    prompt = request.form.get('prompt')
    product_description = request.form.get('product_description')
    disable_prompt_enhancement = request.form.get('disable_prompt_enhancement', 'false').lower() == 'true'
    sample_count = request.form.get('sample_count', 1, type=int)
    base_steps = request.form.get('base_steps', type=int)
    safety_setting = request.form.get('safety_setting')
    person_generation = request.form.get('person_generation')
    aspect_ratio = request.form.get('aspect_ratio')
    resolution = request.form.get('resolution')
    seed = request.form.get('seed', type=int)

    image_bytes_list = [base64.b64encode(file.read()).decode('utf-8') for file in image_files]

    try:
        response = call_product_recontext(
            image_bytes_list=image_bytes_list,
            image_uris_list=image_uris,
            prompt=prompt,
            product_description=product_description,
            disable_prompt_enhancement=disable_prompt_enhancement,
            sample_count=sample_count,
            base_steps=base_steps,
            safety_setting=safety_setting,
            person_generation=person_generation,
            aspect_ratio=aspect_ratio,
            resolution=resolution,
            seed=seed,
        )

        predictions = []
        saved_image_path = None
        for i, prediction in enumerate(response.predictions):
            pil_image = prism_prediction_to_pil_image(prediction)
            
            # Save the first generated image locally for the history
            if i == 0:
                image_filename = f"{operation_id}.png"
                image_save_path = os.path.join('static', 'uploads', image_filename)
                pil_image.save(image_save_path)
                saved_image_path = f"/{image_save_path}"

            buf = io.BytesIO()
            pil_image.save(buf, format='PNG')
            img_str = base64.b64encode(buf.getvalue()).decode('utf-8')
            predictions.append(img_str)

        input_payload = {
            'prompt': prompt,
            'product_description': product_description,
            'disable_prompt_enhancement': disable_prompt_enhancement,
            'sample_count': sample_count,
            'base_steps': base_steps,
            'safety_setting': safety_setting,
            'person_generation': person_generation,
            'aspect_ratio': aspect_ratio,
            'resolution': resolution,
            'image_uris': image_uris,
        }
        output_payload = {'predictions': '...'} # Don't save the full image strings
        new_history = GenerationHistory(
            operation_id=operation_id,
            prompt=prompt or "Product Recontext",
            status='completed',
            input_payload=json.dumps(input_payload),
            output_payload=json.dumps(output_payload),
            operation_type='recontext',
            image_path=saved_image_path
        )
        db.session.add(new_history)
        db.session.commit()

        return jsonify({'predictions': predictions})

    except Exception as e:
        new_history = GenerationHistory(
            operation_id=operation_id,
            prompt=request.form.get('prompt') or "Product Recontext",
            status='failed',
            error_message=str(e),
            operation_type='recontext'
        )
        db.session.add(new_history)
        db.session.commit()
        return jsonify({'error': str(e)}), 500

@app.route('/get-usage-report', methods=['GET'])
def get_usage_report():
    range_param = request.args.get('range', '7d')
    
    try:
        # Get data from your local database instead of Cloud Monitoring
        if range_param == '7d':
            # Get last 7 days of data from your database
            seven_days_ago = datetime.datetime.utcnow() - datetime.timedelta(days=7)
            history_items = GenerationHistory.query.filter(
                GenerationHistory.timestamp >= seven_days_ago
            ).all()
            
            # Group by day
            daily_data = {}
            for item in history_items:
                date_key = item.timestamp.date().isoformat()
                if date_key not in daily_data:
                    daily_data[date_key] = {'completed': 0, 'failed': 0, 'queued': 0, 'running': 0}
                daily_data[date_key][item.status] += 1
            
            # Generate daily report
            report_text = "📊 Daily Usage Report (Last 7 days) - Local Database\n\n"
            
            total_requests = len(history_items)
            completed_requests = len([h for h in history_items if h.status == 'completed'])
            failed_requests = len([h for h in history_items if h.status == 'failed'])
            
            report_text += "🔢 Overall Summary:\n"
            report_text += f"  • Total requests: {total_requests:,}\n"
            report_text += f"  • Completed requests: {completed_requests:,}\n"
            report_text += f"  • Failed requests: {failed_requests:,}\n"
            
            if total_requests > 0:
                success_rate = (completed_requests / total_requests) * 100
                report_text += f"  • Success rate: {success_rate:.2f}%\n"
                report_text += f"  • Failure rate: {100 - success_rate:.2f}%\n"
            
            report_text += "\n📅 Daily Breakdown:\n"
            for date, counts in sorted(daily_data.items()):
                day_total = sum(counts.values())
                day_success_rate = (counts['completed'] / day_total * 100) if day_total > 0 else 0
                report_text += f"  • {date}: {day_total} requests ({day_success_rate:.1f}% success)\n"
                report_text += f"    - Completed: {counts['completed']}, Failed: {counts['failed']}\n"
            
            # Failure analysis from local data
            failed_items = [h for h in history_items if h.status == 'failed' and h.error_message]
            if failed_items:
                report_text += "\n❌ Common Failure Reasons:\n"
                error_counts = {}
                for item in failed_items:
                    # Extract error type from error message
                    error_msg = item.error_message[:50] + "..." if len(item.error_message) > 50 else item.error_message
                    error_counts[error_msg] = error_counts.get(error_msg, 0) + 1
                
                for error, count in sorted(error_counts.items(), key=lambda x: x[1], reverse=True)[:5]:
                    percentage = (count / len(failed_items)) * 100
                    report_text += f"  • {error}: {count} ({percentage:.1f}%)\n"
            
        elif range_param == '4w':
            # Get last 4 weeks of data
            four_weeks_ago = datetime.datetime.utcnow() - datetime.timedelta(weeks=4)
            history_items = GenerationHistory.query.filter(
                GenerationHistory.timestamp >= four_weeks_ago
            ).all()
            
            # Group by week
            weekly_data = {}
            for item in history_items:
                # Get week start (Monday)
                week_start = item.timestamp.date() - datetime.timedelta(days=item.timestamp.weekday())
                week_key = week_start.isoformat()
                if week_key not in weekly_data:
                    weekly_data[week_key] = {'completed': 0, 'failed': 0, 'queued': 0, 'running': 0}
                weekly_data[week_key][item.status] += 1
            
            report_text = "📊 Weekly Usage Report (Last 4 weeks) - Local Database\n\n"
            
            total_requests = len(history_items)
            completed_requests = len([h for h in history_items if h.status == 'completed'])
            failed_requests = len([h for h in history_items if h.status == 'failed'])
            
            report_text += "🔢 Overall Summary:\n"
            report_text += f"  • Total requests: {total_requests:,}\n"
            report_text += f"  • Completed requests: {completed_requests:,}\n"
            report_text += f"  • Failed requests: {failed_requests:,}\n"
            
            if total_requests > 0:
                success_rate = (completed_requests / total_requests) * 100
                report_text += f"  • Success rate: {success_rate:.2f}%\n"
            
            report_text += "\n📅 Weekly Breakdown:\n"
            for week_start, counts in sorted(weekly_data.items()):
                week_end = datetime.datetime.fromisoformat(week_start) + datetime.timedelta(days=6)
                week_total = sum(counts.values())
                week_success_rate = (counts['completed'] / week_total * 100) if week_total > 0 else 0
                report_text += f"  • Week {week_start} to {week_end.date()}: {week_total} requests ({week_success_rate:.1f}% success)\n"
        
        else:
            # Default simple report
            total_items = GenerationHistory.query.count()
            completed_items = GenerationHistory.query.filter_by(status='completed').count()
            failed_items = GenerationHistory.query.filter_by(status='failed').count()
            
            report_text = f"📊 Simple Usage Report:\n\n"
            report_text += f"  • Total requests in database: {total_items}\n"
            report_text += f"  • Completed: {completed_items}\n"
            report_text += f"  • Failed: {failed_items}\n"
            
            if total_items > 0:
                success_rate = (completed_items / total_items) * 100
                report_text += f"  • Success rate: {success_rate:.2f}%\n"
        
        # Add recommendations
        report_text += "\n💡 Note:\n"
        report_text += "  • This report is based on local database records\n"
        report_text += "  • For real-time Cloud Monitoring metrics, install: pip install google-cloud-monitoring\n"
        
        return jsonify({
            'report': report_text,
            'data': {
                'source': 'local_database',
                'total_requests': total_requests if 'total_requests' in locals() else 0,
                'completed_requests': completed_requests if 'completed_requests' in locals() else 0,
                'failed_requests': failed_requests if 'failed_requests' in locals() else 0
            }
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to generate usage report: {str(e)}'})

def veo_edit_internal(app_context, operation_id, prompt, parameters, mask_gcs, mask_mime_type, mask_mode, video_gcs, image_uri, last_frame_uri, camera_control):
    with app_context:
        history_item = GenerationHistory.query.filter_by(operation_id=operation_id).first()
        try:
            history_item.status = 'running'
            db.session.commit()

            op = generate_veo_video(
                project_id=PROJECT_ID,
                location=LOCATION,
                prompt=prompt,
                parameters=parameters,
                mask_gcs=mask_gcs,
                mask_mime_type=mask_mime_type,
                mask_mode=mask_mode,
                video_uri=video_gcs,
                image_uri=image_uri,
                last_frame_uri=last_frame_uri,
                camera_control=camera_control,
            )

            if "error" in op:
                history_item.status = 'failed'
                history_item.error_message = op["error"]["message"]
            elif "response" in op and "videos" in op["response"]:
                video_info = op["response"]["videos"][0]
                gcs_uri = video_info["gcsUri"]
                
                # Download the video from GCS to a local path
                gcs_bucket = gcs_uri.split('/')[2]
                gcs_blob = '/'.join(gcs_uri.split('/')[3:])
                local_path = os.path.join(VIDEO_DIR, f"{operation_id}.mp4")
                download_from_gcs(gcs_bucket, gcs_blob, local_path)

                history_item.status = 'completed'
                history_item.video_path = f"/{local_path}"
                history_item.output_payload = json.dumps(op['response'])
            else:
                history_item.status = 'failed'
                history_item.error_message = "Operation finished with no error but no video was generated."
        except Exception as e:
            history_item.status = 'failed'
            history_item.error_message = str(e)
        db.session.commit()


@app.route('/veo-edit', methods=['POST'])
def veo_edit_route():
    operation_id = f"veo_edit_op_{int(time.time() * 1000)}"
    
    prompt = request.form.get('prompt', '')
    video_gcs = request.form.get('video_gcs')
    mask_gcs = request.form.get('mask_gcs')
    mask_mime_type = request.form.get('mask_mime_type')
    mask_mode = request.form.get('mask_mode')
    aspect_ratio = request.form.get('aspect_ratio', '16:9')
    enhance_prompt = request.form.get('enhance_prompt', 'false').lower() == 'true'
    sample_count = request.form.get('sample_count', 1, type=int)
    duration = request.form.get('duration', 8, type=int)

    video_file = request.files.get('video_file')
    mask_file = request.files.get('mask_file')

    if not (video_gcs or video_file):
        return jsonify({'error': 'Video GCS URI or file is required.'}), 400
    if not (mask_gcs or mask_file):
        return jsonify({'error': 'Mask GCS URI or file is required.'}), 400

    try:
        # Handle file uploads
        if video_file:
            temp_video_path = os.path.join('static', 'uploads', f"{operation_id}_{video_file.filename}")
            video_file.save(temp_video_path)
            video_gcs = upload_veo_to_gcs(PROJECT_ID, GCS_BUCKET_NAME, temp_video_path, f"veo-edit-inputs/{operation_id}_{video_file.filename}")
            os.remove(temp_video_path)
            if not video_gcs:
                return jsonify({'error': 'Failed to upload video to GCS.'}), 500

        if mask_file:
            temp_mask_path = os.path.join('static', 'uploads', f"{operation_id}_{mask_file.filename}")
            mask_file.save(temp_mask_path)
            mask_gcs = upload_veo_to_gcs(PROJECT_ID, GCS_BUCKET_NAME, temp_mask_path, f"veo-edit-inputs/{operation_id}_{mask_file.filename}")
            os.remove(temp_mask_path)
            if not mask_gcs:
                return jsonify({'error': 'Failed to upload mask to GCS.'}), 500

        output_gcs_path = f"gs://{GCS_BUCKET_NAME}/veo-edit-outputs/"
        parameters = {
            "storageUri": output_gcs_path,
            "aspectRatio": aspect_ratio,
            "enhancePrompt": enhance_prompt,
            "sampleCount": sample_count,
            "durationSeconds": duration,
        }

        input_payload = {
            'prompt': prompt, 'video_gcs': video_gcs, 'mask_gcs': mask_gcs,
            'mask_mime_type': mask_mime_type, 'mask_mode': mask_mode, 'parameters': parameters
        }
        new_history = GenerationHistory(
            operation_id=operation_id,
            prompt=prompt or f"VEO Edit: {mask_mode}",
            status='queued',
            input_payload=json.dumps(input_payload),
            operation_type='veo_edit'
        )
        db.session.add(new_history)
        db.session.commit()

        thread = threading.Thread(target=veo_edit_internal, args=(
            app.app_context(), operation_id, prompt, parameters, mask_gcs, mask_mime_type, mask_mode, video_gcs, None, None, None
        ))
        thread.start()

        return jsonify({'operation_id': operation_id})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/veo-advanced-edit', methods=['POST'])
def veo_advanced_edit_route():
    operation_id = f"veo_advanced_op_{int(time.time() * 1000)}"
    
    prompt = request.form.get('prompt', '')
    aspect_ratio = request.form.get('aspect_ratio', '16:9')
    enhance_prompt = request.form.get('enhance_prompt', 'false').lower() == 'true'
    duration = request.form.get('duration', 8, type=int)
    camera_control = request.form.get('camera_control')

    image_gcs = request.form.get('image_gcs')
    video_gcs = request.form.get('video_gcs')
    last_frame_gcs = request.form.get('last_frame_gcs')

    image_file = request.files.get('image_file')
    video_file = request.files.get('video_file')
    last_frame_file = request.files.get('last_frame_file')

    try:
        # Handle file uploads
        if image_file:
            temp_image_path = os.path.join('static', 'uploads', f"{operation_id}_{image_file.filename}")
            image_file.save(temp_image_path)
            image_gcs = upload_veo_to_gcs(PROJECT_ID, GCS_BUCKET_NAME, temp_image_path, f"veo-advanced-inputs/{operation_id}_{image_file.filename}")
            os.remove(temp_image_path)
            if not image_gcs:
                return jsonify({'error': 'Failed to upload image to GCS.'}), 500

        if video_file:
            temp_video_path = os.path.join('static', 'uploads', f"{operation_id}_{video_file.filename}")
            video_file.save(temp_video_path)
            video_gcs = upload_veo_to_gcs(PROJECT_ID, GCS_BUCKET_NAME, temp_video_path, f"veo-advanced-inputs/{operation_id}_{video_file.filename}")
            os.remove(temp_video_path)
            if not video_gcs:
                return jsonify({'error': 'Failed to upload video to GCS.'}), 500

        if last_frame_file:
            temp_last_frame_path = os.path.join('static', 'uploads', f"{operation_id}_{last_frame_file.filename}")
            last_frame_file.save(temp_last_frame_path)
            last_frame_gcs = upload_veo_to_gcs(PROJECT_ID, GCS_BUCKET_NAME, temp_last_frame_path, f"veo-advanced-inputs/{operation_id}_{last_frame_file.filename}")
            os.remove(temp_last_frame_path)
            if not last_frame_gcs:
                return jsonify({'error': 'Failed to upload last frame to GCS.'}), 500

        output_gcs_path = f"gs://{GCS_BUCKET_NAME}/veo-advanced-outputs/"
        parameters = {
            "storageUri": output_gcs_path,
            "aspectRatio": aspect_ratio,
            "enhancePrompt": enhance_prompt,
            "durationSeconds": duration,
        }

        input_payload = {
            'prompt': prompt, 'video_gcs': video_gcs, 'image_gcs': image_gcs,
            'last_frame_gcs': last_frame_gcs, 'camera_control': camera_control, 'parameters': parameters
        }
        new_history = GenerationHistory(
            operation_id=operation_id,
            prompt=prompt or f"VEO Advanced Edit",
            status='queued',
            input_payload=json.dumps(input_payload),
            operation_type='veo_advanced_edit'
        )
        db.session.add(new_history)
        db.session.commit()

        thread = threading.Thread(target=veo_edit_internal, args=(
            app.app_context(), operation_id, prompt, parameters, None, None, None, video_gcs, image_gcs, last_frame_gcs, camera_control
        ))
        thread.start()

        return jsonify({'operation_id': operation_id})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/imagen-edit', methods=['POST'])
def imagen_edit_route():
    if not imagen_client:
        return jsonify({'error': 'Imagen client not initialized.'}), 500

    operation_id = f"imagen_edit_op_{int(time.time() * 1000)}"
    edit_prompt = request.form.get('prompt')
    edit_mode = request.form.get('edit_mode')
    mask_mode = request.form.get('mask_mode')
    
    original_image_file = request.files.get('original_image')
    mask_image_file = request.files.get('mask_image')

    if not original_image_file:
        return jsonify({'error': 'Original image is required.'}), 400

    original_image_bytes = original_image_file.read()
    mask_image_bytes = mask_image_file.read() if mask_image_file else None

    try:
        if edit_mode == "EDIT_MODE_DEFAULT": # Mask-free
            result = imagenedit.edit_image_mask_free(imagen_client, edit_prompt, original_image_bytes)
        else:
            result = imagenedit.edit_image_with_mask(
                client=imagen_client,
                edit_prompt=edit_prompt,
                original_image_bytes=original_image_bytes,
                mask_image_bytes=mask_image_bytes,
                mask_mode=mask_mode,
                edit_mode=edit_mode
            )

        edited_image_bytes = imagenedit.get_bytes_from_pil(result.generated_images[0].image._pil_image)
        
        # Save original and edited images
        original_image_filename = f"{operation_id}_original.png"
        original_image_save_path = os.path.join('static', 'uploads', original_image_filename)
        with open(original_image_save_path, 'wb') as f:
            f.write(original_image_bytes)
        
        edited_image_filename = f"{operation_id}_edited.png"
        edited_image_save_path = os.path.join('static', 'uploads', edited_image_filename)
        with open(edited_image_save_path, 'wb') as f:
            f.write(edited_image_bytes)

        # Save to history
        new_history = GenerationHistory(
            operation_id=operation_id,
            prompt=edit_prompt,
            status='completed',
            image_path=f"/{original_image_save_path}",
            output_payload=json.dumps({'edited_image_path': f"/{edited_image_save_path}"}),
            operation_type='imagen_edit'
        )
        db.session.add(new_history)
        db.session.commit()

        return jsonify({
            'original_image_url': f"/{original_image_save_path}",
            'edited_image_url': f"/{edited_image_save_path}"
        })

    except Exception as e:
        print(f"Error during Imagen edit: {e}")
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
