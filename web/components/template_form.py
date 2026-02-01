# -*- coding: utf-8 -*-
"""
Template Input Forms

Interactive forms for each template type.
Based on specification document pages 4-23.
"""

import streamlit as st
from typing import Optional, Dict


def show_template_dialog(template_name: str) -> Optional[Dict]:
    """
    Show template input dialog based on template type.

    Args:
        template_name: Name of the selected template

    Returns:
        Dictionary of form inputs or None if cancelled
    """
    if template_name == "SNS/마케팅 광고 소재":
        return show_sns_marketing_form()
    elif template_name == "스튜디오 촬영 이미지 생성":
        return show_studio_shooting_form()
    elif template_name == "스타일 기반 이미지 생성":
        return show_style_based_form()
    elif template_name == "다국어 변환 이미지 생성":
        return show_multilingual_form()
    elif template_name == "인포그래픽 이미지 생성":
        return show_infographic_form()
    elif template_name == "삽화 이미지 생성":
        return show_illustration_form()
    elif template_name == "일러스트 이미지 완성":
        return show_artwork_completion_form()
    else:
        st.info(f"'{template_name}' 템플릿 입력 폼 구현 예정")
        return None


@st.dialog("📱 SNS/마케팅 광고 소재", width="large")
def show_sns_marketing_form() -> Optional[Dict]:
    """
    Show SNS/Marketing material input form.

    Based on spec page 4: Template Input Popup for SNS/Marketing.

    Returns:
        Dictionary containing form inputs or None if cancelled
    """
    st.markdown("### SNS/마케팅 광고 소재 생성")

    # Product Name (Required)
    st.markdown("#### 제품명* ")
    col1, col2 = st.columns([3, 1])
    with col1:
        product_name = st.text_input(
            "제품명",
            placeholder="예: CS2203",
            label_visibility="collapsed",
            key="sns_product_name"
        )
    with col2:
        search_method = st.radio(
            "입력 방식",
            ["검색", "업로드"],
            horizontal=True,
            label_visibility="collapsed",
            key="sns_search_method"
        )

    if search_method == "검색":
        st.info("💡 DAM에서 제품을 검색하여 선택하세요 (DAM 연동 예정)")
    else:
        uploaded_product = st.file_uploader(
            "제품 이미지 업로드",
            type=['png', 'jpg', 'jpeg', 'webp'],
            label_visibility="collapsed",
            key="sns_product_upload"
        )

    # Target Audience (Required)
    st.markdown("#### 타겟고객*")
    target_audience = st.text_area(
        "타겟고객",
        placeholder="예: 20~30대 신혼부부",
        label_visibility="collapsed",
        height=100,
        key="sns_target_audience"
    )

    # Layout (Required)
    st.markdown("#### 레이아웃*")
    layout_ratio = st.selectbox(
        "레이아웃 비율",
        ["1:1 정방형", "4:5 세로형", "9:16 세로형", "16:9 가로형"],
        label_visibility="collapsed",
        key="sns_layout"
    )

    # Show layout guidance
    if layout_ratio == "1:1 정방형":
        st.info("""
        **레이아웃 구성:**
        - 상단(15%): 메인카피 (감성자극)
        - 중단(60%): 제품 이미지(시선 집중)
        - 하단(25%): 제품명, 서브카피, 핵심 기능 아이콘
        """)

    # Concept (Optional)
    st.markdown("#### 컨셉")
    concept = st.text_area(
        "컨셉/광고 목적",
        placeholder="예: 우리 둘만의 완벽한 쉼, 소파가 완성하는 신혼로망",
        label_visibility="collapsed",
        height=80,
        key="sns_concept"
    )

    # Reference Document (Optional)
    st.markdown("#### 참조 문서*")
    reference_file = st.file_uploader(
        "참조 문서 업로드 (PNG, PDF)",
        type=['png', 'pdf'],
        label_visibility="collapsed",
        key="sns_reference"
    )

    if reference_file:
        st.success(f"✓ {reference_file.name} 업로드됨")

    # Additional Fields
    with st.expander("➕ 항목 추가"):
        st.text_input("키 (Key)", key="sns_custom_key")
        st.text_input("값 (Value)", key="sns_custom_value")

    st.markdown("---")

    # Action buttons
    col1, col2 = st.columns(2)
    with col1:
        if st.button("취소", use_container_width=True):
            st.rerun()

    with col2:
        # Check if required fields are filled
        is_valid = bool(product_name and target_audience and layout_ratio)

        if st.button(
            "확인",
            type="primary",
            use_container_width=True,
            disabled=not is_valid
        ):
            # Return form data
            return {
                'template_type': 'SNS/마케팅 광고 소재',
                'product_name': product_name,
                'target_audience': target_audience,
                'layout': layout_ratio,
                'concept': concept,
                'reference_file': reference_file,
                'uploaded_product': uploaded_product if search_method == "업로드" else None
            }

    if not is_valid:
        st.warning("⚠️ 필수 항목(*)을 모두 입력해주세요.")

    return None


