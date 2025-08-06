import base64
import io
import timeit
from google.cloud import aiplatform
from PIL import Image

def get_vto_client(location="us-central1"):
    """Initializes the VTO PredictionServiceClient."""
    api_regional_endpoint = f"{location}-autopush-aiplatform.sandbox.googleapis.com"
    client_options = {"api_endpoint": api_regional_endpoint}
    return aiplatform.gapic.PredictionServiceClient(client_options=client_options)

def call_virtual_try_on(
    client,
    project_id,
    location,
    model_endpoint_name="virtual-try-on-exp-05-31",
    person_image_bytes=None,
    product_image_bytes=None,
    mask_image_bytes=None,
    person_image_uri=None,
    product_image_uri=None,
    prompt=None,
    person_description=None,
    product_description=None,
    sample_count=None,
    base_steps=None,
    seed=None,
):
    """
    Calls the Virtual Try-On API.
    """
    model_endpoint = f"projects/{project_id}/locations/{location}/publishers/google/models/{model_endpoint_name}"
    
    instance = {}

    if prompt:
        instance["prompt"] = prompt

    if person_image_uri:
        instance["personImage"] = {"image": {"gcsUri": person_image_uri}}
    elif person_image_bytes:
        instance["personImage"] = {"image": {"bytesBase64Encoded": base64.b64encode(person_image_bytes).decode("utf-8")}}
    else:
        raise ValueError("Either person_image_bytes or person_image_uri must be provided.")

    if person_description:
        instance["personImage"]["description"] = person_description

    if product_image_uri:
        instance["productImages"] = [{"image": {"gcsUri": product_image_uri}}]
    elif product_image_bytes:
        instance["productImages"] = [{"image": {"bytesBase64Encoded": base64.b64encode(product_image_bytes).decode("utf-8")}}]
    else:
        raise ValueError("Either product_image_bytes or product_image_uri must be provided.")

    if mask_image_bytes:
        instance["productImages"][0]["maskImage"] = {"bytesBase64Encoded": base64.b64encode(mask_image_bytes).decode("utf-8")}

    if product_description:
        if "productConfig" not in instance["productImages"][0]:
            instance["productImages"][0]["productConfig"] = {}
        instance["productImages"][0]["productConfig"]["productDescription"] = product_description

    parameters = {"returnMask": True}
    if sample_count:
        parameters["sampleCount"] = sample_count
    if base_steps:
        parameters["baseSteps"] = base_steps
    if seed:
        parameters["seed"] = seed

    start = timeit.default_timer()
    response = client.predict(
        endpoint=model_endpoint,
        instances=[instance],
        parameters=parameters
    )
    end = timeit.default_timer()
    print(f"Virtual Try-On took {end - start:.2f}s.")

    return response

def prediction_to_pil_image(prediction) -> Image:
    encoded_mask_string = prediction["bytesBase64Encoded"]
    mask_bytes = base64.b64decode(encoded_mask_string)
    mask_pil = Image.open(io.BytesIO(mask_bytes))
    return mask_pil
