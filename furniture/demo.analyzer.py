import os
import glob
import json

from common import config, prompt, gemini

import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk


class VisionAnalyzer:
    def __init__(self, input_dir, output_dir):
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.gemini = gemini.Gemini()
        self.base_columns = [
            'filename',
            'category',
            'sub_category',
            'attributes',
            'description'
        ]
        self.all_columns = set(self.base_columns)

    def analyze(self):
        image_paths = self._get_image_paths()
        if not image_paths:
            print(f"No images found in {self.input_dir}")
            return

        results = []
        for image_path in image_paths:
            print(f"Analyzing: {image_path}...")
            try:

                # 1. Analyze Category - 메인 카테고리 분석
                category_prompt = prompt.PRODUCT_CATEGORY.format(
                    product_categories=json.dumps(config.PRODUCT_CATEGORY, ensure_ascii=False, indent=4),
                    category_keys=list(config.PRODUCT_CATEGORY.keys()),
                    category_values=list(config.PRODUCT_CATEGORY.values())
                )
                category_response = self.gemini.call_gemini_image_text(prompt=category_prompt, image=image_path)
                category_data = json.loads(category_response)

                main_category = category_data.get('category', '')
                sub_category = category_data.get('sub_category', '')

                # 2. Analyze Category-specific Attributes - 카테고리별 가변 속성
                product_attributes = {}
                if main_category in config.PRODUCT_ATTRIBUTE:
                    product_attr_config = config.PRODUCT_ATTRIBUTE[main_category]

                    # 카테고리별 속성 분석 프롬프트 생성
                    product_attr_prompt = prompt.PRODUCT_ATTRIBUTE.format(
                        category=main_category,
                        attributes_config=json.dumps(product_attr_config, ensure_ascii=False, indent=4)
                    )
                    product_attr_response = self.gemini.call_gemini_image_text(prompt=product_attr_prompt, image=image_path)
                    product_attributes = json.loads(product_attr_response)

                print(f"Category attributes: {list(product_attributes.keys())}")

                # 3. Analyze Common Attributes - 공통 속성 (스타일, 색상, 무늬 등)
                common_attr_prompt = prompt.COMMON_ATTRIBUTE.format(
                    styles=json.dumps(config.COMMON_ATTRIBUTE['스타일'], ensure_ascii=False),
                    colors=json.dumps(list(config.COMMON_ATTRIBUTE['색상']), ensure_ascii=False),
                    patterns=json.dumps(config.COMMON_ATTRIBUTE['무늬'], ensure_ascii=False),
                    target_customers=json.dumps(config.COMMON_ATTRIBUTE['타겟 고객'], ensure_ascii=False),
                    target_ages=json.dumps(config.COMMON_ATTRIBUTE['타겟 연령층'], ensure_ascii=False)
                )
                common_attr_response = self.gemini.call_gemini_image_text(prompt=common_attr_prompt, image=image_path)
                common_attributes = json.loads(common_attr_response)

                print(f"Common attributes: {list(common_attributes.keys())}")

                # 4. 모든 속성 통합
                all_attributes = {}
                all_attributes.update(product_attributes)
                all_attributes.update(common_attributes)

                # 5. Generate Description
                description_prompt = prompt.PRODUCT_DESCRIPTION.format(
                    category=main_category,
                    sub_category=sub_category,
                    attributes=json.dumps(all_attributes, ensure_ascii=False, indent=4)
                )
                description_response = self.gemini.call_gemini_text(prompt=description_prompt)
                description_data = json.loads(description_response)

                # 결과 정리
                result = {
                    'image_path': image_path,
                    'filename': os.path.basename(image_path),
                    'category': main_category,
                    'sub_category': sub_category,
                    'attributes': json.dumps(all_attributes, ensure_ascii=False),
                    'description': json.dumps(description_data, ensure_ascii=False)
                }

                # Add individual attribute fields
                if isinstance(all_attributes, dict):
                    for key, value in all_attributes.items():
                        field_name = f'attr_{key}'
                        result[field_name] = value
                        self.all_columns.add(field_name)

                # Add individual description fields
                if isinstance(description_data, dict):
                    for key, value in description_data.items():
                        field_name = f'desc_{key}'
                        result[field_name] = value
                        self.all_columns.add(field_name)

                results.append(result)

                # Show popup for each result and save
                self.show_single_result_popup(result)
                self._save_result_json(result)

            except Exception as e:
                print(f"Error analyzing {image_path}: {e}")

    def show_single_result_popup(self, result):
        root = tk.Tk()
        root.title(f"Analysis Result - {result['filename']}")
        root.geometry("1000x900")
        root.resizable(True, True)

        main_frame = ttk.Frame(root, padding="15")
        main_frame.pack(fill='both', expand=True)

        # Image frame - centered at top
        image_frame = ttk.Frame(main_frame)
        image_frame.pack(fill='x', pady=(0, 20))

        img = Image.open(result['image_path'])
        img.thumbnail((300, 300))
        photo = ImageTk.PhotoImage(img)
        img_label = ttk.Label(image_frame, image=photo)
        img_label.image = photo
        img_label.pack()

        # Table frame
        table_frame = ttk.LabelFrame(main_frame, text="Analysis Results", padding="10")
        table_frame.pack(fill='both', expand=True)

        # Create treeview with proper columns
        columns = ('Value', 'Reason')
        tree = ttk.Treeview(table_frame, columns=columns, show='tree headings', height=12)

        # Configure columns
        tree.heading('#0', text='Field', anchor='w')
        tree.heading('Value', text='Value', anchor='w')
        tree.heading('Reason', text='Reason', anchor='w')

        tree.column('#0', width=120, minwidth=80, anchor='w')
        tree.column('Value', width=150, minwidth=100, anchor='w')
        tree.column('Reason', width=600, minwidth=400, anchor='w')

        # Parse JSON data
        try:
            attributes = json.loads(result.get('attributes', '{}'))
            description = json.loads(result.get('description', '{}'))
        except:
            attributes = {}
            description = {}

        # Get category-specific attributes from config
        category = result.get('category', '')
        category_attributes = config.PRODUCT_ATTRIBUTE.get(category, {})

        # Prepare basic data rows
        rows_data = [
            ('filename', result.get('filename', ''), '-'),
            ('category', result.get('category', ''), '-'),
            ('sub_category', result.get('sub_category', ''), '-'),
        ]

        # 카테고리별 속성 추가 (순서 보장)
        for attr_key in category_attributes.keys():
            value, reason = self._extract_attribute_value_reason(attributes, attr_key)
            if value and value.strip():
                rows_data.append((attr_key, value, reason))

        # 공통 속성 추가
        common_attrs = ['스타일', '색상', '무늬', '타겟 고객', '타겟 연령층']
        for attr_key in common_attrs:
            if attr_key not in category_attributes:  # 중복 방지
                value, reason = self._extract_attribute_value_reason(attributes, attr_key)
                if value and value.strip():
                    rows_data.append((attr_key, value, reason))

        # 기타 추가 속성들 (분석에서 나온 다른 속성들)
        processed_keys = set([row[0] for row in rows_data])
        for attr_key, attr_data in attributes.items():
            if attr_key not in processed_keys:
                value, reason = self._parse_attribute_data(attr_data, attr_key)
                if value and value.strip():
                    rows_data.append((attr_key, value, reason))

        # Insert data into treeview
        for i, (field, value, reason) in enumerate(rows_data):
            if value and value.strip():
                item_id = tree.insert("", "end", text=field, values=(str(value), str(reason)))
                # Alternate row colors
                if i % 2 == 1:
                    tree.item(item_id, tags=('oddrow',))

        # Configure alternating row colors
        tree.tag_configure('oddrow', background='#f5f5f5')

        # Scrollbars
        v_scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
        h_scrollbar = ttk.Scrollbar(table_frame, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)

        # Grid layout for table and scrollbars
        tree.grid(row=0, column=0, sticky='nsew')
        v_scrollbar.grid(row=0, column=1, sticky='ns')
        h_scrollbar.grid(row=1, column=0, sticky='ew')

        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)
        table_frame.grid_rowconfigure(1, weight=0)

        # Add description section below the table
        desc_frame = ttk.LabelFrame(main_frame, text="Description", padding="10")
        desc_frame.pack(fill='x', pady=(10, 0))

        desc_text = tk.Text(desc_frame, wrap='word', height=6, font=('TkDefaultFont', 10), padx=10, pady=10)
        desc_scrollbar = ttk.Scrollbar(desc_frame, orient="vertical", command=desc_text.yview)
        desc_text.configure(yscrollcommand=desc_scrollbar.set)

        description_content = description.get('description', '')
        if description_content:
            desc_text.insert('1.0', description_content)
        else:
            desc_text.insert('1.0', "설명 정보 없음")

        desc_text.config(state='disabled')

        desc_text.pack(side='left', fill='both', expand=True)
        desc_scrollbar.pack(side='right', fill='y')

        root.mainloop()

    def _extract_attribute_value_reason(self, attributes, attr_key):
        """주어진 속성 키에 대한 값과 이유를 추출"""
        value = ''
        reason = ''

        # 1. 직접 매치 시도
        if attr_key in attributes:
            attr_data = attributes[attr_key]
            value, reason = self._parse_attribute_data(attr_data, attr_key)
            if value:
                return value, reason

        # 2. 키 매핑을 통한 매치 시도
        key_mappings = {
            '색상': ['color', '컬러', 'colour'],
            '주요 소재': ['material', '소재', 'materials', '재료', '상판 소재', '프레임 소재'],
            '유형': ['type', '타입'],
            '형태': ['shape', 'form'],
            '침구 사이즈': ['size', '사이즈', '크기', '침구사이즈'],
            '단 수': ['단수', '단', 'tier', 'level'],
            '우드톤': ['wood_tone', 'woodtone', '우드', 'wood'],
            '도어 형태': ['door_type', 'door', '도어', '문'],
            '다리': ['leg', 'legs', '다리', '받침'],
            '바퀴': ['wheel', 'wheels', '바퀴', '캐스터'],
            '서랍': ['drawer', 'drawers', '서랍'],
            '헤드 유무': ['head', '헤드', 'headboard', '헤드보드'],
            '프레임 형태': ['frame', '프레임', 'frame_type'],
            '스타일': ['style'],
            '무늬': ['pattern', '패턴'],
            '타겟 고객': ['target', '타겟'],
            '타겟 연령층': ['age', '연령', 'age_group']
        }

        possible_keys = key_mappings.get(attr_key, [])
        for mapped_key in possible_keys:
            if mapped_key in attributes:
                attr_data = attributes[mapped_key]
                value, reason = self._parse_attribute_data(attr_data, attr_key)
                if value:
                    return value, reason

        # 3. 대소문자 및 공백 무시한 매치 시도
        attr_key_clean = attr_key.lower().replace(' ', '').replace('·', '')
        for key in attributes.keys():
            key_clean = key.lower().replace(' ', '').replace('·', '')
            if key_clean == attr_key_clean:
                attr_data = attributes[key]
                value, reason = self._parse_attribute_data(attr_data, attr_key)
                if value:
                    return value, reason

        return '', f'{attr_key} 정보 없음'

    def _parse_attribute_data(self, attr_data, attr_key):
        """속성 데이터에서 값과 이유를 파싱"""
        value = ''
        reason = ''

        if isinstance(attr_data, dict):

            value = attr_data.get('value', '')
            reason = attr_data.get('reason', '')
            # 값이 없으면 전체 딕셔너리에서 의미있는 값 찾기
            if not value:
                meaningful_values = [v for v in attr_data.values() if v and str(v).strip() and str(v) != 'null']
                if meaningful_values:
                    value = str(meaningful_values[0])
        else:
            value = str(attr_data) if attr_data else ''

        # 기본 이유 설정
        if value and not reason:
            reason = f'{attr_key} 분석 결과'

        # 의미없는 값 필터링
        if value and (value.startswith('{') or value == 'null' or value.lower() == 'none'):
            value = ''

        return value.strip(), reason.strip()

    def _save_result_json(self, result):
        filename = result['filename']
        name, ext = os.path.splitext(filename)

        # Create output directory
        os.makedirs(self.output_dir, exist_ok=True)
        output_path = os.path.join(self.output_dir, f'{name}.json')
        json_data = {key: value for key, value in result.items() if key != 'image_path'}

        # Save as JSON file
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, ensure_ascii=False, indent=4)

        print(f"JSON result saved to: {output_path}")

    def _get_image_paths(self, extensions=['.jpg', '.jpeg', '.png']):
        image_paths = []
        for ext in extensions:
            image_paths.extend(glob.glob(os.path.join(self.input_dir, f"**/*{ext}"), recursive=True))
        return image_paths


if __name__ == '__main__':
    input_directory = './resource/가구'
    output_directory = './output/meta'
    analyzer = VisionAnalyzer(input_dir=input_directory, output_dir=output_directory)
    analyzer.analyze()