@st.dialog("📸 스튜디오 촬영 이미지 생성", width="large")
def show_studio_shooting_form() -> Optional[Dict]:
    """Show Studio Shooting template input form."""
    st.markdown("### 스튜디오 촬영 이미지 생성")

    # Product Image
    st.markdown("#### 제품 이미지*")
    product_image = st.file_uploader(
        "메인 제품 이미지 업로드",
        type=['png', 'jpg', 'jpeg', 'webp'],
        label_visibility="collapsed",
        key="studio_product"
    )

    # Model Setting
    st.markdown("#### 모델 설정")
    model_setting = st.text_input(
        "모델 설정",
        placeholder="예: model_kuho_plus.png",
        label_visibility="collapsed",
        key="studio_model"
    )

    # Shooting Concept
    st.markdown("#### 촬영 콘셉트")
    shooting_concept = st.text_area(
        "촬영 콘셉트",
        value="미니멀리즘 하이엔드 패션 룩북",
        label_visibility="collapsed",
        height=80,
        key="studio_concept"
    )

    # Combination Products (Optional)
    st.markdown("#### 조합 제품 (선택)")
    combination_products = st.file_uploader(
        "추가 제품 이미지 (Cross-Sell용)",
        type=['png', 'jpg', 'jpeg', 'webp'],
        accept_multiple_files=True,
        label_visibility="collapsed",
        key="studio_combination"
    )

    st.markdown("---")

    # Action buttons
    col1, col2 = st.columns(2)
    with col1:
        if st.button("취소", use_container_width=True, key="studio_cancel"):
            st.rerun()

    with col2:
        is_valid = bool(product_image)

        if st.button("확인", type="primary", use_container_width=True, disabled=not is_valid, key="studio_confirm"):
            return {
                'template_type': '스튜디오 촬영 이미지 생성',
                'product_image': product_image,
                'model_setting': model_setting,
                'shooting_concept': shooting_concept,
                'combination_products': combination_products
            }

    return None


@st.dialog("🌐 다국어 변환 이미지 생성", width="large")
def show_multilingual_form() -> Optional[Dict]:
    """Show Multilingual Conversion template input form."""
    st.markdown("### 다국어 변환 이미지 생성")

    # Original Image
    st.markdown("#### 원본 이미지*")
    original_image = st.file_uploader(
        "원본 이미지 업로드",
        type=['png', 'jpg', 'jpeg', 'webp'],
        label_visibility="collapsed",
        key="multi_original"
    )

    # Target Language
    st.markdown("#### 변환 대상 언어*")
    target_language = st.selectbox(
        "언어 선택",
        ["일본어", "영어", "중국어(간체)", "중국어(번체)", "스페인어", "프랑스어"],
        label_visibility="collapsed",
        key="multi_language"
    )

    # Font Settings
    st.markdown("#### 폰트 설정")
    with st.expander("폰트 상세 설정"):
        font_family = st.text_input("폰트 패밀리", placeholder="자동 선택", key="multi_font")
        emphasis_keywords = st.text_input("강조 키워드", placeholder="강조할 단어", key="multi_emphasis")
        translation_tone = st.selectbox("번역 톤", ["일반", "정중", "친근", "전문적"], key="multi_tone")

    # Requirements
    st.markdown("#### 필수사항")
    requirements = st.text_area(
        "필수사항",
        placeholder="예: 강조 키워드 및 번역 톤 설정",
        label_visibility="collapsed",
        height=80,
        key="multi_requirements"
    )

    st.markdown("---")

    # Action buttons
    col1, col2 = st.columns(2)
    with col1:
        if st.button("취소", use_container_width=True, key="multi_cancel"):
            st.rerun()

    with col2:
        is_valid = bool(original_image and target_language)

        if st.button("확인", type="primary", use_container_width=True, disabled=not is_valid, key="multi_confirm"):
            return {
                'template_type': '다국어 변환 이미지 생성',
                'original_image': original_image,
                'target_language': target_language,
                'font_family': font_family,
                'emphasis_keywords': emphasis_keywords,
                'translation_tone': translation_tone,
                'requirements': requirements
            }

    return None


