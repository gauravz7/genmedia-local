# -*- coding: utf-8 -*-
# Copyright 2024 Google LLC
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

import io
import os
import urllib

from google import genai
from google.genai.types import (
    EditImageConfig,
    GenerateImagesConfig,
    Image,
    MaskReferenceConfig,
    MaskReferenceImage,
    RawReferenceImage,
)
from PIL import Image as PIL_Image


def get_bytes_from_pil(image: PIL_Image) -> bytes:
    """Gets the image bytes from a PIL Image object."""
    byte_io_png = io.BytesIO()
    image.save(byte_io_png, "PNG")
    return byte_io_png.getvalue()


def initialize_imagen_client(project_id, location):
    """Initializes the Imagen client."""
    return genai.Client(vertexai=True, project=project_id, location=location)


def generate_image(client, prompt, aspect_ratio="1:1"):
    """Generates an image using Imagen 3."""
    return client.models.generate_images(
        model="imagen-3.0-generate-002",
        prompt=prompt,
        config=GenerateImagesConfig(
            number_of_images=1,
            aspect_ratio=aspect_ratio,
            safety_filter_level="BLOCK_MEDIUM_AND_ABOVE",
            person_generation="DONT_ALLOW",
        ),
    )


def inpainting_insert(
    client,
    edit_prompt,
    original_image,
    mask_image=None,
    mask_mode="MASK_MODE_FOREGROUND",
    segmentation_classes=None,
    mask_dilation=0.1,
):
    """Edits an image with inpainting insert."""
    raw_ref_image = RawReferenceImage(reference_image=original_image, reference_id=0)
    mask_config = MaskReferenceConfig(mask_mode=mask_mode, mask_dilation=mask_dilation)
    if segmentation_classes:
        mask_config.segmentation_classes = segmentation_classes

    mask_ref_image = MaskReferenceImage(
        reference_id=1,
        reference_image=mask_image,
        config=mask_config,
    )
    return client.models.edit_image(
        model="imagen-3.0-capability-001",
        prompt=edit_prompt,
        reference_images=[raw_ref_image, mask_ref_image],
        config=EditImageConfig(
            edit_mode="EDIT_MODE_INPAINT_INSERTION",
            number_of_images=1,
            safety_filter_level="BLOCK_MEDIUM_AND_ABOVE",
            person_generation="ALLOW_ADULT",
        ),
    )


def inpainting_remove(client, original_image, segmentation_classes):
    """Removes content from an image using inpainting."""
    raw_ref_image = RawReferenceImage(reference_image=original_image, reference_id=0)
    mask_ref_image = MaskReferenceImage(
        reference_id=1,
        reference_image=None,
        config=MaskReferenceConfig(
            mask_mode="MASK_MODE_SEMANTIC", segmentation_classes=segmentation_classes
        ),
    )
    return client.models.edit_image(
        model="imagen-3.0-capability-001",
        prompt="",
        reference_images=[raw_ref_image, mask_ref_image],
        config=EditImageConfig(
            edit_mode="EDIT_MODE_INPAINT_REMOVAL",
            number_of_images=1,
            safety_filter_level="BLOCK_MEDIUM_AND_ABOVE",
            person_generation="ALLOW_ADULT",
        ),
    )


def product_background_swap(client, prompt, product_image):
    """Swaps the background of a product image."""
    raw_ref_image = RawReferenceImage(reference_image=product_image, reference_id=0)
    mask_ref_image = MaskReferenceImage(
        reference_id=1,
        reference_image=None,
        config=MaskReferenceConfig(mask_mode="MASK_MODE_BACKGROUND"),
    )
    return client.models.edit_image(
        model="imagen-3.0-capability-001",
        prompt=prompt,
        reference_images=[raw_ref_image, mask_ref_image],
        config=EditImageConfig(
            edit_mode="EDIT_MODE_BGSWAP",
            number_of_images=1,
            seed=1,
            safety_filter_level="BLOCK_MEDIUM_AND_ABOVE",
            person_generation="ALLOW_ADULT",
        ),
    )


