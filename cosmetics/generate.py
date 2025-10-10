import os
from datetime import datetime

import json
import tkinter as tk
from PIL import Image, ImageTk

from common import prompt
from common.gemini import Gemini

PRODUCT_DESCRIPTION = """
    제공된 상세페이지 속성 정보를 바탕으로 고객의 시선을 사로잡는 매력적인 상품 설명을 생성해주세요.
    ### 생성 가이드
    1. 제품의 핵심 매력을 간결하고 임팩트 있는 문장 묘사
    2. 속성 정보를 활용하여 제품의 특징과 장점을 구체적으로 묘사
    3. 제품이 제공하는 가치나 고객 경험을 강조
    
    ### 상세페이지 속성 정보
    {attributes}
    
    응답 형식(반드시 Json으로 반환 한다.):
    {{
        description: ""
    }}
    """


CHANGE_ATTRIBUTES = """
    주어진 이미지의 특정 속성을 변경하여 새로운 이미지를 생성해주세요.
    변경 요청 사항: {instructions}
    원본 이미지를 바탕으로 요청된 사항만 자연스럽게 수정해주세요.
    """

CREATE_THUMBNAIL_WITH_METADATA = """
    상세페이지 이미지와 메타데이터, 설명을 바탕으로 시선을 끄는 썸네일 이미지를 생성해주세요.
    메타데이터: {metadata}
    제품의 특징이 잘 드러나도록 매력적인 배경이나 구성을 추가해주세요.
    """

APPLY_STYLE_FROM_REFERENCE = """
    첫 번째 이미지를 두 번째 이미지의 스타일로 재구성해주세요.
    첫 번째 이미지는 상세페이지 이미지이며, 두 번째 이미지는 스타일 레퍼런스입니다.
    제품의 고유 속성(색상,형태) 는 유지하되, 색상, 질감, 분위기, 배경 및 소품에 대해서 레퍼런스 스타일에 맞춰 변경해주세요.
    """

REPLACE_OBJECT_IN_REFERENCE = """
    두 번째 레퍼런스 이미지에서 {object_to_replace} 객체를 첫 번째 상세페이지 이미지로 교체해주세요.
    제품이 주변 환경과 자연스럽게 어우러지도록 빛, 그림자, 비율을 조정해주세요.
    """

CREATE_INTERIOR_SCENE = """
    제공된 여러 상세페이지 이미지들을 활용하여 조화로운 인테리어 장면을 연출해주세요.
    반드시, **제품의 고유 속성(색상,형태)**는 유지 되어야 해.
    모든 제품이 하나의 공간에 자연스럽게 배치된 것처럼 보이게 해주세요.
    """