@st.dialog("📊 인포그래픽 이미지 생성", width="large")
def show_infographic_form() -> Optional[Dict]:
    """Show Infographic template input form."""
    st.markdown("### 인포그래픽 이미지 생성")

    # Data Source
    st.markdown("#### 데이터 소스*")
    data_source = st.file_uploader(
        "문서 업로드 (PDF, XLSX 등)",
        type=['pdf', 'xlsx', 'csv'],
        label_visibility="collapsed",
        key="infographic_data"
    )

    # Content Type
    st.markdown("#### 콘텐츠 유형*")
    content_type = st.radio(
        "유형 선택",
        ["시리즈형", "단일형"],
        horizontal=True,
        label_visibility="collapsed",
        key="infographic_type"
    )

    # Purpose
    st.markdown("#### 목적*")
    purpose = st.text_input(
        "목적",
        placeholder="예: 프로덕트 제품 교육",
        label_visibility="collapsed",
        key="infographic_purpose"
    )

    # Target Audience
    st.markdown("#### 타겟 오디언스")
    target_audience = st.text_input(
        "타겟 오디언스",
        placeholder="예: 신규 영업사원",
        label_visibility="collapsed",
        key="infographic_audience"
    )

    # Visual Style
    st.markdown("#### 시각화 스타일*")
    visual_style = st.selectbox(
        "스타일 선택",
        ["프레젠테이션 슬라이드", "그리드형", "타임라인", "플로우차트", "인포그래픽 차트"],
        label_visibility="collapsed",
        key="infographic_style"
    )

    # Key Message
    st.markdown("#### 핵심 메시지")
    key_message = st.text_area(
        "핵심 메시지",
        placeholder="전달하고자 하는 핵심 메시지를 입력하세요",
        label_visibility="collapsed",
        height=100,
        key="infographic_message"
    )

    st.markdown("---")

    # Action buttons
    col1, col2 = st.columns(2)
    with col1:
        if st.button("취소", use_container_width=True, key="infographic_cancel"):
            st.rerun()

    with col2:
        is_valid = bool(data_source and content_type and purpose and visual_style)

        if st.button("확인", type="primary", use_container_width=True, disabled=not is_valid, key="infographic_confirm"):
            return {
                'template_type': '인포그래픽 이미지 생성',
                'data_source': data_source,
                'content_type': content_type,
                'purpose': purpose,
                'target_audience': target_audience,
                'visual_style': visual_style,
                'key_message': key_message
            }

    return None