def outpainting(client, prompt, initial_image, target_size=(1536, 1536)):
    """Expands an image using outpainting."""
    mask = PIL_Image.new("L", initial_image._pil_image.size, 0)
    image_pil_outpaint, mask_pil_outpaint = pad_image_and_mask(
        initial_image._pil_image,
        mask,
        target_size,
        0,
        0,
    )
    image_pil_outpaint_image = Image(image_bytes=get_bytes_from_pil(image_pil_outpaint))
    mask_pil_outpaint_image = Image(image_bytes=get_bytes_from_pil(mask_pil_outpaint))

    raw_ref_image = RawReferenceImage(
        reference_image=image_pil_outpaint_image, reference_id=0
    )
    mask_ref_image = MaskReferenceImage(
        reference_id=1,
        reference_image=mask_pil_outpaint_image,
        config=MaskReferenceConfig(
            mask_mode="MASK_MODE_USER_PROVIDED",
            mask_dilation=0.03,
        ),
    )
    return client.models.edit_image(
        model="imagen-3.0-capability-001",
        prompt=prompt,
        reference_images=[raw_ref_image, mask_ref_image],
        config=EditImageConfig(
            edit_mode="EDIT_MODE_OUTPAINT",
            number_of_images=1,
            safety_filter_level="BLOCK_MEDIUM_AND_ABOVE",
            person_generation="ALLOW_ADULT",
        ),
    )


def mask_free_edit(client, prompt, original_image):
    """Edits an image without a mask."""
    raw_ref_image = RawReferenceImage(reference_image=original_image, reference_id=0)
    return client.models.edit_image(
        model="imagen-3.0-capability-001",
        prompt=prompt,
        reference_images=[raw_ref_image],
        config=EditImageConfig(
            edit_mode="EDIT_MODE_DEFAULT",
            number_of_images=1,
            safety_filter_level="BLOCK_MEDIUM_AND_ABOVE",
            person_generation="ALLOW_ADULT",
        ),
    )


def pad_to_target_size(
    source_image,
    target_size=(1536, 1536),
    mode="RGB",
    vertical_offset_ratio=0,
    horizontal_offset_ratio=0,
    fill_val=255,
):
    """Pads an image for outpainting."""
    orig_image_size_w, orig_image_size_h = source_image.size
    target_size_w, target_size_h = target_size

    insert_pt_x = (target_size_w - orig_image_size_w) // 2 + int(
        horizontal_offset_ratio * target_size_w
    )
    insert_pt_y = (target_size_h - orig_image_size_h) // 2 + int(
        vertical_offset_ratio * target_size_h
    )
    insert_pt_x = min(insert_pt_x, target_size_w - orig_image_size_w)
    insert_pt_y = min(insert_pt_y, target_size_h - orig_image_size_h)

    if mode == "RGB":
        source_image_padded = PIL_Image.new(
            mode, target_size, color=(fill_val, fill_val, fill_val)
        )
    elif mode == "L":
        source_image_padded = PIL_Image.new(mode, target_size, color=(fill_val))
    else:
        raise ValueError("source image mode must be RGB or L.")

    source_image_padded.paste(source_image, (insert_pt_x, insert_pt_y))
    return source_image_padded


def pad_image_and_mask(
    image_pil: PIL_Image,
    mask_pil: PIL_Image,
    target_size,
    vertical_offset_ratio,
    horizontal_offset_ratio,
):
    """Pads and resizes image and mask to the same target size."""
    image_pil.thumbnail(target_size)
    mask_pil.thumbnail(target_size)

    image_pil = pad_to_target_size(
        image_pil,
        target_size=target_size,
        mode="RGB",
        vertical_offset_ratio=vertical_offset_ratio,
        horizontal_offset_ratio=horizontal_offset_ratio,
        fill_val=0,
    )
    mask_pil = pad_to_target_size(
        mask_pil,
        target_size=target_size,
        mode="L",
        vertical_offset_ratio=vertical_offset_ratio,
        horizontal_offset_ratio=horizontal_offset_ratio,
        fill_val=255,
    )
    return image_pil, mask_pil
