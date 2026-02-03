# -*- coding: utf-8 -*-
"""
AI Tools Panel Component

Advanced AI-powered image editing tools for the Image Editor.
Features: Background Removal, Style Transfer, Image Upscaling, Object Operations.
"""

import streamlit as st
from typing import Optional, Dict
from PIL import Image
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from core import ImageGenerator


@st.dialog("🤖 AI 도구", width="large")
def show_ai_tools_panel() -> Optional[Dict]:
    """
    Display AI Tools panel with various AI-powered editing options.

    Returns:
        Dictionary with tool type and parameters, or None if cancelled
    """
    st.markdown("### AI 기반 이미지 편집 도구")

    # Tool selection
    selected_tool = st.selectbox(
        "도구 선택",
        [
            "배경 제거",
            "스타일 전환",
            "이미지 업스케일링",
            "객체 교체",
            "색상 보정",
            "이미지 확장"
        ],
        key="ai_tool_selector"
    )

    st.markdown("---")

    # Tool-specific parameters
    tool_params = {}

    if selected_tool == "배경 제거":
        st.markdown("#### 🎭 배경 제거")
        st.info("현재 캔버스의 이미지에서 배경을 자동으로 제거하고 투명 배경으로 변환합니다.")

        background_option = st.radio(
            "배경 옵션",
            ["투명 배경", "단색 배경", "블러 배경"],
            horizontal=True,
            key="bg_removal_option"
        )

        if background_option == "단색 배경":
            bg_color = st.color_picker("배경 색상 선택", "#FFFFFF", key="bg_color")
            tool_params['background_color'] = bg_color
        elif background_option == "블러 배경":
            blur_intensity = st.slider("블러 강도", 1, 10, 5, key="blur_intensity")
            tool_params['blur_intensity'] = blur_intensity

        tool_params['background_type'] = background_option

    elif selected_tool == "스타일 전환":
        st.markdown("#### 🎨 스타일 전환")
        st.info("레퍼런스 이미지의 스타일을 현재 이미지에 적용합니다.")

        style_preset = st.selectbox(
            "스타일 프리셋",
            [
                "사용자 정의",
                "유화 스타일",
                "수채화 스타일",
                "만화/애니메이션 스타일",
                "미니멀리즘",
                "사실주의",
                "팝아트"
            ],
            key="style_preset"
        )

        if style_preset == "사용자 정의":
            reference_image = st.file_uploader(
                "레퍼런스 이미지 업로드",
                type=['png', 'jpg', 'jpeg', 'webp'],
                key="style_reference"
            )
            tool_params['reference_image'] = reference_image
        else:
            tool_params['preset_style'] = style_preset

        style_intensity = st.slider("스타일 강도", 0, 100, 70, key="style_intensity")
        tool_params['intensity'] = style_intensity

    elif selected_tool == "이미지 업스케일링":
        st.markdown("#### 📐 이미지 업스케일링")
        st.info("AI 기반 고해상도 변환으로 이미지 품질을 향상시킵니다.")

        scale_factor = st.select_slider(
            "확대 배율",
            options=[2, 3, 4, 8],
            value=2,
            key="scale_factor"
        )

        enhance_quality = st.checkbox("추가 품질 향상", value=True, key="enhance_quality")

        tool_params['scale_factor'] = scale_factor
        tool_params['enhance'] = enhance_quality

    elif selected_tool == "객체 교체":
        st.markdown("#### 🔄 객체 교체")
        st.info("이미지 내 특정 객체를 다른 객체로 교체합니다.")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**제거할 객체**")
            object_to_remove = st.text_input(
                "객체 설명",
                placeholder="예: 의자",
                key="object_remove",
                label_visibility="collapsed"
            )

        with col2:
            st.markdown("**추가할 객체**")
            object_to_add = st.text_input(
                "객체 설명",
                placeholder="예: 소파",
                key="object_add",
                label_visibility="collapsed"
            )

        replacement_image = st.file_uploader(
            "교체할 객체 이미지 (선택사항)",
            type=['png', 'jpg', 'jpeg', 'webp'],
            key="replacement_image"
        )

        tool_params['remove_object'] = object_to_remove
        tool_params['add_object'] = object_to_add
        tool_params['replacement_image'] = replacement_image

    elif selected_tool == "색상 보정":
        st.markdown("#### 🌈 색상 보정")
        st.info("이미지의 색상, 밝기, 대비를 AI 기반으로 자동 보정합니다.")

        correction_mode = st.radio(
            "보정 모드",
            ["자동 보정", "수동 조정"],
            horizontal=True,
            key="correction_mode"
        )

        if correction_mode == "수동 조정":
            brightness = st.slider("밝기", -50, 50, 0, key="brightness")
            contrast = st.slider("대비", -50, 50, 0, key="contrast")
            saturation = st.slider("채도", -50, 50, 0, key="saturation")

            tool_params['brightness'] = brightness
            tool_params['contrast'] = contrast
            tool_params['saturation'] = saturation
        else:
            auto_enhance_level = st.select_slider(
                "보정 강도",
                options=["약하게", "보통", "강하게"],
                value="보통",
                key="auto_enhance"
            )
            tool_params['auto_level'] = auto_enhance_level

        tool_params['mode'] = correction_mode

    elif selected_tool == "이미지 확장":
        st.markdown("#### 📏 이미지 확장")
        st.info("AI가 이미지 외곽을 자연스럽게 확장합니다 (Outpainting).")

        col1, col2 = st.columns(2)

        with col1:
            expand_left = st.number_input("왼쪽 확장 (px)", 0, 500, 0, key="expand_left")
            expand_right = st.number_input("오른쪽 확장 (px)", 0, 500, 0, key="expand_right")

        with col2:
            expand_top = st.number_input("위쪽 확장 (px)", 0, 500, 0, key="expand_top")
            expand_bottom = st.number_input("아래쪽 확장 (px)", 0, 500, 0, key="expand_bottom")

        expansion_prompt = st.text_area(
            "확장 영역 설명 (선택사항)",
            placeholder="예: 자연스러운 배경 확장, 동일한 스타일 유지",
            height=80,
            key="expansion_prompt"
        )

        tool_params['expand_left'] = expand_left
        tool_params['expand_right'] = expand_right
        tool_params['expand_top'] = expand_top
        tool_params['expand_bottom'] = expand_bottom
        tool_params['prompt'] = expansion_prompt

    st.markdown("---")

    # Action buttons
    col1, col2 = st.columns(2)

    with col1:
        if st.button("취소", use_container_width=True, key="ai_tools_cancel"):
            st.rerun()

    with col2:
        if st.button("적용", type="primary", use_container_width=True, key="ai_tools_apply"):
            return {
                'tool': selected_tool,
                'params': tool_params
            }

    return None


