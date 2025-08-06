# -*- coding: utf-8 -*-
# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import time
import google.auth
import google.auth.transport.requests
import requests
from google.cloud import storage
import os

def upload_to_gcs(project_id, bucket_name, source_file_name, destination_blob_name):
    """Uploads a file to the bucket."""
    try:
        storage_client = storage.Client(project=project_id)
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(destination_blob_name)
        blob.upload_from_filename(source_file_name)
        return f"gs://{bucket_name}/{destination_blob_name}"
    except Exception as e:
        print(f"Error uploading to GCS: {e}")
        return None

def send_request_to_google_api(api_endpoint, data=None):
    """
    Sends an HTTP request to a Google API endpoint.
    """
    creds, project = google.auth.default()
    auth_req = google.auth.transport.requests.Request()
    creds.refresh(auth_req)
    access_token = creds.token

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    response = requests.post(api_endpoint, headers=headers, json=data)
    response.raise_for_status()
    return response.json()


def compose_videogen_request(
    prompt,
    parameters: dict,
    image_uri: str = "",
    video_uri: str = "",
    last_frame_uri: str = "",
    camera_control: str = "",
    mask_gcs: str = "",
    mask_mime_type: str = "",
    mask_mode: str = "",
):
    instance = {"prompt": prompt}
    if image_uri:
        instance["image"] = {"gcsUri": image_uri, "mimeType": "image/jpg"}
    if video_uri:
        instance["video"] = {"gcsUri": video_uri, "mimeType": "video/mp4"}
    if last_frame_uri:
        instance["lastFrame"] = {"gcsUri": last_frame_uri, "mimeType": "image/jpg"}
    if camera_control:
        instance["cameraControl"] = camera_control
    if mask_gcs:
        instance["mask"] = {"gcsUri": mask_gcs, "mimeType": mask_mime_type, "maskMode": mask_mode}
    request = {"instances": [instance], "parameters": parameters}
    return request


def fetch_operation(fetch_endpoint, lro_name):
    request = {"operationName": lro_name}
    for i in range(30):
        try:
            resp = send_request_to_google_api(fetch_endpoint, request)
            if "done" in resp and resp["done"]:
                return resp
            time.sleep(10)
        except Exception as e:
            print(f"Error fetching operation status: {e}")
            # Return a failed operation structure
            return {"done": True, "error": {"message": str(e)}}
    return {"done": True, "error": {"message": "Operation timed out."}}


def generate_video(
    project_id: str,
    location: str,
    prompt: str,
    parameters: dict,
    image_uri: str = "",
    video_uri: str = "",
    last_frame_uri: str = "",
    camera_control: str = "",
    mask_gcs: str = "",
    mask_mime_type: str = "",
    mask_mode: str = "",
):
    video_model = f"https://{location}-aiplatform.googleapis.com/v1beta1/projects/{project_id}/locations/{location}/publishers/google/models/veo-2.0-generate-exp"
    prediction_endpoint = f"{video_model}:predictLongRunning"
    fetch_endpoint = f"{video_model}:fetchPredictOperation"

    req = compose_videogen_request(
        prompt=prompt,
        parameters=parameters,
        image_uri=image_uri,
        video_uri=video_uri,
        last_frame_uri=last_frame_uri,
        camera_control=camera_control,
        mask_gcs=mask_gcs,
        mask_mime_type=mask_mime_type,
        mask_mode=mask_mode,
    )
    resp = send_request_to_google_api(prediction_endpoint, req)
    print(f"Started VEO editing operation: {resp}")
    return fetch_operation(fetch_endpoint, resp["name"])