class ImageGenerator:
    def __init__(self, output_dir=None):
        if output_dir:
            self.output_dir = output_dir
            os.makedirs(self.output_dir, exist_ok=True)
        self.gemini = Gemini()

    def create_prompt(self, generation_mode, keywords, **kwargs):
        if generation_mode == "style_transfer":
            return APPLY_STYLE_FROM_REFERENCE
        elif generation_mode == "object_replace":
            # In this case, the object to replace might be passed in kwargs
            object_to_replace = kwargs.get("object_to_replace", "the main object")
            return REPLACE_OBJECT_IN_REFERENCE.format(object_to_replace=object_to_replace)
        elif generation_mode == "scene_create":
            return CREATE_INTERIOR_SCENE
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

    def change_attributes(self, image_path, instructions):
        """Changes the color or orientation of a furniture image."""
        p = prompt.CHANGE_ATTRIBUTES.format(instructions=", ".join(instructions))
        generated_image_data, _ = self.gemini.call_image_generator(prompt=p, image_files=[image_path])

        output_path = self._get_output_path(image_path, "_changed")
        saved_files = self._save_image_from_data(generated_image_data, output_path)
        self.show_image_popup(product_image_path=image_path, save_image_path=saved_files)
        return saved_files

    def create_thumbnail_with_metadata(self, image_path, metadata_path):
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
        self.show_image_popup(product_image_path=image_path, save_image_path=saved_files)
        return saved_files

    def apply_style_from_reference(self, product_image_path, reference_image_path):
        """Uses a reference image for style transfer."""
        p = prompt.APPLY_STYLE_FROM_REFERENCE

        all_image_files = [product_image_path] + reference_image_path
        generated_image_data, _ = self.gemini.call_image_generator(prompt=p, image_files=all_image_files)

        output_path = self._get_output_path(product_image_path, "_styled")
        saved_files = self._save_image_from_data(generated_image_data, output_path)
        self.show_image_popup(product_image_path=product_image_path, reference_image_path=reference_image_path, save_image_path=saved_files)
        return saved_files

    def replace_object_in_reference(self, product_image_path, reference_image_path):
        """Inpaints the product into a reference scene."""
        p = prompt.REPLACE_OBJECT_IN_REFERENCE.format(object_to_replace=product_image_path)

        all_image_files = [product_image_path] + reference_image_path
        generated_image_data, _ = self.gemini.call_image_generator(prompt=p, image_files=all_image_files)

        output_path = self._get_output_path(product_image_path, "_replaced")
        saved_files = self._save_image_from_data(generated_image_data, output_path)
        self.show_image_popup(product_image_path=product_image_path, reference_image_path=reference_image_path, save_image_path=saved_files)
        return saved_files

    def create_interior_scene(self, product_image_paths):
        """Combines multiple products into one scene."""

        p = prompt.CREATE_INTERIOR_SCENE
        generated_image_data, _ = self.gemini.call_image_generator(prompt=p, image_files=product_image_paths)

        output_path = os.path.join(self.output_dir, "interior_scene.png")
        saved_files = self._save_image_from_data(generated_image_data, output_path)
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

    def show_image_popup(self, product_image_path=None, reference_image_path=None, save_image_path=None):
        image_paths = []
        if product_image_path:
            if isinstance(product_image_path, list):
                image_paths.extend(product_image_path)
            else:
                image_paths.append(product_image_path)

        if reference_image_path:
            if isinstance(reference_image_path, list):
                image_paths.extend(reference_image_path)
            else:
                image_paths.append(reference_image_path)

        if save_image_path:
            if isinstance(save_image_path, list):
                image_paths.extend(save_image_path)
            else:
                image_paths.append(save_image_path)

        root = tk.Tk()
        root.title("Generated Images")

        if not image_paths:
            print("No images to display.")
            root.destroy()
            return

        for image_path in image_paths:
            if not os.path.exists(image_path):
                print(f"Image not found at {image_path}, skipping.")
                continue
            img = Image.open(image_path)
            img.thumbnail((800, 600))
            photo = ImageTk.PhotoImage(img)
            label = tk.Label(root, image=photo)
            label.image = photo
            label.pack(side=tk.LEFT)

        if root.children:
            root.mainloop()
        else:
            root.destroy()

if __name__ == '__main__':

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = "./output/{}".format(timestamp)

    meta_dir = './output/meta'
    input_dir = 'resource/제품'
    refer_dir = './resource/레퍼런스'
    generator = ImageGenerator(output_dir=output_dir)

    # 1. Change Attributes
    generator.change_attributes(
        image_path=f'{input_dir}/샴푸.png',
        instructions=['검정색 샴푸를 흰색 으로 변경하고, 화면의 우측 컷으로 교체 해주세요.']
    )

    ## 2. Create Thumbnail with Metadata
    generator.create_thumbnail_with_metadata(
        image_path=f'{input_dir}/샴푸.png',
        metadata_path=f'{meta_dir}/샴푸2.json',
    )

    ## 3. Apply Style
    generator.apply_style_from_reference(
        product_image_path=f'{input_dir}/샴푸.png',
        reference_image_path=[f'{refer_dir}/샴푸스틸001.jpg']
    )

    ## 4. Replace Object
    generator.replace_object_in_reference(
        product_image_path=f'{input_dir}/헤어세럼.jpg',
        reference_image_path=[f'{refer_dir}/스틸컷001.jpg']
    )

    ##5. Create Interior Scene
    generator.create_interior_scene(
        product_image_paths=[
            f'{input_dir}/샴푸.png',
            f'{input_dir}/트린트먼트.jpg',
            f'{input_dir}/헤어스프레이.jpg',
            f'{input_dir}/헤어오일.jpg'
        ]
    )
