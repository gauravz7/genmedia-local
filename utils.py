import base64
import io
import json
import os
import time
import requests
import google.auth
import google.auth.transport.requests
from google.cloud import storage
from google.genai import types
from PIL import Image
from config import Config
from extensions import db
from models import GenerationHistory
import vertexai
from google import genai
from segmentation import initialize_segmentation_model
from vto import get_vto_client
import imagenedit

def upload_to_gcs(file_bytes, destination_blob_name):
    """Uploads a file to the bucket."""
    try:
        storage_client = storage.Client(project=Config.PROJECT_ID)
        bucket = storage_client.bucket(Config.GCS_BUCKET_NAME)
        blob = bucket.blob(destination_blob_name)
        blob.upload_from_string(file_bytes)
        return f"gs://{Config.GCS_BUCKET_NAME}/{destination_blob_name}"
    except Exception as e:
        print(f"Error uploading to GCS: {e}")
        return None

def download_from_gcs(bucket_name, source_blob_name, destination_file_name):
    """Downloads a file from the bucket."""
    try:
        storage_client = storage.Client(project=Config.PROJECT_ID)
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(source_blob_name)
        blob.download_to_filename(destination_file_name)
        return destination_file_name
    except Exception as e:
        print(f"Error downloading from GCS: {e}")
        return None

def generate_veo_prompt_internal(client, user_prompt, system_instructions, image_data=None):
    print(f"--- [DEBUG] Starting VEO Prompt Generation ---")
    if not client or not Config.GEMINI_MODEL:
        print(f"[DEBUG] VEO prompt generation failed: Gemini model not initialized.")
        return "Error: Gemini model not initialized."
    try:
        print(f"[DEBUG] Generating VEO prompt with model: {Config.GEMINI_MODEL}")
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
        response = client.models.generate_content(model=Config.GEMINI_MODEL, contents=content)
        print(f"[DEBUG] Received response from Vertex AI.")
        return response.text
    except Exception as e:
        print(f"--- [DEBUG] ERROR during VEO prompt generation: {e} ---")
        return f"Error generating prompt: {e}"

def generate_video_internal(app_context, client, prompt, operation_id, model_name, seed, aspect_ratio, negative_prompt):
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
                video_bytes = generated_video.video.video_bytes
                local_path = os.path.join(Config.VIDEO_DIR, f"{operation_id}.mp4")
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
            url = f"https://{api_endpoint}/v1/projects/{Config.PROJECT_ID}/locations/{Config.LOCATION}/publishers/google/models/{model_name}:predictLongRunning"

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
            
            fetch_url = f"https://{api_endpoint}/v1/projects/{Config.PROJECT_ID}/locations/{Config.LOCATION}/publishers/google/models/{model_name}:fetchPredictOperation"
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
                    local_path = os.path.join(Config.VIDEO_DIR, f"{operation_id}.mp4")
                    with open(local_path, "wb") as f:
                        f.write(video_bytes)
                    history_item.status = 'completed'
                    history_item.video_path = f"/{local_path}"
                else:
                    history_item.status = 'failed'
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
