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

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.session import init_session_state
from components.template_form import show_template_dialog
from web.common.styles import load_app_styles

# Page configuration
st.set_page_config(
    page_title="AgentGo Creative",
    page_icon="🎨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
load_app_styles()

def show_sidebar():
    with st.sidebar:
        # Page navigation
        page_options = {
            "🏠 홈": "app.py",
            "🎨 Image Editor": "pages/01_Image_Editor.py",
            "📊 DAM System": "pages/02_DAM_System.py",
            "⚙️ Settings": "pages/03_Settings.py"
        }

        # Get the current script path to determine the active page
        try:
            # This works when the script is run directly
            current_script_path = os.path.basename(__file__)
        except NameError:
            # This is a fallback for Streamlit's execution environment
            current_script_path = os.path.basename(st.main.__file__)

        # Find the index of the current page
        page_titles = list(page_options.keys())
        current_page_index = 0  # Default to Home
        for i, path in enumerate(page_options.values()):
            if path.endswith(current_script_path):
                current_page_index = i
                break

        selected_page = st.radio(
            "메뉴",
            page_titles,
            index=current_page_index,
            key="sidebar_radio",
            label_visibility="collapsed"
        )
        st.sidebar.markdown("---")

        # Switch page if selection changes
        selected_page_path = page_options[selected_page]
        if not selected_page_path.endswith(current_script_path):
            st.switch_page(selected_page_path)

        # Recent projects
        st.markdown("### 최근 프로젝트")
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

        st.sidebar.markdown("---")

        # Copyright 정보
        st.sidebar.markdown("""
        <div style='text-align: center; font-size: 1rem; color: #888; padding: 0.5rem 0;'>
            Copyright © 2026<br>
            ITCEN CLOIT<br>
            All rights reserved.
        </div>
        """, unsafe_allow_html=True)


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
                    st.switch_page("pages/03_Settings.py")
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
        if st.button("🥰Create Now", key="create_now", use_container_width=True, type="primary"):
            st.switch_page("pages/01_Image_Editor.py")


def show_template_gallery():
    """Render template card gallery."""
    st.markdown("---")
    st.markdown("### 템플릿 즐겨찾기")

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
                    show_template_dialog(template['title'])
                else:
                    st.info(f"'{template['title']}' 템플릿 폼 구현 예정")


def main():
    """Main application entry point."""
    init_session_state()

    # Show header with account info
    show_header()

    # Show sidebar
    show_sidebar()

    # Main content area
    show_welcome_section()
    show_template_gallery()


if __name__ == "__main__":
    import sys
    from streamlit.web import cli as stcli

    if st.runtime.exists():
        main()
    else:
        sys.argv = ["streamlit", "run", sys.argv[0]]
        sys.exit(stcli.main())
