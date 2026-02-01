import os
from datetime import datetime
import json

from common import prompt
from common.gemini import Gemini


class ImageGenerator:
    def __init__(self, output_dir):
        self.output_dir = output_dir
        self.gemini = Gemini()
        os.makedirs(self.output_dir, exist_ok=True)

    def change_attributes(self, image_path, instructions, show_ui=True):
        """Changes the color or orientation of a furniture image."""
        p = prompt.CHANGE_ATTRIBUTES.format(instructions=", ".join(instructions))
        generated_image_data, _ = self.gemini.call_image_generator(prompt=p, image_files=[image_path])

        output_path = self._get_output_path(image_path, "_changed")
        saved_files = self._save_image_from_data(generated_image_data, output_path)
        if show_ui:
            self.show_image_popup(product_image_path=image_path, save_image_path=saved_files)
        return saved_files

    def create_thumbnail_with_metadata(self, image_path, metadata_path, show_ui=True):
        """Generates a thumbnail with text overlay or a scene based on the description."""
        with open(metadata_path, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
        
        description = metadata.get("description", "")
        if isinstance(description, dict):
            description = description.get("description", "")

        p = prompt.CREATE_THUMBNAIL_WITH_METADATA.format(metadata=description)

        generated_image_data, _ = self.gemini.call_image_generator(prompt=p, image_files=[image_path])

        output_path = self._get_output_path(image_path, "_thumbnail_meta")
        saved_files = self._save_image_from_data(generated_image_data, output_path)
        if show_ui:
            self.show_image_popup(product_image_path=image_path, save_image_path=saved_files)
        return saved_files

    def apply_style_from_reference(self, product_image_path, reference_image_paths, show_ui=True):
        """Uses a reference image for style transfer."""
        p = prompt.APPLY_STYLE_FROM_REFERENCE

        all_image_files = [product_image_path] + reference_image_paths
        generated_image_data, _ = self.gemini.call_image_generator(prompt=p, image_files=all_image_files)

        output_path = self._get_output_path(product_image_path, "_styled")
        saved_files = self._save_image_from_data(generated_image_data, output_path)
        if show_ui:
            self.show_image_popup(product_image_path=product_image_path, reference_image_path=reference_image_paths, save_image_path=saved_files)
        return saved_files

    def replace_object_in_reference(self, product_image_path, reference_image_paths, show_ui=True):
        """Inpaints the product into a reference scene."""
        p = prompt.REPLACE_OBJECT_IN_REFERENCE.format(object_to_replace=product_image_path)

        all_image_files = [product_image_path] + reference_image_paths
        generated_image_data, _ = self.gemini.call_image_generator(prompt=p, image_files=all_image_files)

        output_path = self._get_output_path(product_image_path, "_replaced")
        saved_files = self._save_image_from_data(generated_image_data, output_path)
        if show_ui:
            self.show_image_popup(product_image_path=product_image_path, reference_image_path=reference_image_paths, save_image_path=saved_files)
        return saved_files

    def create_interior_scene(self, product_image_paths, show_ui=True):
        """Combines multiple products into one scene."""

        p = prompt.CREATE_INTERIOR_SCENE
        generated_image_data, _ = self.gemini.call_image_generator(prompt=p, image_files=product_image_paths)

        output_path = os.path.join(self.output_dir, "interior_scene.png")
        saved_files = self._save_image_from_data(generated_image_data, output_path)
        if show_ui:
            self.show_image_popup(product_image_path=product_image_paths, save_image_path=saved_files)
        return saved_files

    def _get_output_path(self, original_path, suffix):
        base, ext = os.path.splitext(os.path.basename(original_path))
        return os.path.join(self.output_dir, f"{base}{suffix}{ext}")

    def _save_image_from_data(self, image_data, output_path):
        saved_files = []
        if isinstance(image_data, list):
            for data in image_data:
                with open(output_path, 'wb') as f:
                    f.write(data.data)
                print(f"Image saved to {output_path}")
                saved_files.append(output_path)

        return saved_files



if __name__ == '__main__':

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = "./output/{}".format(timestamp)

    meta_dir = './output/meta'
    input_dir = './resource/가구'
    refer_dir = './resource/레퍼런스'
    generator = ImageGenerator(output_dir=output_dir)

    # # 1. Change Attributes
    # generator.change_attributes(
    #     image_path=f'{input_dir}/의자1.jpg',
    #     instructions=['검정색 의자를 흰색 으로 변경하고, 화면의 우측 컷으로 교체 해주세요.']
    # )
    #
    # ## 2. Create Thumbnail with Metadata
    # generator.create_thumbnail_with_metadata(
    #     image_path=f'{input_dir}/서랍장4.jpg',
    #     metadata_path=f'{meta_dir}/서랍장4.json',
    # )
    #
    # ## 3. Apply Style
    # generator.apply_style_from_reference(
    #     product_image_path=f'{input_dir}/소파1.png',
    #     reference_image_path=[f'{refer_dir}/001.png']
    # )
    #
    # ## 4. Replace Object
    # generator.replace_object_in_reference(
    #     product_image_path=f'{input_dir}/의자2.jpg',
    #     reference_image_path=[f'{refer_dir}/002.png']
    # )

    ##5. Create Interior Scene
    generator.create_interior_scene(
        product_image_paths=[
            f'{input_dir}/소파1.png',
            f'{input_dir}/테이블1.jpg',
            f'{input_dir}/의자1.jpg'
            f'{input_dir}/책장3.jpg'
        ]
    )
