# -*- coding: utf-8 -*-
"""
AI Prompt Templates for CEN AI DAM Editor

This module contains all prompt templates used for Gemini AI interactions.
Organized by feature category as defined in the specification document.
"""


class PromptTemplates:
    """Collection of AI prompt templates for various image generation and analysis tasks."""

    # ================================================================
    # PRODUCT ANALYSIS PROMPTS
    # ================================================================

    @staticmethod
    def product_category_analysis(product_categories: dict) -> str:
        """Generate prompt for product category classification."""
        return f"""
제시된 이미지를 분석하여 정확한 카테고리를 결정해주세요.

### 분석 가이드
1. **주요 제품 식별**: 이미지에서 가장 중심이 되는 제품을 파악
2. **형태적 특성 분석**: 제품의 모양, 구조, 디자인적 특징 관찰
3. **기능적 용도 파악**: 제품의 실제 사용 목적 고려

## 카테고리 옵션
{product_categories}

응답 형식 (JSON):
{{
    "category": "선택된 카테고리명",
    "sub_category": "세부 카테고리명",
    "confidence": 0.0~1.0,
    "reason": "선택 근거를 구체적으로 설명",
    "key_features": [
        "특징1: 구체적 관찰 내용",
        "특징2: 구체적 관찰 내용"
    ]
}}
"""

    @staticmethod
    def product_attribute_analysis(category: str, attributes_config: dict) -> str:
        """Generate prompt for product-specific attribute analysis."""
        return f"""
이미지를 보고 해당 {category} 제품의 속성을 분석해주세요.

### 분석할 {category} 전용 속성들:
{attributes_config}

### 분석 가이드
- 각 속성에 대해 위의 옵션들 중에서 가장 적합한 값을 선택해주세요.
- 시각적 증거를 바탕으로 정확한 판단을 해주세요.
- 불확실한 경우 confidence를 낮게 설정해주세요.

응답 형식 (JSON):
{{
    "속성명1": {{
        "value": "선택된 값",
        "confidence": 0.0~1.0,
        "reason": "선택 이유"
    }},
    "속성명2": {{
        "value": "선택된 값",
        "confidence": 0.0~1.0,
        "reason": "선택 이유"
    }}
}}
"""

    @staticmethod
    def common_attribute_analysis(colors: list, patterns: list, styles: list,
                                   target_customers: list, target_ages: list) -> str:
        """Generate prompt for common product attributes (style, color, pattern, target)."""
        return f"""
제시된 제품 이미지에서 상품의 핵심 속성을 정확히 분석해주세요.

### 색상(Color) 옵션: {colors}
- 제품 전체 면적의 50% 이상을 차지하는 주색상 우선 식별
- 패턴이 있는 경우 바탕색 기준 판단

### 무늬(Pattern) 옵션: {patterns}
- 무지: 패턴 없이 단색
- 우드그레인: 나뭇결 무늬
- 마블: 대리석 질감
- 패브릭 텍스처: 직조 무늬
- 그래픽: 프린트/문양

### 스타일(Style) 옵션: {styles}
- 모던, 클래식, 빈티지, 미니멀, 내추럴, 럭셔리, 인더스트리얼, 북유럽, 러블리

### 타겟 고객 옵션: {target_customers}
### 타겟 연령층 옵션: {target_ages}

응답 형식 (JSON):
{{
    "스타일": {{
        "value": "선택된_스타일",
        "confidence": 0.0~1.0,
        "reason": "선택 근거"
    }},
    "타겟 고객": {{
        "value": "선택된 타겟 고객",
        "confidence": 0.0~1.0,
        "reason": "선택 근거"
    }},
    "타겟 연령층": {{
        "value": "선택된 연령층",
        "confidence": 0.0~1.0,
        "reason": "선택 근거"
    }},
    "색상": {{
        "value": "선택된_색상",
        "confidence": 0.0~1.0,
        "reason": "선택 근거"
    }},
    "무늬": {{
        "value": "선택된_패턴",
        "confidence": 0.0~1.0,
        "reason": "선택 근거"
    }}
}}
"""

    @staticmethod
    def product_description(attributes: dict) -> str:
        """Generate prompt for creating product description from attributes."""
        return f"""
제공된 제품 속성 정보를 바탕으로 고객의 시선을 사로잡는 매력적인 상품 설명을 생성해주세요.

### 제품 속성 정보
{attributes}

### 생성 가이드
1. 제품의 핵심 매력을 간결하고 임팩트 있게 묘사
2. 속성 정보를 활용하여 특징과 장점을 구체적으로 묘사
3. 제품이 제공하는 가치나 고객 경험을 강조

응답 형식 (JSON):
{{
    "description": "매력적인 상품 설명 (2-3문장)"
}}
"""

    # ================================================================
    # TEMPLATE 01: SNS/마케팅 광고 소재 생성
    # ================================================================

    @staticmethod
    def sns_marketing_template(
        product_name: str,
        target_audience: str,
        layout: str,
        concept: str,
        copy: dict = None
    ) -> str:
        """Generate SNS/Marketing material based on template inputs."""
        copy_text = f"""
메인카피: {copy.get('main', '')}
서브카피: {copy.get('sub', '')}
해시태그: {copy.get('hashtags', '')}
""" if copy else "AI가 적절한 카피를 생성해주세요."

        return f"""
SNS/마케팅 광고 소재를 생성해주세요.

### 제품 정보
- 제품명: {product_name}
- 타겟 고객: {target_audience}

### 레이아웃 구성
{layout}

### 컨셉/광고 목적
{concept}

### 문구(카피)
{copy_text}

### 생성 요구사항
1. 레이아웃 구성을 정확히 따를 것
2. 타겟 고객의 감성을 자극하는 비주얼
3. 제품의 핵심 가치를 시각적으로 전달
4. 브랜드 아이덴티티에 부합하는 색감과 톤앤매너

고품질의 SNS 광고 이미지를 생성해주세요.
"""

    # ================================================================
    # TEMPLATE 02: 상세페이지/카탈로그 생성
    # ================================================================

    @staticmethod
    def detail_page_template(
        product_name: str,
        product_images: list,
        layout_ratio: str,
        reference_frame: str = None
    ) -> str:
        """Generate product detail page / catalog based on brand layout."""
        frame_text = f"레퍼런스 프레임: {reference_frame}" if reference_frame else ""

        return f"""
제품 상세페이지/카탈로그 이미지를 생성해주세요.

### 제품 정보
- 제품명: {product_name}
- 조합 제품 이미지: {len(product_images)}개 제공됨

### 레이아웃
- 비율: {layout_ratio}
- {frame_text}

### 생성 요구사항
1. 브랜드 레이아웃에 맞춰 제품 조합
2. 모델·배경·상품을 자연스럽게 합성
3. 실제 스튜디오 촬영과 같은 고품질
4. 제품의 디테일이 잘 드러나도록 구성

스튜디오 촬영 없이도 실무에 바로 활용 가능한 고품질 콘텐츠를 생성해주세요.
"""

    # ================================================================
    # TEMPLATE 03: 스튜디오 촬영 이미지 생성
    # ================================================================

    @staticmethod
    def studio_shooting_template(
        product_image: str,
        model_setting: str = None,
        combination_products: list = None,
        shooting_concept: str = "미니멀리즘 하이엔드 패션 룩북"
    ) -> str:
        """Generate studio shooting images (model fitting, cross-sell)."""
        model_text = f"모델 설정: {model_setting}" if model_setting else "AI가 적절한 모델을 선택합니다."
        combo_text = f"조합 제품: {', '.join(combination_products)}" if combination_products else "단일 제품 촬영"

        return f"""
스튜디오 촬영 이미지를 생성해주세요.

### 제품 정보
- 메인 제품 이미지: {product_image}
- {combo_text}

### 촬영 설정
- {model_text}
- 촬영 컨셉: {shooting_concept}

### 생성 단계
1. AI 모델 가상 피팅 (제품을 모델에 자연스럽게 착용)
2. 특정 모델 변경 (필요시 다른 포즈/모델로 교체)
3. 촬영 배경 추가 (컨셉에 맞는 배경 연출)
4. 톤&무드 조정 (최종 색감 보정)

### 생성 요구사항
- 한 번의 업로드만으로 다양한 포즈의 모델컷 생성
- 스튜디오 촬영 비용과 시간을 획기적으로 절감
- 실제 촬영과 구분이 어려운 고퀄리티 결과물

고품질의 스튜디오 촬영 이미지를 생성해주세요.
"""

    # ================================================================
    # TEMPLATE 04: 다국어 변환 이미지 생성
    # ================================================================

    @staticmethod
    def multilingual_conversion_template(
        original_image: str,
        target_language: str,
        font_settings: dict = None,
        requirements: str = None
    ) -> str:
        """Convert image text to different languages while maintaining design."""
        font_text = f"""
폰트 설정:
- 폰트 패밀리: {font_settings.get('family', '자동 선택')}
- 강조 키워드: {font_settings.get('emphasis', '없음')}
- 번역 톤: {font_settings.get('tone', '일반')}
""" if font_settings else "폰트는 자동으로 선택됩니다."

        return f"""
다국어 변환 이미지를 생성해주세요.

### 원본 이미지
- 파일: {original_image}

### 변환 대상 언어
- 언어: {target_language}

### {font_text}

### 필수사항
{requirements or "원본 디자인의 톤앤매너와 레이아웃을 그대로 유지"}

### 생성 요구사항
1. 글로벌 캠페인을 위한 언어별 이미지 자동 변환
2. 각 언어의 텍스트 길이와 특성을 분석하여 폰트 크기와 줄바꿈 자동 조정
3. 원본 디자인의 레이아웃과 시각적 밸런스 일관되게 유지
4. 웹툰/만화의 경우 말풍선 크기를 자동 최적화

디자인 톤앤매너를 유지하면서 타겟 국가의 언어로 자연스럽게 현지화된 이미지를 생성해주세요.
"""

    # ================================================================
    # TEMPLATE 05: 인포그래픽 이미지 생성
    # ================================================================

    @staticmethod
    def infographic_template(
        data_source: str,
        content_type: str,
        purpose: str,
        target_audience: str,
        visual_style: str,
        key_message: str
    ) -> str:
        """Generate infographic images from data/documents."""
        return f"""
인포그래픽 이미지를 생성해주세요.

### 데이터 소스
- 입력 파일: {data_source}

### 콘텐츠 정보
- 콘텐츠 유형: {content_type} (시리즈형/단일형)
- 목적: {purpose}
- 타겟 오디언스: {target_audience}

### 시각화 스타일
- 스타일: {visual_style} (예: 프레젠테이션 슬라이드, 그리드형, 타임라인)

### 핵심 메시지
{key_message}

### 생성 요구사항
1. 업로드된 문서(PDF)를 자동 분석하여 타겟 고객이 한눈에 이해할 수 있는 인포그래픽 생성
2. 자료의 구성과 스토리 흐름을 고려한 시각화
3. 기능·특징·활용 포인트를 시각 중심으로 정리
4. 짧은 시간 안에 이해와 설명이 가능하도록 구성

데이터를 시각화한 인포그래픽 이미지를 생성해주세요.
"""

    # ================================================================
    # BASIC IMAGE GENERATION PROMPTS (from legacy code)
    # ================================================================

    @staticmethod
    def change_attributes(instructions: str) -> str:
        """Change specific attributes of the image."""
        return f"""
주어진 이미지의 특정 속성을 변경하여 새로운 이미지를 생성해주세요.
변경 요청 사항: {instructions}
원본 이미지를 바탕으로 요청된 사항만 자연스럽게 수정해주세요.
"""

    @staticmethod
    def create_thumbnail_with_metadata(metadata: dict) -> str:
        """Create thumbnail image based on metadata."""
        return f"""
제품 이미지와 메타데이터를 바탕으로 시선을 끄는 썸네일 이미지를 생성해주세요.
메타데이터: {metadata}
제품의 특징이 잘 드러나도록 매력적인 배경이나 구성을 추가해주세요.
"""

    @staticmethod
    def apply_style_from_reference() -> str:
        """Apply style from reference images to product."""
        return """
첫 번째 이미지는 제품 이미지이며, 나머지 이미지들은 스타일 레퍼런스입니다.
제품의 고유 속성(색상,형태)는 유지하되, 질감, 분위기, 배경 및 소품은 레퍼런스 스타일에 맞춰 변경해주세요.
"""

    @staticmethod
    def replace_object_in_reference(object_to_replace: str = "") -> str:
        """Replace masked area with context from reference images."""
        return f"""
첫 번째 이미지는 원본 이미지이고, 두 번째 이미지는 마스크입니다.
마스크는 편집할 영역을 나타냅니다.
세 번째 이미지부터는 스타일 및 컨텍스트 레퍼런스입니다.
원본 이미지의 마스크된 영역을 레퍼런스 이미지의 스타일과 컨텍스트를 활용하여 자연스럽게 채워주세요.
{object_to_replace}
"""

    @staticmethod
    def create_interior_scene() -> str:
        """Create harmonious interior scene with multiple products."""
        return """
제공된 여러 제품 이미지들을 활용하여 조화로운 인테리어 장면을 연출해주세요.
반드시, **제품의 고유 속성(색상,형태)**는 유지되어야 합니다.
모든 제품이 하나의 공간에 자연스럽게 배치된 것처럼 보이게 해주세요.
"""