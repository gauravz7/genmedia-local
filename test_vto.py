import base64
import os
from google.cloud import aiplatform
from PIL import Image

# --- Common Configuration ---
PROJECT_ID = "cloud-lvm-training-nonprod"
LOCATION = "us-central1"
PERSON_IMAGE_PATH = "Person.png"
PRODUCT_IMAGE_PATH = "Product.png"
MASK_IMAGE_PATH = "mask.png"

def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return image_file.read()

def get_image_info(image_path):
    with Image.open(image_path) as img:
        width, height = img.size
        size_bytes = os.path.getsize(image_path)
        print(f"Image: {os.path.basename(image_path)}, Dimensions: {width}x{height}, Size: {size_bytes} bytes")
    return encode_image(image_path)

print("--- Image Information ---")
person_image_bytes = get_image_info(PERSON_IMAGE_PATH)
product_image_bytes = get_image_info(PRODUCT_IMAGE_PATH)
mask_image_bytes = get_image_info(MASK_IMAGE_PATH)

# --- Test Internal Endpoint (predict) ---
print("--- Testing Internal Endpoint (predict) ---")
try:
    api_regional_endpoint = f"{LOCATION}-autopush-aiplatform.sandbox.googleapis.com"
    client_options = {"api_endpoint": api_regional_endpoint}
    prediction_client = aiplatform.gapic.PredictionServiceClient(client_options=client_options)

    model_endpoint = f"projects/{PROJECT_ID}/locations/{LOCATION}/publishers/google/models/virtual-try-on-exp-05-31"
    #
    # 
    # model_endpoint = f"projects/{PROJECT_ID}/locations/{LOCATION}/publishers/google/models/virtual-try-on-preview-08-04"

    
    encoded_person_image = base64.b64encode(person_image_bytes).decode("utf-8")
    encoded_product_image = base64.b64encode(product_image_bytes).decode("utf-8")
    encoded_mask_image = base64.b64encode(mask_image_bytes).decode("utf-8")

    instance = {
        "prompt": "A photo of a woman wearing a blue denim jacket.",
        "personImage": {
            "image": {"bytesBase64Encoded": encoded_person_image},
            "description": "A woman with brown hair and a light skin tone."
        },
        "productImages": [{
            "image": {"bytesBase64Encoded": encoded_product_image},
            "maskImage": {"bytesBase64Encoded": encoded_mask_image},
            "productConfig": {"productDescription": "A blue denim jacket."}
        }],
    }
    parameters = {"returnMask": False}

    response_internal = prediction_client.predict(
        endpoint=model_endpoint,
        instances=[instance],
        parameters=parameters
    )
    print("Internal endpoint response:")
    #print(response_internal)
    print("\nSuccess")

except Exception as e:
    print(f"Error calling Internal endpoint: {e}")
