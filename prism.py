import base64
import io
import re
import timeit
from typing import Any, Dict

from PIL import Image
from google.cloud import aiplatform
from google.cloud.aiplatform.gapic import PredictResponse
from google.cloud import storage

PROJECT_ID = "cloud-lvm-training-nonprod"
LOCATION = "us-central1"

aiplatform.init(project=PROJECT_ID, location=LOCATION)

api_regional_endpoint = f"{LOCATION}-aiplatform.googleapis.com"
client_options = {"api_endpoint": api_regional_endpoint}
client = aiplatform.gapic.PredictionServiceClient(client_options=client_options)

model_endpoint = f"projects/{PROJECT_ID}/locations/{LOCATION}/publishers/google/models/imagen-product-recontext-preview-06-30"
print(f"Prediction client initiated on project {PROJECT_ID} in {LOCATION}.")


def prediction_to_pil_image(
    prediction: PredictResponse,
) -> Image.Image:
    encoded_bytes_string = prediction["bytesBase64Encoded"]
    decoded_image_bytes = base64.b64decode(encoded_bytes_string)
    image_pil = Image.open(io.BytesIO(decoded_image_bytes))
    return image_pil


def download_gcs_image_bytes(uri: str) -> bytes:
    matched = re.match(r"gs://(.*?)/(.*)", uri)

    if matched:
        bucket_name = matched.group(1)
        object_name = matched.group(2)
    else:
        raise ValueError(f"Invalid GCS URI format: {uri}")

    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(object_name)
    return blob.download_as_bytes()


def call_product_recontext(
    image_bytes_list=None,
    image_uris_list=None,
    prompt=None,
    product_description=None,
    disable_prompt_enhancement: bool = False,
    sample_count: int = 1,
    base_steps=None,
    safety_setting=None,
    person_generation=None,
    aspect_ratio=None,
    resolution=None,
    seed=None,
) -> PredictResponse:
    instances = []

    instance: Dict[str, Any] = {"productImages": []}

    if image_bytes_list:
        for product_image_bytes in image_bytes_list:
            product_image = {"image": {"bytesBase64Encoded": product_image_bytes}}
            instance["productImages"].append(product_image)

    if image_uris_list:
        for product_image_uri in image_uris_list:
            product_image = {"image": {"gcsUri": product_image_uri}}
            instance["productImages"].append(product_image)

    if len(instance["productImages"]) == 0:
        raise ValueError(
            "No product images provided. At least one image must be provided."
        )

    if product_description:
        instance["productImages"][0]["productConfig"] = {
            "productDescription": product_description
        }

    if prompt:
        instance["prompt"] = prompt

    parameters = {"sampleCount": sample_count}

    if base_steps:
        parameters["baseSteps"] = base_steps

    if aspect_ratio:
        parameters["aspectRatio"] = aspect_ratio

    if resolution:
        parameters["resolution"] = resolution

    if seed:
        parameters["seed"] = seed

    if safety_setting is not None:
        parameters["safetySetting"] = safety_setting

    if person_generation is not None:
        parameters["personGeneration"] = person_generation

    if disable_prompt_enhancement:
        parameters["enhancePrompt"] = False

    instances.append(instance)

    start = timeit.default_timer()

    response = client.predict(
        endpoint=model_endpoint, instances=instances, parameters=parameters
    )
    end = timeit.default_timer()
    print(f"Product Recontextualization took {end - start:.2f}s.")

    return response