def apply_ai_tool(tool_data: Dict, current_image: Image.Image, workspace_dir: str) -> Optional[Image.Image]:
    """
    Apply selected AI tool to the current image.

    Args:
        tool_data: Dictionary containing tool type and parameters
        current_image: Current canvas image
        workspace_dir: User workspace directory

    Returns:
        Processed image or None if failed
    """
    tool = tool_data['tool']
    params = tool_data['params']

    try:
        # Save current image temporarily
        temp_path = os.path.join(workspace_dir, 'temp_ai_tool.png')
        current_image.save(temp_path)

        # Initialize generator
        output_dir = os.path.join(workspace_dir, 'generated')
        generator = ImageGenerator(output_dir)

        # Build AI instruction based on tool type
        if tool == "배경 제거":
            if params['background_type'] == "투명 배경":
                instruction = "Remove the background completely and make it transparent, keeping only the main subject"
            elif params['background_type'] == "단색 배경":
                bg_color = params.get('background_color', '#FFFFFF')
                instruction = f"Remove the background and replace it with a solid {bg_color} color background"
            else:  # 블러 배경
                blur = params.get('blur_intensity', 5)
                instruction = f"Apply a blur effect to the background with intensity level {blur}, keeping the main subject sharp"

        elif tool == "스타일 전환":
            if 'preset_style' in params:
                style = params['preset_style']
                intensity = params['intensity']
                instruction = f"Transform this image into {style} style with {intensity}% intensity, maintaining the main composition"
            else:
                instruction = "Apply the style from the reference image to this image while preserving the content"
                # TODO: Handle reference image upload

        elif tool == "이미지 업스케일링":
            scale = params['scale_factor']
            enhance = params.get('enhance', True)
            instruction = f"Upscale this image by {scale}x using AI super-resolution"
            if enhance:
                instruction += " with additional quality enhancement and detail restoration"

        elif tool == "객체 교체":
            remove_obj = params.get('remove_object', '')
            add_obj = params.get('add_object', '')
            if remove_obj and add_obj:
                instruction = f"Replace the {remove_obj} in the image with {add_obj}, maintaining natural lighting and perspective"
            else:
                instruction = "Perform object replacement based on the provided specifications"

        elif tool == "색상 보정":
            if params['mode'] == "자동 보정":
                level = params.get('auto_level', '보통')
                instruction = f"Automatically adjust colors, brightness, and contrast with {level} enhancement level"
            else:
                brightness = params.get('brightness', 0)
                contrast = params.get('contrast', 0)
                saturation = params.get('saturation', 0)
                instruction = f"Adjust image: brightness {brightness:+d}, contrast {contrast:+d}, saturation {saturation:+d}"

        elif tool == "이미지 확장":
            left = params.get('expand_left', 0)
            right = params.get('expand_right', 0)
            top = params.get('expand_top', 0)
            bottom = params.get('expand_bottom', 0)
            custom_prompt = params.get('prompt', '')

            instruction = f"Expand the image outward: {left}px left, {right}px right, {top}px top, {bottom}px bottom"
            if custom_prompt:
                instruction += f". {custom_prompt}"
            else:
                instruction += ". Fill the expanded areas naturally based on the existing image context"

        else:
            st.error(f"알 수 없는 도구: {tool}")
            return None

        # Apply AI tool via generator
        generated_paths = generator.change_attributes(
            image_path=temp_path,
            instructions=[instruction]
        )

        if generated_paths:
            # Load and return processed image
            processed_image = Image.open(generated_paths[0])
            return processed_image
        else:
            st.error("AI 도구 적용 실패")
            return None

    except Exception as e:
        st.error(f"AI 도구 적용 중 오류 발생: {str(e)}")
        return None