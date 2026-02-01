import os
from datetime import datetime

from common import prompt
from common.gemini import Gemini

class ImageGenerator:
    def __init__(self, output_dir=None):
        if output_dir:
            self.output_dir = output_dir
            os.makedirs(self.output_dir, exist_ok=True)
        else:
            # If no output directory is provided, create a default one.
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.output_dir = "./output/{}".format(timestamp)
            os.makedirs(self.output_dir, exist_ok=True)
        self.gemini = Gemini()

    def create_prompt(self, generation_mode, keywords, **kwargs):
        if generation_mode == "style_transfer":
            return prompt.APPLY_STYLE_FROM_REFERENCE
        elif generation_mode == "object_replace":
            # In this case, the object to replace might be passed in kwargs
            object_to_replace = kwargs.get("object_to_replace", "the main object")
            return prompt.REPLACE_OBJECT_IN_REFERENCE.format(object_to_replace=object_to_replace)
        elif generation_mode == "scene_create":
            return prompt.CREATE_BEAUTY_SCENE
        else: # basic or custom
            product_desc = keywords.get('product', 'a product')
            props_desc = keywords.get('props', 'minimalist setup')
            background_desc = keywords.get('background', 'clean, neutral background')
            mood_desc = keywords.get('mood', 'soft, natural lighting')

            return f"""An editorial-style photograph of {product_desc}. \
                    Props/Objects: {props_desc}. \
                    Background/Surface: {background_desc}. \
                    Mood/Lighting: {mood_desc}. \
                    The image should be vivid, high-end, and professionally captured."""

    def change_attributes(self, image_paths, instructions):
        """Changes the color or orientation of a furniture image."""
        p = prompt.CHANGE_ATTRIBUTES.format(instructions=", ".join(instructions))
        generated_image_data, _ = self.gemini.call_image_generator(prompt=p, image_files=image_paths)

        output_path = self._get_output_path(image_paths[0], "_changed")
        saved_files = self._save_image_from_data(generated_image_data, output_path)
        # self.show_image_popup(product_image_path=image_paths, save_image_path=saved_files)
        return saved_files

    def create_thumbnail_with_metadata(self, image_paths, reference_image_paths=None):
        """Generates a thumbnail with text overlay or a scene based on the description."""
        if reference_image_paths:
            p = prompt.APPLY_STYLE_FROM_REFERENCE
            all_image_files = image_paths + reference_image_paths
        else:
            p = prompt.CREATE_THUMBNAIL_WITH_METADATA
            all_image_files = image_paths

        generated_image_data, _ = self.gemini.call_image_generator(prompt=p, image_files=all_image_files)

        output_path = self._get_output_path(image_paths[0], "_thumbnail_style")
        saved_files = self._save_image_from_data(generated_image_data, output_path)
        # self.show_image_popup(product_image_path=image_paths, reference_image_path=reference_image_path, save_image_path=saved_files)
        return saved_files

    def apply_style_from_reference(self, product_image_paths, reference_image_paths):
        """Uses a reference image for style transfer."""
        p = prompt.APPLY_STYLE_FROM_REFERENCE

        all_image_files = product_image_paths + reference_image_paths
        generated_image_data, _ = self.gemini.call_image_generator(prompt=p, image_files=all_image_files)

        output_path = self._get_output_path(product_image_paths[0], "_styled")
        saved_files = self._save_image_from_data(generated_image_data, output_path)
        # self.show_image_popup(product_image_path=product_image_paths, reference_image_path=reference_image_path, save_image_path=saved_files)
        return saved_files

    def replace_object_in_reference(self, product_image_paths, reference_image_paths):
        """Inpaints the product into a reference scene."""
        object_description = ", ".join([os.path.splitext(os.path.basename(p))[0] for p in product_image_paths])
        p = prompt.REPLACE_OBJECT_IN_REFERENCE.format(object_to_replace=object_description)

        all_image_files = product_image_paths + reference_image_paths
        generated_image_data, _ = self.gemini.call_image_generator(prompt=p, image_files=all_image_files)

        output_path = self._get_output_path(product_image_paths[0], "_replaced")
        saved_files = self._save_image_from_data(generated_image_data, output_path)
        # self.show_image_popup(product_image_path=product_image_paths, reference_image_path=reference_image_path, save_image_path=saved_files)
        return saved_files

    def create_beauty_scene(self, product_image_paths, reference_image_paths=None):
        """Combines multiple products into one scene."""

        p = prompt.CREATE_BEAUTY_SCENE
        if reference_image_paths is not None:
            all_image_files = product_image_paths + reference_image_paths
        else:
            all_image_files = product_image_paths
        generated_image_data, _ = self.gemini.call_image_generator(prompt=p, image_files=all_image_files)

        output_path = os.path.join(self.output_dir, "beauty_scene.png")
        saved_files = self._save_image_from_data(generated_image_data, output_path)
        # self.show_image_popup(product_image_path=product_image_paths, save_image_path=saved_files)
        return saved_files

    def _get_output_path(self, original_path, suffix):
        base, ext = os.path.splitext(os.path.basename(original_path))
        return os.path.join(self.output_dir, f"{base}{suffix}{ext}")

    def _save_image_from_data(self, image_data, output_path):
        saved_files = []
        if isinstance(image_data, list):
            base, ext = os.path.splitext(output_path)
            for i, data in enumerate(image_data):
                # Create a new filename for each image to avoid overwriting
                new_path = f"{base}_{i}{ext}" if len(image_data) > 1 else output_path
                with open(new_path, 'wb') as f:
                    f.write(data.data)
                print(f"Image saved to {new_path}")
                saved_files.append(new_path)
        return saved_files


if __name__ == '__main__':

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = "./output/{}".format(timestamp)

    meta_dir = './output/meta'
    input_dir = 'resource/제품'
    refer_dir = './resource/레퍼런스'
    generator = ImageGenerator(output_dir=output_dir)

    # # # 1. Change Attributes
    # generator.change_attributes(
    #     image_paths=[f'{input_dir}/샴푸.png'],
    #     instructions=['제품 우측 컷으로 교체 해주세요.']
    # )
    #
    # # ## 2. Create Thumbnail with Metadata
    # generator.create_thumbnail_with_metadata(
    #     image_paths=[f'{input_dir}/샴푸.png'],
    # )
    # #
    # # ## 3. Apply Style
    # generator.apply_style_from_reference(
    #     product_image_paths=[f'{input_dir}/샴푸.png'],
    #     reference_image_paths=[f'{refer_dir}/샴푸002.jpg'],
    # )
    #
    # ## 4. Replace Object
    # generator.replace_object_in_reference(
    #     product_image_paths=[f'{input_dir}/헤어오일.png'],
    #     reference_image_paths=[f'{refer_dir}/스틸컷001.jpg'],
    # )

    ##5. Create Beauty Scene
    generator.create_beauty_scene(
        product_image_paths=[
            f'{input_dir}/샴푸.png',
            f'{input_dir}/트린트먼트.png',
            f'{input_dir}/헤어스프레이.jpg',
            f'{input_dir}/헤어오일.png'
        ],
        reference_image_paths=[
            f'{refer_dir}/제품라인업005.jpg'
        ]
    )
