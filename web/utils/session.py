# -*- coding: utf-8 -*-
"""
Session State Management

Initialize and manage Streamlit session state variables.
"""

import streamlit as st
import os
from datetime import datetime


def init_session_state():
    """
    Initialize all session state variables.

    This should be called at the beginning of each page.
    """
    # User information
    if 'user' not in st.session_state:
        st.session_state.user = {
            'name': '클로잇',
            'email': 'cloit@itcen.com',
            'is_logged_in': True,
            'workspace_dir': get_user_workspace_dir('cloit@itcen.com')
        }

    # Recent projects
    if 'recent_projects' not in st.session_state:
        st.session_state.recent_projects = []

    # Current project
    if 'current_project' not in st.session_state:
        st.session_state.current_project = None

    # Image generation history
    if 'generation_history' not in st.session_state:
        st.session_state.generation_history = []

    # Image analysis results
    if 'analysis_results' not in st.session_state:
        st.session_state.analysis_results = {}

    # Selected template
    if 'selected_template' not in st.session_state:
        st.session_state.selected_template = None

    # Uploaded images
    if 'uploaded_images' not in st.session_state:
        st.session_state.uploaded_images = []

    # Generated images
    if 'generated_images' not in st.session_state:
        st.session_state.generated_images = []


def get_user_workspace_dir(user_email: str) -> str:
    """
    Get user's workspace directory path.

    Args:
        user_email: User's email address

    Returns:
        Path to user's workspace directory
    """
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    workspace_dir = os.path.join(base_dir, 'workspace', user_email.split('@')[0])

    # Create directories if they don't exist
    os.makedirs(os.path.join(workspace_dir, 'uploads'), exist_ok=True)
    os.makedirs(os.path.join(workspace_dir, 'generated'), exist_ok=True)
    os.makedirs(os.path.join(workspace_dir, 'metadata'), exist_ok=True)
    os.makedirs(os.path.join(workspace_dir, 'projects'), exist_ok=True)

    return workspace_dir


def create_new_project(project_name: str) -> dict:
    """
    Create a new project.

    Args:
        project_name: Name of the project

    Returns:
        Project dictionary
    """
    project = {
        'name': project_name,
        'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'modified_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'images': [],
        'metadata': {}
    }

    st.session_state.current_project = project
    st.session_state.recent_projects.insert(0, project)

    return project


def update_project():
    """Update current project's modified timestamp."""
    if st.session_state.current_project:
        st.session_state.current_project['modified_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')