@st.dialog("🎨 스타일 기반 이미지 생성", width="large")
def show_style_based_form() -> Optional[Dict]:
    """Show Style-based Image Generation template input form."""
    st.markdown("### 스타일 기반 이미지 생성")

    # Product Image
    st.markdown("#### 제품 이미지*")
    product_image = st.file_uploader(
        "제품 이미지 업로드",
        type=['png', 'jpg', 'jpeg', 'webp'],
        label_visibility="collapsed",
        key="style_product"
    )

    # Reference Style Images
    st.markdown("#### 레퍼런스 스타일 이미지*")
    st.caption("제품 배치, 공간 연출 등 원하는 스타일의 참조 이미지를 업로드하세요 (최대 3개)")

    reference_images = st.file_uploader(
        "레퍼런스 이미지 업로드",
        type=['png', 'jpg', 'jpeg', 'webp'],
        accept_multiple_files=True,
        label_visibility="collapsed",
        key="style_reference"
    )

    # Placement Requirements
    st.markdown("#### 배치 요구사항")
    placement = st.text_area(
        "배치 요구사항",
        placeholder="예: 거실 소파 위에 배치, 자연광이 들어오는 창가 연출",
        label_visibility="collapsed",
        height=100,
        key="style_placement"
    )

    # Environment/Scene
    st.markdown("#### 환경/장면 설정")
    environment = st.selectbox(
        "환경 유형",
        ["거실", "침실", "주방", "사무실", "카페", "야외", "스튜디오", "사용자 정의"],
        label_visibility="collapsed",
        key="style_environment"
    )

    if environment == "사용자 정의":
        custom_environment = st.text_input(
            "환경 상세 설명",
            placeholder="예: 북유럽풍 미니멀 인테리어 공간",
            key="style_custom_env"
        )

    # Mood/Atmosphere
    st.markdown("#### 분위기")
    mood = st.multiselect(
        "원하는 분위기 (복수 선택 가능)",
        ["따뜻한", "차가운", "고급스러운", "캐주얼한", "모던한", "빈티지한", "자연스러운", "화려한"],
        default=["따뜻한"],
        key="style_mood"
    )

    # Lighting
    st.markdown("#### 조명 설정")
    lighting = st.radio(
        "조명 타입",
        ["자연광", "인공조명", "혼합", "자동"],
        horizontal=True,
        label_visibility="collapsed",
        key="style_lighting"
    )

    st.markdown("---")

    # Action buttons
    col1, col2 = st.columns(2)
    with col1:
        if st.button("취소", use_container_width=True, key="style_cancel"):
            st.rerun()

    with col2:
        is_valid = bool(product_image and reference_images)

        if st.button("확인", type="primary", use_container_width=True, disabled=not is_valid, key="style_confirm"):
            return {
                'template_type': '스타일 기반 이미지 생성',
                'product_image': product_image,
                'reference_images': reference_images[:3] if reference_images else [],
                'placement': placement,
                'environment': custom_environment if environment == "사용자 정의" else environment,
                'mood': mood,
                'lighting': lighting
            }

    if not is_valid:
        st.warning("⚠️ 제품 이미지와 레퍼런스 이미지를 업로드해주세요.")

    return None


