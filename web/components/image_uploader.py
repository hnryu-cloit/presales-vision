# -*- coding: utf-8 -*-
"""
Image Uploader Widget

Reusable image upload component with preview.
"""

import streamlit as st
from typing import List, Optional
from PIL import Image


def image_uploader_widget(
    label: str = "이미지 업로드",
    multiple: bool = False,
    max_files: int = 5,
    key: str = "image_upload"
) -> Optional[List]:
    """
    Display image uploader with preview.

    Args:
        label: Label for the uploader
        multiple: Allow multiple file uploads
        max_files: Maximum number of files
        key: Unique key for the widget

    Returns:
        List of uploaded files or None
    """
    st.markdown(f"#### {label}")

    uploaded_files = st.file_uploader(
        label,
        type=['png', 'jpg', 'jpeg', 'webp'],
        accept_multiple_files=multiple,
        label_visibility="collapsed",
        key=key
    )

    # Show preview
    if uploaded_files:
        if isinstance(uploaded_files, list):
            # Multiple files
            cols = st.columns(min(len(uploaded_files), 4))
            for idx, file in enumerate(uploaded_files):
                with cols[idx % 4]:
                    image = Image.open(file)
                    st.image(image, caption=file.name, use_container_width=True)

        else:
            # Single file
            image = Image.open(uploaded_files)
            st.image(image, caption=uploaded_files.name, use_container_width=True)

    return uploaded_files