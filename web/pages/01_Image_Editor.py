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
from PIL import Image
import io
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from streamlit_drawable_canvas import st_canvas
import numpy as np

from core import ImageGenerator, ImageAnalyzer
from utils.session import init_session_state
from utils.file_handler import save_uploaded_file
from components.ai_tools_panel import show_ai_tools_panel, apply_ai_tool
from components.template_form import show_template_dialog
from utils.project_manager import ProjectManager

# Page configuration
st.set_page_config(
    page_title="이미지 에디터 - CEN AI DAM Editor",
    page_icon="🎨",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for Image Editor
st.markdown("""
<style>
    /* Hide default sidebar and multipage nav */
    [data-testid="stSidebar"] {
        display: none;
    }
    [data-testid="stSidebarNav"] {
        display: none;
    }

    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    /* Tool card styling */
    .tool-card {
        background: white;
        border: 2px solid #e0e0e0;
        border-radius: 12px;
        padding: 12px 8px;
        text-align: center;
        cursor: pointer;
        transition: all 0.2s;
        min-height: 80px;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
    }

    .tool-card:hover {
        border-color: #A23B72;
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(162, 59, 114, 0.15);
    }

    .tool-card.selected {
        border-color: #A23B72;
        background: linear-gradient(135deg, rgba(162, 59, 114, 0.1) 0%, rgba(139, 46, 95, 0.1) 100%);
    }

    .tool-icon {
        font-size: 28px;
        margin-bottom: 4px;
    }

    .tool-label {
        font-size: 12px;
        font-weight: 500;
        color: #273444;
    }

    /* History card styling */
    .history-card {
        background: white;
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 8px;
        margin-bottom: 12px;
        transition: all 0.2s;
    }

    .history-card:hover {
        border-color: #A23B72;
        box-shadow: 0 2px 8px rgba(162, 59, 114, 0.15);
    }

    .history-title {
        font-size: 13px;
        font-weight: 600;
        color: #273444;
        margin: 8px 0 4px 0;
    }

    .history-date {
        font-size: 11px;
        color: #718096;
    }

    /* Canvas placeholder */
    .canvas-placeholder {
        background: white;
        border: 2px dashed #a0aec0;
        border-radius: 12px;
        min-height: 500px;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        color: #4a5568;
    }

    /* Left menu styling */
    .left-menu-btn {
        background: #273444;
        color: white;
        border: none;
        border-radius: 8px;
        padding: 12px;
        margin-bottom: 8px;
        width: 100%;
        text-align: center;
        cursor: pointer;
    }
</style>
""", unsafe_allow_html=True)


def init_editor_state():
    """Initialize editor-specific session state."""
    init_session_state()

    if 'current_canvas_image' not in st.session_state:
        st.session_state.current_canvas_image = None

    if 'canvas_history' not in st.session_state:
        st.session_state.canvas_history = []  # List of dicts: {image, title, created_at}

    if 'reference_images' not in st.session_state:
        st.session_state.reference_images = []

    if 'current_tool' not in st.session_state:
        st.session_state.current_tool = 'brush'

    if 'stroke_width' not in st.session_state:
        st.session_state.stroke_width = 5

    if 'stroke_color' not in st.session_state:
        st.session_state.stroke_color = '#000000'

    if 'highlighter_opacity' not in st.session_state:
        st.session_state.highlighter_opacity = 0.4

    if 'reference_expanded' not in st.session_state:
        st.session_state.reference_expanded = True

    if 'current_project_path' not in st.session_state:
        st.session_state.current_project_path = None

    if 'current_project_name' not in st.session_state:
        st.session_state.current_project_name = None

    if 'history_counter' not in st.session_state:
        st.session_state.history_counter = 0

    if 'show_template_panel' not in st.session_state:
        st.session_state.show_template_panel = False

    if 'last_uploaded_file' not in st.session_state:
        st.session_state.last_uploaded_file = None


def add_to_history(image, title="AI 생성 이미지"):
    """Add an image to history with metadata."""
    st.session_state.history_counter += 1
    history_item = {
        'image': image.copy(),
        'title': f"{title} #{st.session_state.history_counter}",
        'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    st.session_state.canvas_history.append(history_item)


def get_templates():
    """Return template list matching home page."""
    return [
        {
            'icon': '📱',
            'title': 'SNS/마케팅 광고 소재',
            'desc': '브랜드 캠페인·프로모션 등 마케팅 목적의 SNS피드, 배너, 썸네일 등'
        },
        {
            'icon': '📸',
            'title': '스튜디오 촬영 이미지 생성',
            'desc': '패션, 화장품, 가구, 가전 등 고품질 촬영 연출 이미지'
        },
        {
            'icon': '🎨',
            'title': '스타일 기반 이미지 생성',
            'desc': '제품 배치, 공간 연출 등 실제 사용 환경 표현'
        },
        {
            'icon': '🌐',
            'title': '다국어 변환 이미지 생성',
            'desc': '콘텐츠를 여러 언어 이미지로 자동 변환'
        },
        {
            'icon': '📊',
            'title': '인포그래픽 이미지 생성',
            'desc': '제품 설명서, 홍보물, 분석 리포트 시각화'
        },
        {
            'icon': '🖼️',
            'title': '삽화 이미지 생성',
            'desc': '텍스트 기반 콘텐츠의 시각화 대표 이미지'
        },
        {
            'icon': '✏️',
            'title': '일러스트 이미지 완성',
            'desc': '스케치 기반으로 채색·완성된 일러스트 변환'
        },
    ]


def show_template_panel():
    """Show template selection panel."""
    st.markdown("#### 📋 템플릿 선택")
    st.caption("원하는 템플릿을 선택하세요")

    templates = get_templates()

    for template in templates:
        with st.container():
            if st.button(
                f"{template['icon']} {template['title']}",
                key=f"tpl_{template['title']}",
                use_container_width=True
            ):
                st.session_state.show_template_panel = False
                show_template_dialog(template['title'])

    st.markdown("---")
    if st.button("✖️ 닫기", key="close_template_panel", use_container_width=True):
        st.session_state.show_template_panel = False
        st.rerun()


def show_left_menu():
    """Render left menu panel."""
    st.markdown("#### 메뉴")

    # Template
    if st.button("📋 템플릿", key="menu_template", use_container_width=True):
        st.session_state.show_template_panel = not st.session_state.show_template_panel
        st.rerun()

    # New Project
    if st.button("➕ 새 프로젝트", key="menu_new", use_container_width=True):
        st.session_state.current_canvas_image = None
        st.session_state.canvas_history = []
        st.session_state.reference_images = []
        st.session_state.current_project_path = None
        st.session_state.current_project_name = None
        st.session_state.history_counter = 0
        st.success("새 프로젝트 생성됨")
        st.rerun()

    # Save Project
    if st.button("💾 저장", key="menu_save", use_container_width=True):
        if st.session_state.current_canvas_image is None:
            st.warning("저장할 내용이 없습니다")
        else:
            st.session_state.show_save_dialog = True
            st.rerun()

    # Load Project
    if st.button("📂 불러오기", key="menu_load", use_container_width=True):
        st.session_state.show_load_dialog = True
        st.rerun()

    # Upload
    uploaded = st.file_uploader(
        "이미지 업로드",
        type=['png', 'jpg', 'jpeg', 'webp'],
        key="menu_upload",
        label_visibility="collapsed"
    )

    if uploaded:
        # Check if this is a new file (not already processed)
        file_id = f"{uploaded.name}_{uploaded.size}"
        if st.session_state.last_uploaded_file != file_id:
            st.session_state.last_uploaded_file = file_id
            # Load directly from memory (faster than saving to disk first)
            image = Image.open(uploaded).convert("RGB")
            st.session_state.current_canvas_image = image
            add_to_history(image, "업로드 이미지")
            st.rerun()

    st.markdown("---")

    # Home
    if st.button("🏠 홈으로", key="menu_home", use_container_width=True):
        st.switch_page("app.py")


def show_tool_cards():
    """Render tool selection as cards."""
    st.markdown("#### 도구 선택")

    tools = [
        {"id": "brush", "icon": "✏️", "label": "브러쉬"},
        {"id": "highlighter", "icon": "🖍️", "label": "형광펜"},
        {"id": "eraser", "icon": "🧹", "label": "지우개"},
    ]

    cols = st.columns(len(tools))

    for idx, tool in enumerate(tools):
        with cols[idx]:
            is_selected = st.session_state.current_tool == tool["id"]

            if st.button(
                f"{tool['icon']}\n{tool['label']}",
                key=f"tool_{tool['id']}",
                use_container_width=True,
                type="primary" if is_selected else "secondary"
            ):
                st.session_state.current_tool = tool["id"]
                st.rerun()

    # Tool settings
    st.markdown("#### 도구 설정")

    col1, col2 = st.columns(2)

    with col1:
        st.session_state.stroke_width = st.slider(
            "굵기", 1, 50, st.session_state.stroke_width, key="stroke_slider"
        )

    with col2:
        if st.session_state.current_tool == "highlighter":
            st.session_state.highlighter_opacity = st.slider(
                "투명도", 0.1, 1.0, st.session_state.highlighter_opacity, key="opacity_slider"
            )
        elif st.session_state.current_tool != "eraser":
            st.session_state.stroke_color = st.color_picker(
                "색상", st.session_state.stroke_color, key="color_picker"
            )


def show_canvas():
    """Render main canvas area using streamlit-drawable-canvas."""

    if st.session_state.current_canvas_image is None:
        st.markdown("""
        <div class='canvas-placeholder'>
            <div style='font-size: 48px; margin-bottom: 16px;'>🖼️</div>
            <div style='font-size: 18px; font-weight: 600; margin-bottom: 8px;'>캔버스가 비어있습니다</div>
            <div style='font-size: 14px;'>좌측 메뉴에서 이미지를 업로드하세요</div>
        </div>
        """, unsafe_allow_html=True)
        return

    # Configure drawing based on selected tool
    current_tool = st.session_state.current_tool

    if current_tool == "eraser":
        drawing_mode = "freedraw"
        stroke_color = "#FFFFFF"
        stroke_width = st.session_state.stroke_width * 2
    elif current_tool == "highlighter":
        drawing_mode = "freedraw"
        # Convert hex to rgba with opacity
        hex_color = st.session_state.stroke_color
        r = int(hex_color[1:3], 16)
        g = int(hex_color[3:5], 16)
        b = int(hex_color[5:7], 16)
        opacity = st.session_state.highlighter_opacity
        stroke_color = f"rgba({r}, {g}, {b}, {opacity})"
        stroke_width = st.session_state.stroke_width * 2
    else:  # brush
        drawing_mode = "freedraw"
        stroke_color = st.session_state.stroke_color
        stroke_width = st.session_state.stroke_width

    # Get image dimensions
    img_width = st.session_state.current_canvas_image.width
    img_height = st.session_state.current_canvas_image.height

    # Scale if too large
    max_width = 800
    scale = min(1.0, max_width / img_width)
    display_width = int(img_width * scale)
    display_height = int(img_height * scale)

    # Canvas
    canvas_result = st_canvas(
        fill_color="rgba(255, 165, 0, 0.3)",
        stroke_width=stroke_width,
        stroke_color=stroke_color,
        background_image=st.session_state.current_canvas_image,
        update_streamlit=True,
        height=display_height,
        width=display_width,
        drawing_mode=drawing_mode,
        key="main_canvas",
    )

    # Quick actions
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if st.button("↩️ 실행취소", use_container_width=True):
            if len(st.session_state.canvas_history) > 1:
                st.session_state.canvas_history.pop()
                st.session_state.current_canvas_image = st.session_state.canvas_history[-1]['image'].copy()
                st.rerun()
            else:
                st.warning("더 이상 되돌릴 내역이 없습니다.")

    with col2:
        if st.button("💾 저장", use_container_width=True):
            workspace_dir = st.session_state.user['workspace_dir']
            save_dir = os.path.join(workspace_dir, 'generated')
            os.makedirs(save_dir, exist_ok=True)

            filename = f"canvas_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            filepath = os.path.join(save_dir, filename)

            st.session_state.current_canvas_image.save(filepath)
            st.success(f"저장 완료: {filename}")

    with col3:
        if st.button("🗑️ 초기화", use_container_width=True):
            st.session_state.current_canvas_image = None
            st.session_state.canvas_history = []
            st.session_state.history_counter = 0
            st.rerun()

    with col4:
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
    """Render right history panel with cards."""
    st.markdown("#### 📜 히스토리")

    if not st.session_state.canvas_history:
        st.info("히스토리가 비어있습니다.\n적용하기를 통해 이미지를 생성하세요.")
        return

    st.caption(f"총 {len(st.session_state.canvas_history)}개 항목")

    # Display history items (most recent first)
    for idx, hist_item in enumerate(reversed(st.session_state.canvas_history)):
        with st.container():
            # Image thumbnail
            st.image(hist_item['image'], use_container_width=True)

            # Card info
            st.markdown(f"""
            <div class="history-card">
                <div class="history-title">{hist_item['title']}</div>
                <div class="history-date">{hist_item['created_at']}</div>
            </div>
            """, unsafe_allow_html=True)

            if st.button("복원", key=f"restore_{idx}", use_container_width=True):
                st.session_state.current_canvas_image = hist_item['image'].copy()
                st.rerun()

        st.markdown("---")


def show_prompt_area():
    """Render prompt input and apply button."""
    st.markdown("---")
    st.markdown("#### 💬 AI 프롬프트")

    prompt = st.text_area(
        "프롬프트를 입력하세요",
        placeholder="예: 배경을 파란색으로 변경하세요",
        height=80,
        key="editor_prompt",
        label_visibility="collapsed"
    )

    if st.button("🚀 적용하기", type="primary", use_container_width=True, key="apply_prompt"):
        if not prompt:
            st.warning("프롬프트를 입력해주세요")
        elif st.session_state.current_canvas_image is None:
            st.warning("먼저 이미지를 업로드해주세요")
        else:
            with st.spinner("AI가 이미지를 생성하고 있습니다..."):
                try:
                    workspace_dir = st.session_state.user['workspace_dir']
                    generator = ImageGenerator(os.path.join(workspace_dir, 'generated'))

                    temp_path = os.path.join(workspace_dir, 'temp_canvas.png')
                    st.session_state.current_canvas_image.save(temp_path)

                    generated_paths = generator.change_attributes(
                        image_path=temp_path,
                        instructions=[prompt]
                    )

                    if generated_paths:
                        new_image = Image.open(generated_paths[0])
                        st.session_state.current_canvas_image = new_image

                        # Add to history with prompt as title
                        title = prompt[:20] + "..." if len(prompt) > 20 else prompt
                        add_to_history(new_image, title)

                        st.success("✅ 적용 완료!")
                        st.rerun()
                    else:
                        st.error("이미지 생성 실패")

                except Exception as e:
                    st.error(f"오류 발생: {str(e)}")


def show_reference_images():
    """Render reference images accordion."""
    with st.expander("📎 레퍼런스 이미지 (최대 2개)", expanded=st.session_state.reference_expanded):
        reference_uploads = st.file_uploader(
            "레퍼런스 이미지 업로드",
            type=['png', 'jpg', 'jpeg', 'webp'],
            accept_multiple_files=True,
            key="reference_upload",
            label_visibility="collapsed"
        )

        if reference_uploads:
            reference_uploads = reference_uploads[:2]
            st.session_state.reference_images = []

            cols = st.columns(2)
            for idx, ref_file in enumerate(reference_uploads):
                with cols[idx]:
                    image = Image.open(ref_file)
                    st.image(image, caption=f"레퍼런스 {idx+1}", use_container_width=True)
                    st.session_state.reference_images.append(image)


@st.dialog("💾 프로젝트 저장", width="large")
def show_save_project_dialog():
    """Show project save dialog."""
    st.markdown("### 프로젝트 저장")

    default_name = st.session_state.current_project_name or f"Project_{datetime.now().strftime('%Y%m%d')}"
    project_name = st.text_input(
        "프로젝트 이름",
        value=default_name,
        key="save_project_name"
    )

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

                # Extract images from history items
                history_images = [item['image'] for item in st.session_state.canvas_history]

                if st.session_state.current_project_path:
                    success = pm.update_project(
                        st.session_state.current_project_path,
                        canvas_image=st.session_state.current_canvas_image,
                        canvas_history=history_images,
                        reference_images=st.session_state.reference_images
                    )
                    if success:
                        st.success(f"✅ 프로젝트 '{project_name}'이(가) 업데이트되었습니다!")
                    else:
                        st.error("프로젝트 업데이트 실패")
                else:
                    project_path = pm.save_project(
                        project_name=project_name,
                        canvas_image=st.session_state.current_canvas_image,
                        canvas_history=history_images,
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
    projects = pm.list_projects()

    if not projects:
        st.info("저장된 프로젝트가 없습니다.")
        if st.button("닫기", use_container_width=True):
            st.session_state.show_load_dialog = False
            st.rerun()
        return

    st.caption(f"총 {len(projects)}개의 프로젝트")

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
                    project_data = pm.load_project(project['project_path'])

                    if project_data:
                        st.session_state.current_canvas_image = project_data['canvas_image']

                        # Convert old format to new format if needed
                        st.session_state.canvas_history = []
                        for i, img in enumerate(project_data['canvas_history']):
                            st.session_state.canvas_history.append({
                                'image': img,
                                'title': f"복원된 이미지 #{i+1}",
                                'created_at': project_data.get('modified_at', 'Unknown')
                            })

                        st.session_state.reference_images = project_data['reference_images']
                        st.session_state.current_project_path = project_data['project_path']
                        st.session_state.current_project_name = project_data['name']
                        st.session_state.history_counter = len(st.session_state.canvas_history)

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

    if st.button("닫기", use_container_width=True, key="load_close"):
        st.session_state.show_load_dialog = False
        st.rerun()


def main():
    """Main entry point for Image Editor page."""
    init_editor_state()

    # Show dialogs if requested
    if st.session_state.get('show_save_dialog', False):
        show_save_project_dialog()

    if st.session_state.get('show_load_dialog', False):
        show_load_project_dialog()

    # Show current project name
    if st.session_state.current_project_name:
        st.caption(f"📁 현재 프로젝트: {st.session_state.current_project_name}")

    # Main layout: Left Menu | Tools + Canvas | History
    # Adjust column ratio if template panel is open
    if st.session_state.show_template_panel:
        col_menu, col_template, col_main, col_history = st.columns([1, 1.5, 4, 2])
    else:
        col_menu, col_main, col_history = st.columns([1, 5, 2])
        col_template = None

    with col_menu:
        show_left_menu()

    if col_template:
        with col_template:
            show_template_panel()

    with col_main:
        show_tool_cards()
        st.markdown("---")
        show_canvas()
        show_prompt_area()
        show_reference_images()

    with col_history:
        show_history_panel()


if __name__ == "__main__":
    main()
