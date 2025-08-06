import unittest
from unittest.mock import MagicMock, patch
from PIL import Image as PIL_Image
from google.genai.types import Image
import imagenedit
import os
import urllib.request

class TestImagenEdit(unittest.TestCase):

    def setUp(self):
        self.mock_client = MagicMock()
        self.test_image_pil = PIL_Image.new('RGB', (100, 100), color = 'red')
        self.test_image_bytes = imagenedit.get_bytes_from_pil(self.test_image_pil)
        self.test_image = Image(image_bytes=self.test_image_bytes)

    def test_generate_image(self):
        self.mock_client.models.generate_images.return_value = "Generated Image"
        result = imagenedit.generate_image(self.mock_client, "a test prompt")
        self.assertEqual(result, "Generated Image")
        self.mock_client.models.generate_images.assert_called_once()

    def test_inpainting_insert(self):
        self.mock_client.models.edit_image.return_value = "Inpainted Image"
        result = imagenedit.inpainting_insert(self.mock_client, "a test prompt", self.test_image)
        self.assertEqual(result, "Inpainted Image")
        self.mock_client.models.edit_image.assert_called_once()

    def test_inpainting_remove(self):
        self.mock_client.models.edit_image.return_value = "Removed Content Image"
        result = imagenedit.inpainting_remove(self.mock_client, self.test_image, segmentation_classes=[85])
        self.assertEqual(result, "Removed Content Image")
        self.mock_client.models.edit_image.assert_called_once()

    def test_product_background_swap(self):
        self.mock_client.models.edit_image.return_value = "Background Swapped Image"
        result = imagenedit.product_background_swap(self.mock_client, "a test prompt", self.test_image)
        self.assertEqual(result, "Background Swapped Image")
        self.mock_client.models.edit_image.assert_called_once()

    @patch('imagenedit.pad_image_and_mask', return_value=(PIL_Image.new('RGB', (1536, 1536)), PIL_Image.new('L', (1536, 1536))))
    def test_outpainting(self, mock_pad):
        self.mock_client.models.edit_image.return_value = "Outpainted Image"
        # Create a mock PIL image with a _pil_image attribute
        mock_initial_image = MagicMock()
        mock_initial_image._pil_image = self.test_image_pil
        result = imagenedit.outpainting(self.mock_client, "a test prompt", mock_initial_image)
        self.assertEqual(result, "Outpainted Image")
        self.mock_client.models.edit_image.assert_called_once()


    def test_mask_free_edit(self):
        self.mock_client.models.edit_image.return_value = "Mask-Free Edited Image"
        result = imagenedit.mask_free_edit(self.mock_client, "a test prompt", self.test_image)
        self.assertEqual(result, "Mask-Free Edited Image")
        self.mock_client.models.edit_image.assert_called_once()

    def test_mask_free_edit_real_image(self):
        PROJECT_ID = os.environ.get("GOOGLE_CLOUD_PROJECT")
        LOCATION = os.environ.get("GOOGLE_CLOUD_REGION", "us-central1")
        
        if not PROJECT_ID:
            print("\nSkipping real image test: GOOGLE_CLOUD_PROJECT environment variable not set.")
            self.skipTest("GOOGLE_CLOUD_PROJECT environment variable not set.")

        client = imagenedit.initialize_imagen_client(PROJECT_ID, LOCATION)
        
        image_url = "https://storage.googleapis.com/cloud-samples-data/generative-ai/image/latte.jpg"
        with urllib.request.urlopen(image_url) as url:
            original_pil = PIL_Image.open(url)

        original_image = Image(image_bytes=imagenedit.get_bytes_from_pil(original_pil))
        
        prompt = "a cup of black coffee"
        
        edited_image_response = imagenedit.mask_free_edit(client, prompt, original_image)
        
        self.assertIsNotNone(edited_image_response)
        self.assertGreater(len(edited_image_response.generated_images), 0)
        
        edited_pil = edited_image_response.generated_images[0].image._pil_image
        
        output_path = "edited_latte.png"
        edited_pil.save(output_path)
        
        self.assertTrue(os.path.exists(output_path))
        print(f"Edited image saved to {output_path}")


if __name__ == '__main__':
    unittest.main()