@st.dialog("🖼️ 삽화 이미지 생성", width="large")
def show_illustration_form() -> Optional[Dict]:
    """Show Illustration Image Generation template input form."""
    st.markdown("### 삽화 이미지 생성")

    # Content Type
    st.markdown("#### 콘텐츠 유형*")
    content_type = st.selectbox(
        "유형",
        ["뉴스 기사", "웹소설", "블로그 포스트", "교육 자료", "보고서", "프레젠테이션"],
        label_visibility="collapsed",
        key="illust_content_type"
    )

    # Text Content
    st.markdown("#### 텍스트 내용*")
    st.caption("삽화로 표현할 텍스트 내용을 입력하세요")

    text_content = st.text_area(
        "텍스트 내용",
        placeholder="예: 주인공이 어두운 숲 속에서 빛나는 검을 발견하는 장면. 달빛이 나뭇잎 사이로 비치고 있다.",
        label_visibility="collapsed",
        height=150,
        key="illust_text"
    )

    # Main Subject/Theme
    st.markdown("#### 주제/주요 소재*")
    subject = st.text_input(
        "주제",
        placeholder="예: 판타지 검, 신비한 숲, 모험",
        label_visibility="collapsed",
        key="illust_subject"
    )

    # Visual Style
    st.markdown("#### 시각 스타일*")
    visual_style = st.selectbox(
        "스타일",
        [
            "사실적 일러스트",
            "수채화 스타일",
            "만화/웹툰 스타일",
            "벡터 그래픽",
            "디지털 페인팅",
            "연필 스케치",
            "유화 스타일"
        ],
        label_visibility="collapsed",
        key="illust_style"
    )

    # Color Palette
    st.markdown("#### 색상 팔레트")
    color_palette = st.radio(
        "색상 톤",
        ["밝은 톤", "어두운 톤", "중간 톤", "흑백", "사용자 정의"],
        horizontal=True,
        label_visibility="collapsed",
        key="illust_color"
    )

    if color_palette == "사용자 정의":
        custom_colors = st.text_input(
            "주요 색상 지정",
            placeholder="예: 파란색, 금색, 어두운 녹색",
            key="illust_custom_colors"
        )

    # Composition
    st.markdown("#### 구도")
    composition = st.selectbox(
        "구도 스타일",
        ["중앙 집중", "좌우 대칭", "삼분할", "대각선", "원근감", "자동"],
        label_visibility="collapsed",
        key="illust_composition"
    )

    # Aspect Ratio
    st.markdown("#### 비율")
    aspect_ratio = st.selectbox(
        "이미지 비율",
        ["1:1 정방형", "4:3 가로형", "16:9 와이드", "3:4 세로형", "9:16 세로 와이드"],
        label_visibility="collapsed",
        key="illust_ratio"
    )

    # Additional Details
    with st.expander("➕ 추가 세부사항"):
        mood = st.text_input("분위기", placeholder="예: 긴장감 넘치는, 신비로운", key="illust_mood")
        details = st.text_area(
            "추가 세부 사항",
            placeholder="특정 요소나 표현 방식에 대한 추가 설명",
            height=80,
            key="illust_details"
        )

    st.markdown("---")

    # Action buttons
    col1, col2 = st.columns(2)
    with col1:
        if st.button("취소", use_container_width=True, key="illust_cancel"):
            st.rerun()

    with col2:
        is_valid = bool(text_content and subject and visual_style)

        if st.button("확인", type="primary", use_container_width=True, disabled=not is_valid, key="illust_confirm"):
            return {
                'template_type': '삽화 이미지 생성',
                'content_type': content_type,
                'text_content': text_content,
                'subject': subject,
                'visual_style': visual_style,
                'color_palette': custom_colors if color_palette == "사용자 정의" else color_palette,
                'composition': composition,
                'aspect_ratio': aspect_ratio,
                'mood': mood if 'mood' in locals() else '',
                'details': details if 'details' in locals() else ''
            }

    if not is_valid:
        st.warning("⚠️ 필수 항목(*)을 모두 입력해주세요.")

    return None


