# -*- coding: utf-8 -*-
"""
CEN AI DAM Editor - DAM System Page

Digital Asset Management System based on specification pages 11-13.

Features:
- Asset browsing (Grid/List/Column view modes)
- Advanced search and filtering
- Metadata management and viewing
- Asset upload and organization
- Batch operations (delete, move, tag)
- AI-powered metadata extraction
"""

import streamlit as st
import os
import sys
from PIL import Image
from datetime import datetime
from typing import List, Dict, Optional
import json

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from core import ImageAnalyzer
from utils.session import init_session_state
from utils.file_handler import save_uploaded_file, get_user_images

# Page configuration
st.set_page_config(
    page_title="DAM 시스템 - CEN AI DAM Editor",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    /* Asset card styling */
    .asset-card {
        background: white;
        border-radius: 8px;
        padding: 12px;
        border: 1px solid #e0e0e0;
        transition: all 0.2s;
        cursor: pointer;
    }

    .asset-card:hover {
        border-color: #A23B72;
        box-shadow: 0 4px 12px rgba(162, 59, 114, 0.15);
        transform: translateY(-2px);
    }

    .asset-selected {
        border-color: #A23B72;
        background: #fff5f9;
    }

    .asset-title {
        font-size: 14px;
        font-weight: 600;
        color: #273444;
        margin: 8px 0 4px 0;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }

    .asset-meta {
        font-size: 12px;
        color: #666;
        margin: 2px 0;
    }

    .tag-badge {
        display: inline-block;
        background: #f0f0f0;
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 11px;
        color: #666;
        margin: 2px;
    }

    /* View mode buttons */
    .view-mode-btn {
        padding: 8px 16px;
        border: 1px solid #ddd;
        background: white;
        cursor: pointer;
        transition: all 0.2s;
    }

    .view-mode-btn.active {
        background: #A23B72;
        color: white;
        border-color: #A23B72;
    }

    /* Metadata panel */
    .metadata-panel {
        background: white;
        border-radius: 8px;
        padding: 16px;
        border: 1px solid #e0e0e0;
    }

    .metadata-item {
        padding: 8px 0;
        border-bottom: 1px solid #f0f0f0;
    }

    .metadata-label {
        font-size: 12px;
        color: #999;
        margin-bottom: 4px;
    }

    .metadata-value {
        font-size: 14px;
        color: #273444;
        font-weight: 500;
    }
</style>
""", unsafe_allow_html=True)


def init_dam_state():
    """Initialize DAM-specific session state."""
    init_session_state()

    if 'dam_view_mode' not in st.session_state:
        st.session_state.dam_view_mode = 'grid'

    if 'selected_assets' not in st.session_state:
        st.session_state.selected_assets = []

    if 'current_folder' not in st.session_state:
        st.session_state.current_folder = 'all'

    if 'asset_metadata_cache' not in st.session_state:
        st.session_state.asset_metadata_cache = {}

    if 'batch_mode' not in st.session_state:
        st.session_state.batch_mode = False


def load_assets_from_workspace(workspace_dir: str, folder: str = 'all') -> List[Dict]:
    """
    Load assets from user workspace.

    Args:
        workspace_dir: User workspace directory
        folder: Folder to load from ('all', 'uploads', 'generated', etc.)

    Returns:
        List of asset dictionaries with metadata
    """
    assets = []

    # Determine which folders to scan
    if folder == 'all':
        folders_to_scan = ['uploads', 'generated']
    else:
        folders_to_scan = [folder]

    for folder_name in folders_to_scan:
        folder_path = os.path.join(workspace_dir, folder_name)

        if not os.path.exists(folder_path):
            continue

        # Scan for image files
        for filename in os.listdir(folder_path):
            if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
                file_path = os.path.join(folder_path, filename)

                # Get file stats
                stats = os.stat(file_path)
                created_time = datetime.fromtimestamp(stats.st_ctime)
                modified_time = datetime.fromtimestamp(stats.st_mtime)
                file_size = stats.st_size

                # Try to load metadata
                metadata_path = os.path.join(workspace_dir, 'metadata', f"{os.path.splitext(filename)[0]}.json")
                metadata = {}

                if os.path.exists(metadata_path):
                    try:
                        with open(metadata_path, 'r', encoding='utf-8') as f:
                            metadata = json.load(f)
                    except:
                        pass

                # Build asset info
                asset = {
                    'filename': filename,
                    'path': file_path,
                    'folder': folder_name,
                    'created': created_time,
                    'modified': modified_time,
                    'size': file_size,
                    'metadata': metadata,
                    'category': metadata.get('category', '미분류'),
                    'tags': metadata.get('tags', []),
                    'description': metadata.get('description', '')
                }

                assets.append(asset)

    return assets


def show_search_and_filters():
    """Render search bar and filter controls."""
    st.markdown("### 🔍 자산 검색 및 필터")

    col1, col2, col3, col4 = st.columns([3, 1, 1, 1])

    with col1:
        search_query = st.text_input(
            "검색",
            placeholder="제품명, 카테고리, 태그로 검색...",
            key="dam_search",
            label_visibility="collapsed"
        )

    with col2:
        folder_filter = st.selectbox(
            "폴더",
            ["all", "uploads", "generated"],
            format_func=lambda x: {"all": "전체", "uploads": "업로드", "generated": "생성됨"}[x],
            key="dam_folder_filter",
            label_visibility="collapsed"
        )
        st.session_state.current_folder = folder_filter

    with col3:
        category_filter = st.selectbox(
            "카테고리",
            ["전체", "가구", "가전", "화장품", "미분류"],
            key="dam_category_filter",
            label_visibility="collapsed"
        )

    with col4:
        sort_order = st.selectbox(
            "정렬",
            ["최근 수정", "최근 생성", "이름순", "크기순"],
            key="dam_sort",
            label_visibility="collapsed"
        )

    return search_query, folder_filter, category_filter, sort_order


def filter_assets(assets: List[Dict], search_query: str, category_filter: str, sort_order: str) -> List[Dict]:
    """
    Filter and sort assets based on search and filter criteria.

    Args:
        assets: List of asset dictionaries
        search_query: Search query string
        category_filter: Category filter
        sort_order: Sort order

    Returns:
        Filtered and sorted list of assets
    """
    filtered = assets

    # Apply search filter
    if search_query:
        query_lower = search_query.lower()
        filtered = [
            asset for asset in filtered
            if query_lower in asset['filename'].lower()
            or query_lower in asset['category'].lower()
            or any(query_lower in tag.lower() for tag in asset['tags'])
            or query_lower in asset['description'].lower()
        ]

    # Apply category filter
    if category_filter != "전체":
        filtered = [asset for asset in filtered if asset['category'] == category_filter]

    # Apply sorting
    if sort_order == "최근 수정":
        filtered.sort(key=lambda x: x['modified'], reverse=True)
    elif sort_order == "최근 생성":
        filtered.sort(key=lambda x: x['created'], reverse=True)
    elif sort_order == "이름순":
        filtered.sort(key=lambda x: x['filename'])
    elif sort_order == "크기순":
        filtered.sort(key=lambda x: x['size'], reverse=True)

    return filtered


def show_asset_grid(assets: List[Dict]):
    """Render assets in grid view."""
    if not assets:
        st.info("📭 자산이 없습니다. 이미지를 업로드하거나 생성해보세요.")
        return

    cols = st.columns(4)

    for idx, asset in enumerate(assets):
        with cols[idx % 4]:
            # Checkbox for batch selection (if batch mode enabled)
            if st.session_state.batch_mode:
                is_selected = asset['path'] in [a['path'] for a in st.session_state.selected_assets]
                if st.checkbox(
                    "선택",
                    value=is_selected,
                    key=f"select_grid_{idx}",
                    label_visibility="collapsed"
                ):
                    if not is_selected:
                        st.session_state.selected_assets.append(asset)
                else:
                    if is_selected:
                        st.session_state.selected_assets = [
                            a for a in st.session_state.selected_assets
                            if a['path'] != asset['path']
                        ]

            # Load and display image thumbnail
            try:
                image = Image.open(asset['path'])
                st.image(image, use_container_width=True)
            except:
                st.error("이미지 로드 실패")

            st.markdown(f"**{asset['filename']}**")
            st.caption(f"📁 {asset['folder']}")
            st.caption(f"📅 {asset['modified'].strftime('%Y-%m-%d %H:%M')}")
            st.caption(f"📦 {asset['size'] // 1024} KB")

            if asset['tags']:
                tags_html = ' '.join([f'<span class="tag-badge">{tag}</span>' for tag in asset['tags'][:3]])
                st.markdown(tags_html, unsafe_allow_html=True)

            col_btn1, col_btn2 = st.columns(2)

            with col_btn1:
                if st.button("👁️ 보기", key=f"view_{idx}", use_container_width=True):
                    st.session_state.selected_asset_for_preview = asset
                    st.rerun()

            with col_btn2:
                if st.button("📝 편집", key=f"edit_{idx}", use_container_width=True):
                    # Load to Image Editor
                    try:
                        image = Image.open(asset['path'])
                        st.session_state.current_canvas_image = image
                        st.session_state.canvas_history = [image.copy()]
                        st.session_state.reference_images = []
                        st.session_state.current_project_path = None
                        st.session_state.current_project_name = None
                        st.switch_page("pages/01_🎨_Image_Editor.py")
                    except Exception as e:
                        st.error(f"이미지 로드 실패: {str(e)}")


def show_asset_list(assets: List[Dict]):
    """Render assets in list view."""
    if not assets:
        st.info("📭 자산이 없습니다.")
        return

    for idx, asset in enumerate(assets):
        col_check, col_img, col_info, col_actions = st.columns([0.5, 1, 4, 2])

        # Checkbox for batch selection
        if st.session_state.batch_mode:
            with col_check:
                is_selected = asset['path'] in [a['path'] for a in st.session_state.selected_assets]
                if st.checkbox(
                    "",
                    value=is_selected,
                    key=f"select_list_{idx}"
                ):
                    if not is_selected:
                        st.session_state.selected_assets.append(asset)
                else:
                    if is_selected:
                        st.session_state.selected_assets = [
                            a for a in st.session_state.selected_assets
                            if a['path'] != asset['path']
                        ]

        with col_img:
            try:
                image = Image.open(asset['path'])
                st.image(image, use_container_width=True)
            except:
                st.error("로드 실패")

        with col_info:
            st.markdown(f"**{asset['filename']}**")
            st.caption(f"카테고리: {asset['category']} | 폴더: {asset['folder']}")
            st.caption(f"생성: {asset['created'].strftime('%Y-%m-%d')} | 수정: {asset['modified'].strftime('%Y-%m-%d %H:%M')}")

            if asset['description']:
                st.caption(f"설명: {asset['description'][:100]}...")

        with col_actions:
            st.markdown("<div style='margin-top: 20px;'></div>", unsafe_allow_html=True)

            if st.button("👁️ 미리보기", key=f"list_view_{idx}", use_container_width=True):
                st.session_state.selected_asset_for_preview = asset
                st.rerun()

            if st.button("📝 편집하기", key=f"list_edit_{idx}", use_container_width=True):
                # Load asset into Image Editor
                try:
                    image = Image.open(asset['path'])
                    st.session_state.current_canvas_image = image
                    st.session_state.canvas_history = [image.copy()]
                    st.session_state.reference_images = []
                    st.session_state.current_project_path = None
                    st.session_state.current_project_name = None
                    st.switch_page("pages/01_🎨_Image_Editor.py")
                except Exception as e:
                    st.error(f"이미지 로드 실패: {str(e)}")

        st.markdown("---")


def show_asset_column(assets: List[Dict]):
    """Render assets in column view (detailed table)."""
    if not assets:
        st.info("📭 자산이 없습니다.")
        return

    # Create table header
    if st.session_state.batch_mode:
        col0, col1, col2, col3, col4, col5, col6 = st.columns([0.5, 3, 2, 2, 2, 2, 2])
        with col0:
            st.markdown("**선택**")
    else:
        col1, col2, col3, col4, col5, col6 = st.columns([3, 2, 2, 2, 2, 2])

    with col1:
        st.markdown("**파일명**")
    with col2:
        st.markdown("**카테고리**")
    with col3:
        st.markdown("**폴더**")
    with col4:
        st.markdown("**크기**")
    with col5:
        st.markdown("**수정일**")
    with col6:
        st.markdown("**작업**")

    st.markdown("---")

    # Table rows
    for idx, asset in enumerate(assets):
        if st.session_state.batch_mode:
            col0, col1, col2, col3, col4, col5, col6 = st.columns([0.5, 3, 2, 2, 2, 2, 2])

            # Checkbox for batch selection
            with col0:
                is_selected = asset['path'] in [a['path'] for a in st.session_state.selected_assets]
                if st.checkbox(
                    "",
                    value=is_selected,
                    key=f"select_col_{idx}"
                ):
                    if not is_selected:
                        st.session_state.selected_assets.append(asset)
                else:
                    if is_selected:
                        st.session_state.selected_assets = [
                            a for a in st.session_state.selected_assets
                            if a['path'] != asset['path']
                        ]
        else:
            col1, col2, col3, col4, col5, col6 = st.columns([3, 2, 2, 2, 2, 2])

        with col1:
            st.text(asset['filename'][:30])
        with col2:
            st.text(asset['category'])
        with col3:
            st.text(asset['folder'])
        with col4:
            st.text(f"{asset['size'] // 1024} KB")
        with col5:
            st.text(asset['modified'].strftime('%Y-%m-%d'))
        with col6:
            if st.button("보기", key=f"col_view_{idx}"):
                st.session_state.selected_asset_for_preview = asset
                st.rerun()


def show_asset_preview_sidebar():
    """Show asset preview and metadata in sidebar."""
    if 'selected_asset_for_preview' not in st.session_state:
        return

    asset = st.session_state.selected_asset_for_preview

    with st.sidebar:
        st.markdown("### 📋 자산 상세 정보")

        # Close button
        if st.button("✖️ 닫기", use_container_width=True):
            del st.session_state.selected_asset_for_preview
            st.rerun()

        st.markdown("---")

        # Image preview
        try:
            image = Image.open(asset['path'])
            st.image(image, use_container_width=True)
        except:
            st.error("이미지 로드 실패")

        # Basic info
        st.markdown(f"**파일명:** {asset['filename']}")
        st.markdown(f"**카테고리:** {asset['category']}")
        st.markdown(f"**폴더:** {asset['folder']}")
        st.markdown(f"**크기:** {asset['size'] // 1024} KB")
        st.markdown(f"**생성일:** {asset['created'].strftime('%Y-%m-%d %H:%M')}")
        st.markdown(f"**수정일:** {asset['modified'].strftime('%Y-%m-%d %H:%M')}")

        # Tags
        if asset['tags']:
            st.markdown("**태그:**")
            tags_html = ' '.join([f'<span class="tag-badge">{tag}</span>' for tag in asset['tags']])
            st.markdown(tags_html, unsafe_allow_html=True)

        # Description
        if asset['description']:
            st.markdown("**설명:**")
            st.caption(asset['description'])

        # Metadata
        if asset['metadata']:
            with st.expander("📊 전체 메타데이터"):
                st.json(asset['metadata'])

        st.markdown("---")

        # Actions
        st.markdown("### 🎬 작업")

        if st.button("📝 이미지 에디터로 열기", use_container_width=True):
            # Load this asset into Image Editor
            try:
                image = Image.open(asset['path'])

                # Clear previous editor state and load new image
                st.session_state.current_canvas_image = image
                st.session_state.canvas_history = [image.copy()]
                st.session_state.reference_images = []
                st.session_state.current_project_path = None
                st.session_state.current_project_name = None

                st.success(f"✅ '{asset['filename']}'을(를) 이미지 에디터로 불러왔습니다!")
                st.switch_page("pages/01_🎨_Image_Editor.py")
            except Exception as e:
                st.error(f"이미지 로드 실패: {str(e)}")

        if st.button("🔄 메타데이터 재생성", use_container_width=True):
            with st.spinner("AI가 메타데이터를 분석하고 있습니다..."):
                try:
                    analyzer = ImageAnalyzer(st.session_state.user['workspace_dir'])
                    new_metadata = analyzer.analyze_image(asset['path'], save_metadata=True)

                    # Update asset metadata
                    asset['metadata'] = new_metadata
                    st.success("✅ 메타데이터 재생성 완료!")
                    st.rerun()
                except Exception as e:
                    st.error(f"메타데이터 생성 실패: {str(e)}")

        # Download
        with open(asset['path'], 'rb') as file:
            st.download_button(
                label="⬇️ 다운로드",
                data=file,
                file_name=asset['filename'],
                mime="image/png",
                use_container_width=True
            )


def batch_delete_assets(assets: List[Dict], workspace_dir: str) -> int:
    """
    Delete multiple assets.

    Args:
        assets: List of asset dictionaries to delete
        workspace_dir: User workspace directory

    Returns:
        Number of assets deleted
    """
    deleted_count = 0

    for asset in assets:
        try:
            # Delete image file
            if os.path.exists(asset['path']):
                os.remove(asset['path'])
                deleted_count += 1

            # Delete metadata file if exists
            metadata_path = os.path.join(
                workspace_dir,
                'metadata',
                f"{os.path.splitext(asset['filename'])[0]}.json"
            )
            if os.path.exists(metadata_path):
                os.remove(metadata_path)

        except Exception as e:
            print(f"Error deleting {asset['filename']}: {str(e)}")

    return deleted_count


def batch_add_tags(assets: List[Dict], tags: List[str], workspace_dir: str) -> int:
    """
    Add tags to multiple assets.

    Args:
        assets: List of asset dictionaries
        tags: List of tags to add
        workspace_dir: User workspace directory

    Returns:
        Number of assets updated
    """
    updated_count = 0

    for asset in assets:
        try:
            metadata_path = os.path.join(
                workspace_dir,
                'metadata',
                f"{os.path.splitext(asset['filename'])[0]}.json"
            )

            # Load or create metadata
            if os.path.exists(metadata_path):
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
            else:
                metadata = {'filename': asset['filename']}

            # Add new tags (avoid duplicates)
            existing_tags = set(metadata.get('tags', []))
            new_tags = existing_tags.union(set(tags))
            metadata['tags'] = list(new_tags)

            # Save metadata
            os.makedirs(os.path.dirname(metadata_path), exist_ok=True)
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)

            updated_count += 1

        except Exception as e:
            print(f"Error updating tags for {asset['filename']}: {str(e)}")

    return updated_count


def batch_move_assets(assets: List[Dict], target_folder: str, workspace_dir: str) -> int:
    """
    Move multiple assets to a different folder.

    Args:
        assets: List of asset dictionaries
        target_folder: Target folder name ('uploads' or 'generated')
        workspace_dir: User workspace directory

    Returns:
        Number of assets moved
    """
    moved_count = 0
    target_dir = os.path.join(workspace_dir, target_folder)
    os.makedirs(target_dir, exist_ok=True)

    for asset in assets:
        try:
            # Skip if already in target folder
            if asset['folder'] == target_folder:
                continue

            # Move image file
            new_path = os.path.join(target_dir, asset['filename'])

            # Handle duplicate filenames
            base, ext = os.path.splitext(asset['filename'])
            counter = 1
            while os.path.exists(new_path):
                new_filename = f"{base}_{counter}{ext}"
                new_path = os.path.join(target_dir, new_filename)
                counter += 1

            os.rename(asset['path'], new_path)
            moved_count += 1

        except Exception as e:
            print(f"Error moving {asset['filename']}: {str(e)}")

    return moved_count


def show_batch_operations_bar(selected_count: int, selected_assets: List[Dict], workspace_dir: str):
    """
    Show batch operations toolbar when assets are selected.

    Args:
        selected_count: Number of selected assets
        selected_assets: List of selected asset dictionaries
        workspace_dir: User workspace directory
    """
    if selected_count == 0:
        return

    st.markdown("---")
    st.markdown(f"### 🔧 배치 작업 ({selected_count}개 선택됨)")

    col1, col2, col3, col4, col5 = st.columns([2, 2, 2, 2, 2])

    with col1:
        if st.button("🗑️ 삭제", use_container_width=True, type="primary"):
            with st.spinner(f"{selected_count}개 자산 삭제 중..."):
                deleted = batch_delete_assets(selected_assets, workspace_dir)
                st.success(f"✅ {deleted}개 자산이 삭제되었습니다.")
                st.session_state.selected_assets = []
                st.rerun()

    with col2:
        with st.popover("🏷️ 태그 추가"):
            st.markdown("**태그 추가**")
            tag_input = st.text_input(
                "태그 입력 (쉼표로 구분)",
                placeholder="예: 제품, 마케팅, 2025",
                key="batch_tag_input"
            )

            if st.button("태그 추가 실행", key="batch_tag_confirm"):
                if tag_input:
                    tags = [tag.strip() for tag in tag_input.split(',') if tag.strip()]
                    if tags:
                        updated = batch_add_tags(selected_assets, tags, workspace_dir)
                        st.success(f"✅ {updated}개 자산에 태그가 추가되었습니다.")
                        st.session_state.selected_assets = []
                        st.rerun()

    with col3:
        with st.popover("📁 폴더 이동"):
            st.markdown("**폴더 이동**")
            target_folder = st.selectbox(
                "이동할 폴더",
                ["uploads", "generated"],
                key="batch_move_folder"
            )

            if st.button("이동 실행", key="batch_move_confirm"):
                moved = batch_move_assets(selected_assets, target_folder, workspace_dir)
                st.success(f"✅ {moved}개 자산이 {target_folder}로 이동되었습니다.")
                st.session_state.selected_assets = []
                st.rerun()

    with col4:
        if st.button("⬇️ 일괄 다운로드", use_container_width=True):
            st.info("일괄 다운로드 기능 (향후 구현)")

    with col5:
        if st.button("❌ 선택 해제", use_container_width=True):
            st.session_state.selected_assets = []
            st.rerun()

    st.markdown("---")


def show_upload_section():
    """Render asset upload section."""
    with st.expander("⬆️ 새 자산 업로드", expanded=False):
        st.markdown("이미지 파일을 업로드하여 DAM에 추가하세요.")

        uploaded_files = st.file_uploader(
            "이미지 업로드",
            type=['png', 'jpg', 'jpeg', 'webp'],
            accept_multiple_files=True,
            key="dam_upload",
            label_visibility="collapsed"
        )

        if uploaded_files:
            col1, col2 = st.columns([3, 1])

            with col1:
                st.success(f"{len(uploaded_files)}개 파일 선택됨")

            with col2:
                if st.button("업로드 완료", type="primary", use_container_width=True):
                    workspace_dir = st.session_state.user['workspace_dir']

                    with st.spinner("업로드 중..."):
                        for uploaded_file in uploaded_files:
                            # Save file
                            save_uploaded_file(uploaded_file, workspace_dir)

                            # Optionally generate metadata
                            # analyzer = ImageAnalyzer(workspace_dir)
                            # analyzer.analyze_image(saved_path, save_metadata=True)

                        st.success(f"✅ {len(uploaded_files)}개 파일 업로드 완료!")
                        st.rerun()


def main():
    """Main entry point for DAM System page."""
    init_dam_state()

    # Show asset preview sidebar if selected
    show_asset_preview_sidebar()

    # Header
    st.title("📦 디지털 자산 관리 (DAM)")

    # Upload section
    show_upload_section()

    st.markdown("---")

    # Search and filters
    search_query, folder_filter, category_filter, sort_order = show_search_and_filters()

    st.markdown("---")

    # View mode selector and batch mode toggle
    col_view1, col_view2, col_view3, col_spacer, col_batch = st.columns([1, 1, 1, 4, 2])

    with col_view1:
        if st.button("🔲 그리드", use_container_width=True, type="primary" if st.session_state.dam_view_mode == "grid" else "secondary"):
            st.session_state.dam_view_mode = "grid"
            st.rerun()

    with col_view2:
        if st.button("📋 리스트", use_container_width=True, type="primary" if st.session_state.dam_view_mode == "list" else "secondary"):
            st.session_state.dam_view_mode = "list"
            st.rerun()

    with col_view3:
        if st.button("📊 컬럼", use_container_width=True, type="primary" if st.session_state.dam_view_mode == "column" else "secondary"):
            st.session_state.dam_view_mode = "column"
            st.rerun()

    with col_batch:
        batch_label = "✅ 배치 모드" if st.session_state.batch_mode else "☑️ 배치 모드"
        if st.button(batch_label, use_container_width=True, type="primary" if st.session_state.batch_mode else "secondary"):
            st.session_state.batch_mode = not st.session_state.batch_mode
            if not st.session_state.batch_mode:
                st.session_state.selected_assets = []
            st.rerun()

    st.markdown("---")

    # Load assets from workspace
    workspace_dir = st.session_state.user['workspace_dir']
    assets = load_assets_from_workspace(workspace_dir, st.session_state.current_folder)

    # Apply filters
    filtered_assets = filter_assets(assets, search_query, category_filter, sort_order)

    # Show asset count
    st.caption(f"총 {len(filtered_assets)}개 자산")

    # Show batch operations bar if assets are selected
    if st.session_state.batch_mode and st.session_state.selected_assets:
        show_batch_operations_bar(
            len(st.session_state.selected_assets),
            st.session_state.selected_assets,
            workspace_dir
        )

    # Render assets based on view mode
    if st.session_state.dam_view_mode == "grid":
        show_asset_grid(filtered_assets)
    elif st.session_state.dam_view_mode == "list":
        show_asset_list(filtered_assets)
    elif st.session_state.dam_view_mode == "column":
        show_asset_column(filtered_assets)


if __name__ == "__main__":
    main()