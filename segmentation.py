import os
import base64
import vertexai
from vertexai.preview.vision_models import Image, ImageSegmentationModel

def initialize_segmentation_model():
    """Initializes the Vertex AI Image Segmentation Model."""
    try:
        # The model name is fixed according to the documentation
        model_name = "image-segmentation-001"
        segmentation_model = ImageSegmentationModel.from_pretrained(model_name)
        return segmentation_model
    except Exception as e:
        print(f"Error initializing segmentation model: {e}")
        return None

def segment_image(
    model: ImageSegmentationModel,
    input_file: str,
    segmentation_mode: str,
    prompt: str = None,
    confidence_threshold: float = 0.5,
    mask_dilation: float = 0.0
):
    """
    Performs image segmentation using an initialized Vertex AI model.

    Args:
        model (ImageSegmentationModel): The initialized image segmentation model.
        input_file (str): Path to the input image file.
        segmentation_mode (str): The segmentation mode ('foreground', 'background', 'semantic', 'prompt').
        prompt (str, optional): The text prompt for 'semantic' or 'prompt' mode. Defaults to None.
        confidence_threshold (float, optional): Confidence threshold for 'prompt' mode. Defaults to 0.5.
        mask_dilation (float, optional): Mask dilation factor. Defaults to 0.0.

    Returns:
        A list of base64 encoded mask images or an error message.
    """
    try:
        image = Image.load_from_file(input_file)

        if segmentation_mode in ["semantic", "prompt"]:
            if not prompt:
                return {"error": f"Prompt is required for '{segmentation_mode}' mode."}
            
            response = model.segment_image(
                image,
                mode=segmentation_mode,
                prompt=prompt,
                confidence_threshold=confidence_threshold,
                mask_dilation=mask_dilation,
            )
        else: # foreground/background
            response = model.segment_image(
                image,
                mode=segmentation_mode,
                mask_dilation=mask_dilation,
            )

        base64_masks = []
        if hasattr(response, '_prediction_response') and hasattr(response._prediction_response, 'predictions'):
            for prediction in response._prediction_response.predictions:
                if 'bytesBase64Encoded' in prediction:
                    base64_masks.append(prediction['bytesBase64Encoded'])
        
        return {"masks": base64_masks}

    except Exception as e:
        return {"error": f"An error occurred during segmentation: {e}"}
