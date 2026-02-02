# -*- coding: utf-8 -*-
"""
CEN AI DAM Editor - Image Editor Page

Full-featured image editing interface based on specification document (pages 3-9).

Features:
- Left Menu Panel (Templates, New Project, Text, Upload, AI Tools, Home)
- Top Toolbar (Canvas Move, Pencil, Highlighter, Eraser, Shape, Object Selection)
- Main Canvas Area
- Right History Panel
- Bottom Prompt Input + Apply Button
- Reference Images Accordion
"""

import streamlit as st
import os
import sys
from PIL import Image, ImageDraw
import io
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from streamlit_drawable_canvas import st_canvas
import numpy as np

from core import ImageGenerator, ImageAnalyzer
from utils.session import init_session_state, get_user_workspace_dir
from utils.file_handler import save_uploaded_file, save_generated_images
from components.ai_tools_panel import show_ai_tools_panel, apply_ai_tool
from utils.project_manager import ProjectManager
from web.common.styles import load_editor_styles

# Page configuration
st.set_page_config(
    page_title="이미지 에디터 - CEN AI DAM Editor",
    page_icon="🎨",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS
load_editor_styles()


def init_editor_state():
    """Initialize editor-specific session state."""
    init_session_state()

    if 'current_canvas_image' not in st.session_state:
        st.session_state.current_canvas_image = None

    if 'canvas_history' not in st.session_state:
        st.session_state.canvas_history = []

    if 'reference_images' not in st.session_state:
        st.session_state.reference_images = []

    if 'current_tool' not in st.session_state:
        st.session_state.current_tool = 'select'
        
    if 'stroke_width' not in st.session_state:
        st.session_state.stroke_width = 5
        
    if 'stroke_color' not in st.session_state:
        st.session_state.stroke_color = '#000000'
        
    if 'shape_type' not in st.session_state:
        st.session_state.shape_type = 'rect'

    if 'reference_expanded' not in st.session_state:
        st.session_state.reference_expanded = True

    if 'current_project_path' not in st.session_state:
        st.session_state.current_project_path = None

    if 'current_project_name' not in st.session_state:
        st.session_state.current_project_name = None


def show_left_menu():
    """Render left menu panel."""
    with st.container():
        st.markdown("""
        <div style='background: #273444; padding: 20px 10px; border-radius: 0 12px 12px 0; min-height: 100vh;'>
        """, unsafe_allow_html=True)

        # Menu items
        col = st.columns(1)[0]

        # Template
        if st.button("📋\n템플릿", key="menu_template", use_container_width=True):
            st.info("템플릿 선택 (구현 예정)")

        # New Project
        if st.button("➕\n새 프로젝트", key="menu_new", use_container_width=True):
            st.session_state.current_canvas_image = None
            st.session_state.canvas_history = []
            st.session_state.reference_images = []
            st.session_state.current_project_path = None
            st.session_state.current_project_name = None
            st.success("새 프로젝트 생성됨")
            st.rerun()

        # Save Project
        if st.button("💾\n저장", key="menu_save", use_container_width=True):
            if st.session_state.current_canvas_image is None:
                st.warning("저장할 내용이 없습니다")
            else:
                st.session_state.show_save_dialog = True
                st.rerun()

        # Load Project
        if st.button("📂\n불러오기", key="menu_load", use_container_width=True):
            st.session_state.show_load_dialog = True
            st.rerun()

        # Save to DAM
        if st.button("📦\nDAM 저장", key="menu_save_dam", use_container_width=True):
            if st.session_state.current_canvas_image is None:
                st.warning("저장할 이미지가 없습니다")
            else:
                st.session_state.show_save_dam_dialog = True
                st.rerun()

        # Text
        if st.button("T\n텍스트", key="menu_text", use_container_width=True):
            st.info("텍스트 도구 (구현 예정)")

        # Upload
        uploaded = st.file_uploader(
            "⬆️\n업로드",
            type=['png', 'jpg', 'jpeg', 'webp'],
            key="menu_upload",
            label_visibility="collapsed"
        )

        if uploaded:
            # Save and load uploaded image
            workspace_dir = st.session_state.user['workspace_dir']
            img_path = save_uploaded_file(uploaded, workspace_dir)

            # Load to canvas
            image = Image.open(img_path)
            st.session_state.current_canvas_image = image
            st.session_state.canvas_history.append(image.copy())
            st.success("이미지 업로드 완료!")
            st.rerun()

        # AI Tools
        if st.button("🤖\nAI 도구", key="menu_ai", use_container_width=True):
            if st.session_state.current_canvas_image is None:
                st.warning("먼저 이미지를 업로드해주세요")
            else:
                # Show AI tools panel
                tool_data = show_ai_tools_panel()

                if tool_data:
                    # Apply AI tool to current canvas
                    with st.spinner(f"AI 도구 '{tool_data['tool']}' 적용 중..."):
                        workspace_dir = st.session_state.user['workspace_dir']
                        processed_image = apply_ai_tool(
                            tool_data,
                            st.session_state.current_canvas_image,
                            workspace_dir
                        )

                        if processed_image:
                            st.session_state.current_canvas_image = processed_image
                            st.session_state.canvas_history.append(processed_image.copy())
                            st.success(f"✅ '{tool_data['tool']}' 적용 완료!")
                            st.rerun()

        # Spacer
        st.markdown("<div style='flex: 1;'></div>", unsafe_allow_html=True)

        # Home
        if st.button("🏠\n홈화면", key="menu_home", use_container_width=True):
            st.switch_page("app.py")

        st.markdown("</div>", unsafe_allow_html=True)


def show_toolbar():
    """Render top toolbar with drawing controls."""
    st.markdown("### 🛠️ 툴바")

    # Tool selection
    tools = [
        ("👆", "transform", "객체선택/이동"),
        ("✏️", "freedraw", "펜슬"),
        ("🖍️", "freedraw", "형광펜"), # Note: Same as pencil, but could use different color/opacity
        ("🧹", "eraser", "지우개"), # Note: Not a direct mode, handled by background color
        ("⬜", "rect", "사각형"),
        ("⭕", "circle", "원"),
        ("〰️", "line", "선"),
    ]
    
    tool_ids = [tool[1] for tool in tools]
    tool_labels = [f"{tool[0]} {tool[2]}" for tool in tools]

    # Map our tool names to canvas drawing modes
    tool_map = {
        "select": "transform",
        "pencil": "freedraw",
        "highlighter": "freedraw",
        "eraser": "freedraw", # Eraser is free drawing with background color
        "shape": "rect", # Default shape
        "canvas_move": "transform",
    }
    
    # Update current_tool if a shape is selected
    if st.session_state.current_tool in ["rect", "circle", "line"]:
        st.session_state.current_tool = "shape"

    selected_tool_label = tool_labels[tool_ids.index(tool_map.get(st.session_state.current_tool, "transform"))]

    cols = st.columns([2, 1, 1, 3])
    with cols[0]:
        st.session_state.current_tool = st.selectbox(
            "도구 선택", 
            options=["select", "pencil", "highlighter", "eraser", "shape", "canvas_move"],
            format_func=lambda x: {
                "select": "👆 객체선택", "pencil": "✏️ 펜슬", "highlighter": "🖍️ 형광펜",
                "eraser": "🧹 지우개", "shape": "⬜ 도형", "canvas_move": "🔲 캔버스 이동"
            }.get(x),
            key="tool_selector"
        )

    # Drawing controls
    drawing_mode = tool_map.get(st.session_state.current_tool, "transform")

    with cols[1]:
        stroke_width = st.slider("굵기", 1, 50, 5, key="stroke_width")

    with cols[2]:
        stroke_color = st.color_picker("색상", "#000000", key="stroke_color")
        
    # Specific controls for shape tool
    if st.session_state.current_tool == "shape":
        with cols[3]:
            drawing_mode = st.radio("도형 종류", ["rect", "circle", "line"], horizontal=True, key="shape_type")


def show_canvas():
    """Render main canvas area using streamlit-drawable-canvas."""
    st.markdown("### 🎨 캔버스")

    if st.session_state.current_canvas_image is None:
        st.markdown("""
        <div class='canvas-placeholder'>
            <div style='font-size: 48px; margin-bottom: 16px;'>🖼️</div>
            <div style='font-size: 18px; font-weight: 600; margin-bottom: 8px;'>캔버스가 비어있습니다</div>
            <div style='font-size: 14px;'>좌측 메뉴에서 이미지를 업로드하거나 새 프로젝트를 생성하세요</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        # Tool mapping
        tool_map = {
            "select": "transform",
            "pencil": "freedraw",
            "highlighter": "freedraw",
            "eraser": "freedraw",
            "shape": st.session_state.get("shape_type", "rect"),
            "canvas_move": "transform"
        }
        drawing_mode = tool_map.get(st.session_state.current_tool, "transform")
        
        # Eraser works by drawing with the background color
        # This is a simple implementation. A better one would handle transparency.
        stroke_color = "#FFFFFF" if st.session_state.current_tool == "eraser" else st.session_state.stroke_color

        # Set canvas properties
        canvas_result = st_canvas(
            fill_color="rgba(255, 165, 0, 0.3)",  # Color for shape fill
            stroke_width=st.session_state.stroke_width,
            stroke_color=stroke_color,
            background_image=st.session_state.current_canvas_image,
            update_streamlit=True,
            height=st.session_state.current_canvas_image.height,
            width=st.session_state.current_canvas_image.width,
            drawing_mode=drawing_mode,
            key="canvas",
        )

        # If the user has drawn something, update the image
        if canvas_result.image_data is not None:
            # Check if the canvas is not empty (i.e., drawings were made)
            if not np.array_equal(
                np.array(st.session_state.current_canvas_image), canvas_result.image_data
            ):
                # Convert canvas output to PIL Image
                new_image = Image.fromarray(canvas_result.image_data).convert("RGB")
                
                # Update session state only if image has changed
                # This check prevents loops on rerun
                if not st.session_state.current_canvas_image.tobytes() == new_image.tobytes():
                    st.session_state.current_canvas_image = new_image
                    st.session_state.canvas_history.append(new_image.copy())
                    st.success("드로잉 적용 완료!")
                    st.rerun()

        # Quick actions
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            if st.button("↩️ 실행취소", use_container_width=True):
                if len(st.session_state.canvas_history) > 1:
                    st.session_state.canvas_history.pop()
                    st.session_state.current_canvas_image = st.session_state.canvas_history[-1].copy()
                    st.rerun()
                elif len(st.session_state.canvas_history) == 1:
                     st.warning("더 이상 되돌릴 내역이 없습니다.")


        with col2:
            if st.button("💾 저장", use_container_width=True):
                workspace_dir = st.session_state.user['workspace_dir']
                save_dir = os.path.join(workspace_dir, 'generated')
                os.makedirs(save_dir, exist_ok=True)

                from datetime import datetime
                filename = f"canvas_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                filepath = os.path.join(save_dir, filename)

                st.session_state.current_canvas_image.save(filepath)
                st.success(f"저장 완료: {filename}")

        with col3:
            if st.button("🗑️ 초기화", use_container_width=True):
                st.session_state.current_canvas_image = None
                st.session_state.canvas_history = []
                st.rerun()

        with col4:
            # Download button
            if st.session_state.current_canvas_image:
                buf = io.BytesIO()
                st.session_state.current_canvas_image.save(buf, format='PNG')
                byte_im = buf.getvalue()

                st.download_button(
                    label="⬇️ 다운로드",
                    data=byte_im,
                    file_name="canvas_image.png",
                    mime="image/png",
                    use_container_width=True
                )


def show_history_panel():
    """Render right history panel."""
    st.markdown("### 📜 히스토리")

    if not st.session_state.canvas_history:
        st.info("히스토리가 비어있습니다")
    else:
        st.caption(f"총 {len(st.session_state.canvas_history)}개 항목")

        # Display history items (most recent first)
        for idx, hist_image in enumerate(reversed(st.session_state.canvas_history)):
            with st.container():
                st.image(hist_image, use_container_width=True, caption=f"Step {len(st.session_state.canvas_history) - idx}")

                if st.button("복원", key=f"restore_{idx}", use_container_width=True):
                    st.session_state.current_canvas_image = hist_image.copy()
                    st.rerun()

            st.markdown("---")


def show_prompt_area():
    """Render prompt input and apply button."""
    st.markdown("---")
    st.markdown("### 💬 프롬프트")

    col_prompt, col_btn = st.columns([5, 1])

    with col_prompt:
        prompt = st.text_area(
            "프롬프트를 입력하세요",
            placeholder="예: 배경을 파란색으로 변경하세요",
            height=80,
            key="editor_prompt",
            label_visibility="collapsed"
        )

    with col_btn:
        st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)  # Spacer

        if st.button("🚀 적용하기", type="primary", use_container_width=True, key="apply_prompt"):
            if not prompt:
                st.warning("프롬프트를 입력해주세요")
            elif st.session_state.current_canvas_image is None:
                st.warning("먼저 이미지를 업로드해주세요")
            else:
                # Generate image based on prompt
                with st.spinner("AI가 이미지를 생성하고 있습니다..."):
                    try:
                        workspace_dir = st.session_state.user['workspace_dir']
                        generator = ImageGenerator(os.path.join(workspace_dir, 'generated'))

                        # Save current canvas image temporarily
                        temp_path = os.path.join(workspace_dir, 'temp_canvas.png')
                        st.session_state.current_canvas_image.save(temp_path)

                        # Generate with prompt
                        generated_paths = generator.change_attributes(
                            image_path=temp_path,
                            instructions=[prompt]
                        )

                        if generated_paths:
                            # Load generated image to canvas
                            new_image = Image.open(generated_paths[0])
                            st.session_state.current_canvas_image = new_image
                            st.session_state.canvas_history.append(new_image.copy())

                            st.success("✅ 적용 완료!")
                            st.rerun()
                        else:
                            st.error("이미지 생성 실패")

                    except Exception as e:
                        st.error(f"오류 발생: {str(e)}")


def show_reference_images():
    """Render reference images accordion."""
    st.markdown("---")

    # Accordion header
    col_header, col_toggle = st.columns([5, 1])

    with col_header:
        st.markdown("### 📎 레퍼런스 이미지")

    with col_toggle:
        if st.button("▼" if st.session_state.reference_expanded else "▶", key="toggle_reference"):
            st.session_state.reference_expanded = not st.session_state.reference_expanded
            st.rerun()

    # Accordion content
    if st.session_state.reference_expanded:
        st.caption("최대 2개까지 등록 가능")

        reference_uploads = st.file_uploader(
            "레퍼런스 이미지 업로드",
            type=['png', 'jpg', 'jpeg', 'webp'],
            accept_multiple_files=True,
            key="reference_upload",
            label_visibility="collapsed"
        )

        if reference_uploads:
            # Limit to 2 images
            reference_uploads = reference_uploads[:2]

            st.session_state.reference_images = []

            cols = st.columns(2)
            for idx, ref_file in enumerate(reference_uploads):
                with cols[idx]:
                    image = Image.open(ref_file)
                    st.image(image, caption=f"레퍼런스 {idx+1}", use_container_width=True)

                    # Save to session
                    st.session_state.reference_images.append(image)


@st.dialog("💾 프로젝트 저장", width="large")
def show_save_project_dialog():
    """Show project save dialog."""
    st.markdown("### 프로젝트 저장")

    # Project name input
    default_name = st.session_state.current_project_name or f"Project_{datetime.now().strftime('%Y%m%d')}"
    project_name = st.text_input(
        "프로젝트 이름",
        value=default_name,
        key="save_project_name"
    )

    # Show current status
    st.markdown("**저장될 내용:**")
    st.caption(f"• 캔버스 이미지: {'있음' if st.session_state.current_canvas_image else '없음'}")
    st.caption(f"• 히스토리: {len(st.session_state.canvas_history)}개")
    st.caption(f"• 레퍼런스 이미지: {len(st.session_state.reference_images)}개")

    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("취소", use_container_width=True, key="save_cancel"):
            st.session_state.show_save_dialog = False
            st.rerun()

    with col2:
        if st.button("저장", type="primary", use_container_width=True, key="save_confirm"):
            if not project_name:
                st.warning("프로젝트 이름을 입력해주세요")
            else:
                workspace_dir = st.session_state.user['workspace_dir']
                pm = ProjectManager(workspace_dir)

                # Check if updating existing project or creating new
                if st.session_state.current_project_path:
                    # Update existing project
                    success = pm.update_project(
                        st.session_state.current_project_path,
                        canvas_image=st.session_state.current_canvas_image,
                        canvas_history=st.session_state.canvas_history,
                        reference_images=st.session_state.reference_images
                    )

                    if success:
                        st.success(f"✅ 프로젝트 '{project_name}'이(가) 업데이트되었습니다!")
                    else:
                        st.error("프로젝트 업데이트 실패")
                else:
                    # Save as new project
                    project_path = pm.save_project(
                        project_name=project_name,
                        canvas_image=st.session_state.current_canvas_image,
                        canvas_history=st.session_state.canvas_history,
                        reference_images=st.session_state.reference_images
                    )

                    if project_path:
                        st.session_state.current_project_path = project_path
                        st.session_state.current_project_name = project_name
                        st.success(f"✅ 프로젝트 '{project_name}'이(가) 저장되었습니다!")
                    else:
                        st.error("프로젝트 저장 실패")

                st.session_state.show_save_dialog = False
                st.rerun()


@st.dialog("📂 프로젝트 불러오기", width="large")
def show_load_project_dialog():
    """Show project load dialog."""
    st.markdown("### 프로젝트 불러오기")

    workspace_dir = st.session_state.user['workspace_dir']
    pm = ProjectManager(workspace_dir)

    # List all projects
    projects = pm.list_projects()

    if not projects:
        st.info("저장된 프로젝트가 없습니다.")
        if st.button("닫기", use_container_width=True):
            st.session_state.show_load_dialog = False
            st.rerun()
        return

    st.caption(f"총 {len(projects)}개의 프로젝트")

    # Show projects in grid
    for idx, project in enumerate(projects):
        with st.container():
            col_img, col_info, col_action = st.columns([1, 3, 1])

            with col_img:
                if project.get('thumbnail'):
                    try:
                        thumb_img = Image.open(project['thumbnail'])
                        st.image(thumb_img, use_container_width=True)
                    except:
                        st.markdown("📄")
                else:
                    st.markdown("📄")

            with col_info:
                st.markdown(f"**{project['name']}**")
                st.caption(f"생성: {project.get('created_at', 'Unknown')}")
                st.caption(f"수정: {project.get('modified_at', 'Unknown')}")

            with col_action:
                if st.button("불러오기", key=f"load_{idx}", use_container_width=True):
                    # Load project
                    project_data = pm.load_project(project['project_path'])

                    if project_data:
                        # Update session state
                        st.session_state.current_canvas_image = project_data['canvas_image']
                        st.session_state.canvas_history = project_data['canvas_history']
                        st.session_state.reference_images = project_data['reference_images']
                        st.session_state.current_project_path = project_data['project_path']
                        st.session_state.current_project_name = project_data['name']

                        st.success(f"✅ 프로젝트 '{project_data['name']}'을(를) 불러왔습니다!")
                        st.session_state.show_load_dialog = False
                        st.rerun()
                    else:
                        st.error("프로젝트 불러오기 실패")

                if st.button("🗑️", key=f"delete_{idx}"):
                    if pm.delete_project(project['project_path']):
                        st.success("프로젝트가 삭제되었습니다!")
                        st.rerun()
                    else:
                        st.error("삭제 실패")

            st.markdown("---")

    # Close button
    if st.button("닫기", use_container_width=True, key="load_close"):
        st.session_state.show_load_dialog = False
        st.rerun()


@st.dialog("📦 DAM에 저장", width="large")
def show_save_dam_dialog():
    """Show DAM save dialog with metadata generation."""
    st.markdown("### DAM에 이미지 저장")
    st.caption("이미지를 DAM에 저장하고 AI가 자동으로 메타데이터를 생성합니다.")

    # File name input
    default_name = f"editor_output_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    file_name = st.text_input(
        "파일명 (확장자 제외)",
        value=default_name,
        key="dam_file_name"
    )

    # Optional description
    description = st.text_area(
        "설명 (선택사항)",
        placeholder="이 이미지에 대한 설명을 입력하세요...",
        key="dam_description"
    )

    # AI metadata generation option
    generate_metadata = st.checkbox(
        "AI 메타데이터 자동 생성",
        value=True,
        key="dam_auto_metadata"
    )

    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("취소", use_container_width=True, key="dam_cancel"):
            st.session_state.show_save_dam_dialog = False
            st.rerun()

    with col2:
        if st.button("저장", type="primary", use_container_width=True, key="dam_confirm"):
            if not file_name:
                st.warning("파일명을 입력해주세요")
            else:
                try:
                    workspace_dir = st.session_state.user['workspace_dir']
                    generated_dir = os.path.join(workspace_dir, 'generated')
                    os.makedirs(generated_dir, exist_ok=True)

                    # Save image to generated folder
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    safe_name = "".join(c for c in file_name if c.isalnum() or c in (' ', '-', '_')).strip()
                    output_path = os.path.join(generated_dir, f"{safe_name}_{timestamp}.png")

                    st.session_state.current_canvas_image.save(output_path)

                    # Generate metadata if requested
                    if generate_metadata:
                        with st.spinner("AI 메타데이터 생성 중..."):
                            analyzer = ImageAnalyzer()
                            metadata = analyzer.analyze_image_metadata(output_path)

                            # Add user description if provided
                            if description:
                                metadata['description'] = description

                            # Save metadata
                            metadata_dir = os.path.join(workspace_dir, 'metadata')
                            os.makedirs(metadata_dir, exist_ok=True)

                            metadata_path = os.path.join(
                                metadata_dir,
                                f"{os.path.splitext(os.path.basename(output_path))[0]}.json"
                            )

                            import json
                            with open(metadata_path, 'w', encoding='utf-8') as f:
                                json.dump(metadata, f, ensure_ascii=False, indent=2)

                            st.success(f"✅ DAM에 저장 완료! (메타데이터 포함)")
                    else:
                        st.success(f"✅ DAM에 저장 완료!")

                    st.info(f"저장 경로: {output_path}")

                    st.session_state.show_save_dam_dialog = False

                    # Offer to open DAM
                    if st.button("📦 DAM 시스템 열기", use_container_width=True):
                        st.switch_page("pages/02_📦_DAM_System.py")

                except Exception as e:
                    st.error(f"저장 실패: {str(e)}")
                    st.exception(e)


def main():
    """Main entry point for Image Editor page."""
    init_editor_state()

    # Show save dialog if requested
    if st.session_state.get('show_save_dialog', False):
        show_save_project_dialog()

    # Show load dialog if requested
    if st.session_state.get('show_load_dialog', False):
        show_load_project_dialog()

    # Show DAM save dialog if requested
    if st.session_state.get('show_save_dam_dialog', False):
        show_save_dam_dialog()

    # Show current project name in title
    if st.session_state.current_project_name:
        st.caption(f"📁 현재 프로젝트: {st.session_state.current_project_name}")

    # Layout
    col_menu, col_main, col_history = st.columns([1, 6, 2])

    with col_menu:
        show_left_menu()

    with col_main:
        show_toolbar()
        show_canvas()
        show_prompt_area()
        show_reference_images()

    with col_history:
        show_history_panel()


if __name__ == "__main__":
    main()