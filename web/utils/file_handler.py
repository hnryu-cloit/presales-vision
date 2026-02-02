# -*- coding: utf-8 -*-
"""
File Handling Utilities

Functions for uploading, saving, and loading images.
"""

import os
from datetime import datetime
from typing import Optional, List
from PIL import Image
import streamlit as st

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from core.logger import get_logger


def save_uploaded_file(uploaded_file, workspace_dir: str) -> str:
    """
    Save uploaded file to workspace directory.

    Args:
        uploaded_file: Streamlit UploadedFile object
        workspace_dir: User's workspace directory path

    Returns:
        Path to saved file
    """
    upload_dir = os.path.join(workspace_dir, 'uploads')
    os.makedirs(upload_dir, exist_ok=True)

    # Generate unique filename with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"{timestamp}_{uploaded_file.name}"
    filepath = os.path.join(upload_dir, filename)

    # Save file
    with open(filepath, 'wb') as f:
        f.write(uploaded_file.getbuffer())

    return filepath


def save_uploaded_files(uploaded_files: List, workspace_dir: str) -> List[str]:
    """
    Save multiple uploaded files.

    Args:
        uploaded_files: List of Streamlit UploadedFile objects
        workspace_dir: User's workspace directory path

    Returns:
        List of paths to saved files
    """
    saved_paths = []
    for uploaded_file in uploaded_files:
        filepath = save_uploaded_file(uploaded_file, workspace_dir)
        saved_paths.append(filepath)

    return saved_paths


def load_image_as_pil(filepath: str) -> Optional[Image.Image]:
    """
    Load image file as PIL Image object.

    Args:
        filepath: Path to image file

    Returns:
        PIL Image object or None if failed
    """
    try:
        return Image.open(filepath)
    except Exception as e:
        st.error(f"이미지 로딩 실패: {e}")
        return None


def save_generated_image(image_data, workspace_dir: str, prefix: str = "generated") -> str:
    """
    Save AI-generated image data to file.

    Args:
        image_data: Image data from Gemini API (bytes or inline_data object)
        workspace_dir: User's workspace directory path
        prefix: Filename prefix

    Returns:
        Path to saved image file
    """
    generated_dir = os.path.join(workspace_dir, 'generated')
    os.makedirs(generated_dir, exist_ok=True)

    # Generate unique filename
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
    filename = f"{prefix}_{timestamp}.png"
    filepath = os.path.join(generated_dir, filename)

    # Extract bytes from image_data
    if hasattr(image_data, 'data'):
        image_bytes = image_data.data
    else:
        image_bytes = image_data

    # Save file
    with open(filepath, 'wb') as f:
        f.write(image_bytes)

    return filepath


def save_generated_images(image_data_list: List, workspace_dir: str, prefix: str = "generated") -> List[str]:
    """
    Save multiple AI-generated images.

    Args:
        image_data_list: List of image data from Gemini API
        workspace_dir: User's workspace directory path
        prefix: Filename prefix

    Returns:
        List of paths to saved image files
    """
    saved_paths = []
    for idx, image_data in enumerate(image_data_list):
        filepath = save_generated_image(image_data, workspace_dir, f"{prefix}_{idx+1}")
        saved_paths.append(filepath)

    return saved_paths


def get_user_images(workspace_dir: str, folder: str = 'generated') -> List[str]:
    """
    Get list of image files in user's workspace.

    Args:
        workspace_dir: User's workspace directory path
        folder: Folder name ('generated', 'uploads', etc.)

    Returns:
        List of image file paths
    """
    dir_path = os.path.join(workspace_dir, folder)

    if not os.path.exists(dir_path):
        return []

    image_extensions = {'.png', '.jpg', '.jpeg', '.webp', '.gif'}
    image_files = []

    for filename in os.listdir(dir_path):
        if any(filename.lower().endswith(ext) for ext in image_extensions):
            filepath = os.path.join(dir_path, filename)
            image_files.append(filepath)

    # Sort by modification time (newest first)
    image_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)

    return image_files


def cleanup_old_files(workspace_dir: str, folder: str = 'uploads', max_age_days: int = 30):
    """
    Clean up old files from workspace directory.

    Args:
        workspace_dir: User's workspace directory path
        folder: Folder name to clean
        max_age_days: Maximum age of files to keep (in days)
    """
    dir_path = os.path.join(workspace_dir, folder)

    if not os.path.exists(dir_path):
        return

    import time
    current_time = time.time()
    max_age_seconds = max_age_days * 24 * 60 * 60

    for filename in os.listdir(dir_path):
        filepath = os.path.join(dir_path, filename)
        file_age = current_time - os.path.getmtime(filepath)

        if file_age > max_age_seconds:
            logger = get_logger()
            try:
                os.remove(filepath)
                logger.info(f"Deleted old file: {filename}")
            except Exception as e:
                logger.error(f"Failed to delete {filename}: {e}")