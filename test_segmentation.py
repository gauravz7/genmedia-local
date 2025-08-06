import os
import base64
import vertexai
from vertexai.preview.vision_models import Image, ImageSegmentationModel
import argparse

# --- Configuration ---
PROJECT_ID = os.environ.get("GCP_PROJECT", "vital-octagon-19612")
LOCATION = "us-central1"
IMAGE_FILE = "static/uploads/img_op_1754168865772.png"

def run_standalone_test(mode, prompt=None):
    """
    Runs a standalone image segmentation test for a specific mode.
    """
    output_file = f"test_mask_output_{mode}.png"
    print(f"--- Starting Standalone Segmentation Test for mode: '{mode}' ---")

    # 1. Initialize Vertex AI
    print(f"--- Initializing Vertex AI for Project: {PROJECT_ID}, Location: {LOCATION} ---")
    try:
        vertexai.init(project=PROJECT_ID, location=LOCATION)
        print("--- Vertex AI Initialized Successfully ---")
    except Exception as e:
        print(f"--- CRITICAL ERROR: Failed to initialize Vertex AI: {e} ---")
        return

    # 2. Initialize the Model
    print("--- Initializing ImageSegmentationModel ---")
    try:
        model = ImageSegmentationModel.from_pretrained("image-segmentation-001")
        print("--- Model Initialized Successfully ---")
    except Exception as e:
        print(f"--- CRITICAL ERROR: Failed to initialize model: {e} ---")
        return

    # 3. Load the Image
    if not os.path.exists(IMAGE_FILE):
        print(f"--- CRITICAL ERROR: Image file not found at '{IMAGE_FILE}' ---")
        return
    print(f"--- Loading image: {IMAGE_FILE} ---")
    try:
        base_image = Image.load_from_file(IMAGE_FILE)
        print("--- Image Loaded Successfully ---")
    except Exception as e:
        print(f"--- CRITICAL ERROR: Failed to load image: {e} ---")
        return

    # 4. Run Segmentation
    print(f"--- Performing segmentation with mode: '{mode}' and prompt: '{prompt}' ---")
    try:
        if mode in ["semantic", "prompt"]:
            response = model.segment_image(
                base_image,
                mode=mode,
                prompt=prompt
            )
        else:
            response = model.segment_image(
                base_image,
                mode=mode
            )
        print("--- Segmentation API call successful ---")
        
        if not isinstance(response, list):
            response = [response]

        # 5. Process and Save the Mask
        if not response:
            print("--- TEST FAILED: No response from model. ---")
            return

        print(f"--- Received {len(response)} prediction(s) ---")
        
        # For this test, we'll just save the first mask if it exists
        first_prediction = response[0]
        if hasattr(first_prediction, 'mask') and hasattr(first_prediction.mask, '_image_bytes'):
            mask_bytes = first_prediction.mask._image_bytes
            with open(output_file, "wb") as f:
                f.write(mask_bytes)
            print(f"--- SUCCESS: First mask saved to '{output_file}' ---")
        else:
            print(f"--- TEST FAILED: Could not extract mask from prediction: {first_prediction} ---")

    except Exception as e:
        print(f"--- CRITICAL ERROR during segmentation: {e} ---")

if __name__ == '__main__':
    modes_to_test = ["foreground", "background", "semantic", "prompt"]
    for mode in modes_to_test:
        if mode in ["semantic", "prompt"]:
            run_standalone_test(mode, prompt="clothing")
        else:
            run_standalone_test(mode)
        print("\n" + "="*50 + "\n")
