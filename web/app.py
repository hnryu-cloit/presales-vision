# -*- coding: utf-8 -*-
"""
CEN AI DAM Editor - Main Dashboard

This is the main entry point for the Streamlit web application.
Features:
- Project management (recent projects, create new)
- Template gallery (SNS/Marketing, Studio Shooting, etc.)
- Quick access to Image Editor and DAM System
"""

import streamlit as st
import os
import sys
from datetime import datetime
from typing import Dict

# Add core module to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import core modules
from core import ImageGenerator, ImageAnalyzer

# Import local utilities
from utils.session import init_session_state, get_user_workspace_dir
from utils.file_handler import save_uploaded_file, save_generated_images
from components.template_form import show_template_dialog

# Page configuration
st.set_page_config(
    page_title="CEN AI DAM Editor",
    page_icon="🎨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    /* Main colors */
    :root {
        --primary-color: #A23B72;
        --sidebar-bg: #273444;
        --main-bg: #f8f9fa;
    }

    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background-color: var(--sidebar-bg);
    }

    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    /* Template card styling */
    .template-card {
        background: white;
        border-radius: 12px;
        padding: 24px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        transition: transform 0.2s, box-shadow 0.2s;
        cursor: pointer;
        text-align: center;
        height: 220px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }

    .template-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 4px 16px rgba(162, 59, 114, 0.2);
    }

    .template-icon {
        font-size: 48px;
        margin-bottom: 16px;
    }

    .template-title {
        font-size: 18px;
        font-weight: 600;
        color: #273444;
        margin-bottom: 8px;
    }

    .template-desc {
        font-size: 13px;
        color: #666;
        line-height: 1.5;
    }

    /* Create Now button */
    .create-now-btn {
        background: linear-gradient(135deg, #A23B72 0%, #8B2E5F 100%);
        color: white;
        padding: 20px 48px;
        font-size: 24px;
        font-weight: 600;
        border-radius: 50px;
        border: none;
        cursor: pointer;
        box-shadow: 0 4px 12px rgba(162, 59, 114, 0.3);
        transition: all 0.3s;
    }

    .create-now-btn:hover {
        transform: scale(1.05);
        box-shadow: 0 6px 20px rgba(162, 59, 114, 0.4);
    }

    /* Recent project card */
    .project-card {
        background: white;
        border-radius: 8px;
        padding: 12px;
        margin-bottom: 12px;
        border: 1px solid #e0e0e0;
        cursor: pointer;
        transition: all 0.2s;
    }

    .project-card:hover {
        border-color: var(--primary-color);
        background: #fff5f9;
    }

    .project-title {
        font-size: 14px;
        font-weight: 600;
        color: #273444;
        margin-bottom: 4px;
    }

    .project-date {
        font-size: 12px;
        color: #999;
    }

    .link-button {
        background: none;
        border: none;
        padding: 0;
        color: black;
        text-decoration: none;
        cursor: pointer;
    }

    .link-button:hover {
        text-decoration: underline;
    }
</style>
""", unsafe_allow_html=True)


def init_session_state():
    """Initialize session state variables (imported from utils.session)."""
    from utils.session import init_session_state as init_sess
    init_sess()


def show_sidebar():
    """Render sidebar with recent projects."""
    with st.sidebar:
        # Logo
        st.markdown("### ITCEN CLOIT")
        st.markdown("---")

        # Recent projects
        st.markdown("### 📁 최근 프로젝트")

        for project in st.session_state.recent_projects:
            with st.container():
                st.markdown(f"""
                <div class="project-card">
                    <div class="project-title">{project['name']}</div>
                    <div class="project-date">{project['date']}</div>
                </div>
                """, unsafe_allow_html=True)
                if st.button("열기", key=f"open_{project['name']}", use_container_width=True):
                    st.info(f"'{project['name']}' 프로젝트 열기 (구현 예정)")

def show_header():
    """Render a header with account information and logout button."""
    if st.session_state.user['is_logged_in']:
        col1, col2 = st.columns([10, 2])
        with col1:
            st.empty()
        with col2:
            # Use columns to place buttons side-by-side
            c1, c2 = st.columns(2)
            with c1:
                if st.button(f"👤 {st.session_state.user['name']}", key="settings_button", use_container_width=True):
                    st.switch_page("pages/03_⚙️_Settings.py")
            with c2:
                if st.button("🚪 로그아웃", key="logout_button", use_container_width=True):
                    st.session_state.user['is_logged_in'] = False
                    st.rerun()
    else:
        _, col2 = st.columns([10, 2])
        with col2:
            if st.button("🔑 로그인", use_container_width=True):
                st.session_state.user['is_logged_in'] = True
                st.rerun()

def show_welcome_section():
    """Render welcome message and Create Now button."""
    st.markdown(f"""
    <div style='text-align: center; margin: 40px 0 60px 0;'>
        <h1 style='color: #273444; margin-bottom: 8px;'>{st.session_state.user['name']} 님, 안녕하세요.</h1>
        <p style='font-size: 18px; color: #666;'>무엇을 도와드릴까요?</p>
    </div>
    """, unsafe_allow_html=True)

    # Create Now button
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("🎨 Create Now", key="create_now", use_container_width=True, type="primary"):
            st.switch_page("pages/01_🎨_Image_Editor.py")


def show_template_gallery():
    """Render template card gallery."""
    st.markdown("---")
    st.markdown("### ⭐ 템플릿 즐겨찾기")

    templates = [
        {
            'icon': '📱',
            'title': 'SNS/마케팅 광고 소재',
            'desc': '브랜드 캠페인·프로모션 등 마케팅 목적의 SNS피드, 배너, 썸네일 등 즉시 활용 가능한 광고 소재 생성'
        },
        {
            'icon': '📸',
            'title': '스튜디오 촬영 이미지 생성',
            'desc': '패션, 화장품, 가구, 가전 등 제품군에 관계없이 고품질 촬영 연출 이미지 생성'
        },
        {
            'icon': '🎨',
            'title': '스타일 기반 이미지 생성',
            'desc': '제품 배치, 공간 연출 등 실제 사용 환경을 표현한 상세 이미지 생성'
        },
        {
            'icon': '🌐',
            'title': '다국어 변환 이미지 생성',
            'desc': '하나의 콘텐츠를 문맥에 맞는 여러 언어로의 이미지로 자동 변환'
        },
        {
            'icon': '📊',
            'title': '인포그래픽 이미지 생성',
            'desc': '제품 설명서, 홍보물, 분석 리포트 등 중요 정보를 시각화한 이미지 생성'
        },
        {
            'icon': '🖼️',
            'title': '삽화 이미지 생성',
            'desc': '뉴스, 웹소설 등 텍스트 기반 콘텐츠의 주제와 문맥을 시각화한 대표 이미지 생성'
        },
        {
            'icon': '✏️',
            'title': '일러스트 이미지 완성',
            'desc': '의상 디자이너, 웹툰 스케치 등의 이미지 기반으로 채색·완성된 일러스트로 변환'
        },
        {
            'icon': '➕',
            'title': '새 템플릿 추가',
            'desc': '사용자 정의 템플릿을 생성하여 자주 사용하는 워크플로우를 저장하세요'
        }
    ]

    # Create 4-column grid
    cols = st.columns(4)

    for idx, template in enumerate(templates):
        with cols[idx % 4]:
            st.markdown(f"""
            <div class="template-card">
                <div class="template-icon">{template['icon']}</div>
                <div class="template-title">{template['title']}</div>
                <div class="template-desc">{template['desc']}</div>
            </div>
            """, unsafe_allow_html=True)

            if st.button("선택", key=f"template_{idx}", use_container_width=True):
                # Show template dialog
                if template['title'] in [
                    'SNS/마케팅 광고 소재',
                    '스튜디오 촬영 이미지 생성',
                    '스타일 기반 이미지 생성',
                    '다국어 변환 이미지 생성',
                    '인포그래픽 이미지 생성',
                    '삽화 이미지 생성',
                    '일러스트 이미지 완성'
                ]:
                    form_data = show_template_dialog(template['title'])

                    if form_data:
                        # Process form and generate image
                        generate_image_from_template(form_data)
                else:
                    st.info(f"'{template['title']}' 템플릿 폼 구현 예정")


def generate_image_from_template(form_data: Dict):
    """Main application entry point."""
    init_session_state()

    # Show header with account info
    show_header()

    # Show sidebar
    show_sidebar()

    # Main content area
    show_welcome_section()
    show_template_gallery()

    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #999; font-size: 12px; padding: 20px 0;'>
        CEN AI DAM Editor v1.0.0 | Powered by Google Gemini AI | © 2025 ITCEN CLOIT
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    generate_image_from_template()