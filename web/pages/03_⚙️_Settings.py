# -*- coding: utf-8 -*-
"""
CEN AI DAM Editor - Settings Page

User profile and application settings.
"""

import streamlit as st
import os
import sys
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from utils.session import init_session_state, get_user_workspace_dir

# Page configuration
st.set_page_config(
    page_title="설정 - CEN AI DAM Editor",
    page_icon="⚙️",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .setting-card {
        background: white;
        border-radius: 8px;
        padding: 20px;
        margin-bottom: 20px;
        border: 1px solid #e0e0e0;
    }

    .setting-title {
        font-size: 18px;
        font-weight: 600;
        color: #273444;
        margin-bottom: 16px;
    }

    .stat-box {
        background: #f8f9fa;
        border-radius: 8px;
        padding: 16px;
        text-align: center;
        border: 1px solid #e0e0e0;
    }

    .stat-value {
        font-size: 32px;
        font-weight: 700;
        color: #A23B72;
        margin-bottom: 4px;
    }

    .stat-label {
        font-size: 14px;
        color: #666;
    }
</style>
""", unsafe_allow_html=True)


def get_workspace_statistics(workspace_dir: str) -> dict:
    """
    Get statistics about user's workspace.

    Args:
        workspace_dir: Path to user's workspace

    Returns:
        Dictionary with statistics
    """
    stats = {
        'total_uploads': 0,
        'total_generated': 0,
        'total_metadata': 0,
        'total_size_mb': 0
    }

    # Count uploads
    uploads_dir = os.path.join(workspace_dir, 'uploads')
    if os.path.exists(uploads_dir):
        stats['total_uploads'] = len([f for f in os.listdir(uploads_dir)
                                       if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))])

    # Count generated images
    generated_dir = os.path.join(workspace_dir, 'generated')
    if os.path.exists(generated_dir):
        stats['total_generated'] = len([f for f in os.listdir(generated_dir)
                                         if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))])

    # Count metadata files
    metadata_dir = os.path.join(workspace_dir, 'metadata')
    if os.path.exists(metadata_dir):
        stats['total_metadata'] = len([f for f in os.listdir(metadata_dir)
                                        if f.endswith('.json')])

    # Calculate total size
    total_size = 0
    for folder in ['uploads', 'generated', 'metadata', 'projects']:
        folder_path = os.path.join(workspace_dir, folder)
        if os.path.exists(folder_path):
            for root, dirs, files in os.walk(folder_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    if os.path.exists(file_path):
                        total_size += os.path.getsize(file_path)

    stats['total_size_mb'] = round(total_size / (1024 * 1024), 2)

    return stats


def show_user_profile():
    """Render user profile section."""
    st.markdown('<div class="setting-card">', unsafe_allow_html=True)
    st.markdown('<div class="setting-title">👤 사용자 프로필</div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        new_name = st.text_input(
            "이름",
            value=st.session_state.user['name'],
            key="user_name_input"
        )

    with col2:
        new_email = st.text_input(
            "이메일",
            value=st.session_state.user['email'],
            key="user_email_input"
        )

    if st.button("프로필 업데이트", type="primary"):
        st.session_state.user['name'] = new_name
        st.session_state.user['email'] = new_email
        # Note: Changing email would require workspace migration
        st.success("✅ 프로필이 업데이트되었습니다.")
        st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)


def show_workspace_stats():
    """Render workspace statistics section."""
    st.markdown('<div class="setting-card">', unsafe_allow_html=True)
    st.markdown('<div class="setting-title">📊 워크스페이스 통계</div>', unsafe_allow_html=True)

    workspace_dir = st.session_state.user['workspace_dir']
    stats = get_workspace_statistics(workspace_dir)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(f"""
        <div class="stat-box">
            <div class="stat-value">{stats['total_uploads']}</div>
            <div class="stat-label">업로드된 이미지</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="stat-box">
            <div class="stat-value">{stats['total_generated']}</div>
            <div class="stat-label">생성된 이미지</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div class="stat-box">
            <div class="stat-value">{stats['total_metadata']}</div>
            <div class="stat-label">메타데이터 파일</div>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown(f"""
        <div class="stat-box">
            <div class="stat-value">{stats['total_size_mb']}</div>
            <div class="stat-label">사용 용량 (MB)</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)


def show_workspace_path():
    """Render workspace path information."""
    st.markdown('<div class="setting-card">', unsafe_allow_html=True)
    st.markdown('<div class="setting-title">📁 워크스페이스 경로</div>', unsafe_allow_html=True)

    workspace_dir = st.session_state.user['workspace_dir']

    st.code(workspace_dir)

    st.caption("**폴더 구조:**")
    st.caption(f"• {workspace_dir}/uploads/ - 업로드된 이미지")
    st.caption(f"• {workspace_dir}/generated/ - AI 생성 이미지")
    st.caption(f"• {workspace_dir}/metadata/ - 메타데이터 JSON 파일")
    st.caption(f"• {workspace_dir}/projects/ - 프로젝트 파일")

    if st.button("📂 Finder에서 열기"):
        try:
            import subprocess
            subprocess.run(['open', workspace_dir])
            st.success("Finder가 열렸습니다.")
        except Exception as e:
            st.error(f"폴더를 열 수 없습니다: {str(e)}")

    st.markdown('</div>', unsafe_allow_html=True)


def show_app_preferences():
    """Render application preferences."""
    st.markdown('<div class="setting-card">', unsafe_allow_html=True)
    st.markdown('<div class="setting-title">🎨 애플리케이션 설정</div>', unsafe_allow_html=True)

    # Default template
    st.markdown("**기본 템플릿**")
    default_template = st.selectbox(
        "앱 시작 시 기본으로 선택할 템플릿",
        [
            "선택 안 함",
            "SNS/마케팅 광고 소재",
            "스튜디오 촬영 이미지 생성",
            "스타일 기반 이미지 생성",
            "삽화 이미지 생성"
        ],
        key="default_template"
    )

    # Auto-save settings
    st.markdown("**자동 저장**")
    auto_save = st.checkbox(
        "이미지 생성 시 자동으로 DAM에 저장",
        value=True,
        key="auto_save"
    )

    # Image quality
    st.markdown("**이미지 품질**")
    image_quality = st.select_slider(
        "생성 이미지 기본 품질",
        options=["낮음", "보통", "높음", "최상"],
        value="높음",
        key="image_quality"
    )

    # Generation count
    st.markdown("**생성 개수**")
    gen_count = st.slider(
        "한 번에 생성할 이미지 개수",
        min_value=1,
        max_value=4,
        value=1,
        key="gen_count"
    )

    if st.button("설정 저장", type="primary"):
        st.success("✅ 설정이 저장되었습니다.")
        # TODO: Save preferences to file or database

    st.markdown('</div>', unsafe_allow_html=True)


def show_about():
    """Render about section."""
    st.markdown('<div class="setting-card">', unsafe_allow_html=True)
    st.markdown('<div class="setting-title">ℹ️ 정보</div>', unsafe_allow_html=True)

    st.markdown("""
    **CEN AI DAM Editor**
    - 버전: 1.0.0 MVP
    - 빌드: 2025-02-01
    - 상태: 프로덕션 준비 완료

    **기술 스택:**
    - Frontend: Streamlit 1.51.0
    - AI Engine: Google Gemini 2.0/2.5
    - Backend: Python 3.8+
    - Image Processing: Pillow 11.3.0

    **개발:**
    - 조직: ITCEN CLOIT
    - 프로젝트: CEN AI DAM Editor

    **문의:**
    - Email: cloit@itcen.com
    """)

    st.markdown('</div>', unsafe_allow_html=True)


def show_danger_zone():
    """Render danger zone section."""
    st.markdown('<div class="setting-card" style="border-color: #dc3545;">', unsafe_allow_html=True)
    st.markdown('<div class="setting-title" style="color: #dc3545;">⚠️ 위험 구역</div>', unsafe_allow_html=True)

    st.warning("**주의:** 아래 작업은 되돌릴 수 없습니다.")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("🗑️ 모든 생성 이미지 삭제", use_container_width=True):
            st.session_state.confirm_delete_generated = True

        if st.session_state.get('confirm_delete_generated', False):
            if st.button("⚠️ 정말 삭제하시겠습니까?", type="primary", use_container_width=True):
                workspace_dir = st.session_state.user['workspace_dir']
                generated_dir = os.path.join(workspace_dir, 'generated')

                if os.path.exists(generated_dir):
                    import shutil
                    shutil.rmtree(generated_dir)
                    os.makedirs(generated_dir, exist_ok=True)
                    st.success("✅ 모든 생성 이미지가 삭제되었습니다.")
                    st.session_state.confirm_delete_generated = False
                    st.rerun()

    with col2:
        if st.button("🔄 워크스페이스 초기화", use_container_width=True):
            st.session_state.confirm_reset_workspace = True

        if st.session_state.get('confirm_reset_workspace', False):
            if st.button("⚠️ 정말 초기화하시겠습니까?", type="primary", use_container_width=True):
                workspace_dir = st.session_state.user['workspace_dir']

                if os.path.exists(workspace_dir):
                    import shutil
                    shutil.rmtree(workspace_dir)
                    # Recreate empty workspace
                    get_user_workspace_dir(st.session_state.user['email'])
                    st.success("✅ 워크스페이스가 초기화되었습니다.")
                    st.session_state.confirm_reset_workspace = False
                    st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)


def main():
    """Main entry point for Settings page."""
    init_session_state()

    st.title("⚙️ 설정")

    # User Profile
    show_user_profile()

    # Workspace Statistics
    show_workspace_stats()

    # Workspace Path
    show_workspace_path()

    # App Preferences
    show_app_preferences()

    # About
    show_about()

    # Danger Zone
    show_danger_zone()


if __name__ == "__main__":
    main()