import base64
from prism import call_product_recontext, prediction_to_pil_image

def test_product_recontext():
    """
    Tests the product recontextualization feature.
    """
    image_path = "static/uploads/img_op_1754168865772.png"
    prompt = "A stylish handbag on a wooden table, with a coffee cup and a magazine."
    product_description = "A red leather handbag."

    try:
        with open(image_path, "rb") as image_file:
            image_bytes = image_file.read()
        
        encoded_image = base64.b64encode(image_bytes).decode("utf-8")

        response = call_product_recontext(
            image_bytes_list=[encoded_image],
            prompt=prompt,
            product_description=product_description,
            sample_count=1,
            safety_setting="block_low_and_above",
            person_generation="allow_all"
        )

        print("API Response:")
        print(response)

        if response and response.predictions:
            for i, prediction in enumerate(response.predictions):
                if "bytesBase64Encoded" in prediction:
                    image = prediction_to_pil_image(prediction)
                    image.save(f"test_prism_output_{i}.png")
                    print(f"Saved generated image to test_prism_output_{i}.png")
                else:
                    print(f"Prediction {i} did not contain image data.")
        else:
            print("No predictions were returned.")

    except FileNotFoundError:
        print(f"Error: Test image not found at {image_path}")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    test_product_recontext()