@st.dialog("✏️ 일러스트 이미지 완성", width="large")
def show_artwork_completion_form() -> Optional[Dict]:
    """Show Artwork Completion template input form."""
    st.markdown("### 일러스트 이미지 완성")

    # Sketch Image
    st.markdown("#### 스케치 이미지*")
    st.caption("채색 및 완성할 스케치, 러프 이미지를 업로드하세요")

    sketch_image = st.file_uploader(
        "스케치 이미지 업로드",
        type=['png', 'jpg', 'jpeg', 'webp'],
        label_visibility="collapsed",
        key="artwork_sketch"
    )

    if sketch_image:
        st.image(sketch_image, caption="업로드된 스케치", use_container_width=True)

    # Artwork Type
    st.markdown("#### 작업 유형*")
    artwork_type = st.selectbox(
        "유형",
        ["의상 디자인", "캐릭터 일러스트", "웹툰/만화", "컨셉 아트", "제품 디자인", "건축 스케치"],
        label_visibility="collapsed",
        key="artwork_type"
    )

    # Coloring Style
    st.markdown("#### 채색 스타일*")
    coloring_style = st.selectbox(
        "스타일",
        [
            "사실적 채색",
            "셀 쉐이딩 (애니메이션)",
            "수채화 터치",
            "디지털 페인팅",
            "플랫 디자인",
            "그라데이션 중심",
            "파스텔 톤"
        ],
        label_visibility="collapsed",
        key="artwork_coloring"
    )

    # Color Scheme
    st.markdown("#### 색상 구성")
    color_scheme = st.radio(
        "색상 지정 방법",
        ["자동 (AI 추천)", "색상 팔레트 지정", "레퍼런스 이미지 참조"],
        label_visibility="collapsed",
        key="artwork_color_method"
    )

    if color_scheme == "색상 팔레트 지정":
        col1, col2, col3 = st.columns(3)
        with col1:
            primary_color = st.color_picker("주 색상", "#FF6B6B", key="artwork_primary")
        with col2:
            secondary_color = st.color_picker("보조 색상", "#4ECDC4", key="artwork_secondary")
        with col3:
            accent_color = st.color_picker("강조 색상", "#FFE66D", key="artwork_accent")

    elif color_scheme == "레퍼런스 이미지 참조":
        reference_color_image = st.file_uploader(
            "색상 참조 이미지",
            type=['png', 'jpg', 'jpeg', 'webp'],
            key="artwork_color_ref"
        )

    # Detail Level
    st.markdown("#### 완성도*")
    detail_level = st.select_slider(
        "디테일 수준",
        options=["최소", "낮음", "보통", "높음", "최고"],
        value="높음",
        label_visibility="collapsed",
        key="artwork_detail"
    )

    # Shading/Lighting
    st.markdown("#### 음영/조명")
    shading = st.checkbox("음영 추가", value=True, key="artwork_shading")
    if shading:
        light_source = st.selectbox(
            "광원 위치",
            ["좌측 상단", "우측 상단", "정면", "후면", "자동"],
            key="artwork_light"
        )

    # Texture
    st.markdown("#### 질감 표현")
    texture = st.multiselect(
        "추가할 질감 (복수 선택 가능)",
        ["종이 질감", "캔버스 질감", "직물 질감", "금속 질감", "없음"],
        default=["없음"],
        key="artwork_texture"
    )

    # Special Effects
    with st.expander("🎨 특수 효과"):
        add_glow = st.checkbox("발광 효과", key="artwork_glow")
        add_blur = st.checkbox("배경 블러", key="artwork_blur")
        add_grain = st.checkbox("필름 그레인", key="artwork_grain")

    # Additional Instructions
    st.markdown("#### 추가 지시사항")
    instructions = st.text_area(
        "특별 요청사항",
        placeholder="예: 눈동자는 파란색으로, 배경은 따뜻한 톤으로 완성해주세요",
        label_visibility="collapsed",
        height=100,
        key="artwork_instructions"
    )

    st.markdown("---")

    # Action buttons
    col1, col2 = st.columns(2)
    with col1:
        if st.button("취소", use_container_width=True, key="artwork_cancel"):
            st.rerun()

    with col2:
        is_valid = bool(sketch_image and artwork_type and coloring_style)

        if st.button("확인", type="primary", use_container_width=True, disabled=not is_valid, key="artwork_confirm"):
            result = {
                'template_type': '일러스트 이미지 완성',
                'sketch_image': sketch_image,
                'artwork_type': artwork_type,
                'coloring_style': coloring_style,
                'detail_level': detail_level,
                'shading': shading,
                'texture': texture,
                'instructions': instructions
            }

            # Add color scheme based on method
            if color_scheme == "색상 팔레트 지정":
                result['color_scheme'] = {
                    'method': 'palette',
                    'primary': primary_color,
                    'secondary': secondary_color,
                    'accent': accent_color
                }
            elif color_scheme == "레퍼런스 이미지 참조":
                result['color_scheme'] = {
                    'method': 'reference',
                    'reference_image': reference_color_image if 'reference_color_image' in locals() else None
                }
            else:
                result['color_scheme'] = {'method': 'auto'}

            # Add optional fields
            if shading and 'light_source' in locals():
                result['light_source'] = light_source

            if 'add_glow' in locals():
                result['effects'] = {
                    'glow': add_glow,
                    'blur': add_blur if 'add_blur' in locals() else False,
                    'grain': add_grain if 'add_grain' in locals() else False
                }

            return result

    if not is_valid:
        st.warning("⚠️ 필수 항목(*)을 모두 입력해주세요.")

    return None