# -*- coding: utf-8 -*-
"""
CEN AI DAM Editor - CSS Styles

This module contains functions that return CSS style strings for different Streamlit pages.
"""

import streamlit as st

def load_app_styles():
    """Loads the CSS for the main application (app.py)."""
    st.markdown("""
<style>
    /* Main colors - 통일된 색상 체계 */
    :root {
        --primary-color: #A23B72;
        --primary-dark: #8B2E5F;
        --sidebar-bg: #273444;
        --main-bg: #f8f9fa;

        /* 텍스트 색상 - 시인성 개선 */
        --text-primary: #1a202c;      /* 주요 텍스트 - 진한 검정 */
        --text-secondary: #2d3748;    /* 보조 텍스트 - 어두운 회색 */
        --text-tertiary: #4a5568;     /* 부가 텍스트 - 중간 회색 */
        --text-caption: #5a6878;      /* 캡션/날짜 - 밝은 회색 (충분한 대비) */
        --text-muted: #718096;        /* 약한 텍스트 - 최소 대비 보장 */
    }

    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    /* Hide default multipage navigation */
    [data-testid="stSidebarNav"] {
        display: none;
    }

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
        color: var(--text-primary);
        margin-bottom: 8px;
    }

    .template-desc {
        font-size: 13px;
        color: var(--text-tertiary);
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
    }

    .project-card:hover {
        border-color: var(--primary-color);
        background: #fff5f9;
    }

    .project-title {
        font-size: 14px;
        font-weight: 600;
        color: var(--text-primary);
        margin-bottom: 4px;
    }

    .project-date {
        font-size: 12px;
        color: var(--text-caption);
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


def load_editor_styles():
    """Loads the CSS for the Image Editor page."""
    st.markdown("""
<style>
    /* Hide default sidebar */
    [data-testid="stSidebar"] {
        display: none;
    }

    /* Main layout */
    .main-container {
        display: flex;
        height: 100vh;
    }

    /* Left menu panel */
    .left-menu {
        width: 80px;
        background: #273444;
        padding: 20px 10px;
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 20px;
    }

    .menu-item {
        color: white;
        text-align: center;
        cursor: pointer;
        padding: 10px;
        border-radius: 8px;
        transition: background 0.2s;
        width: 60px;
    }

    .menu-item:hover {
        background: rgba(255,255,255,0.1);
    }

    .menu-icon {
        font-size: 24px;
        margin-bottom: 4px;
    }

    .menu-label {
        font-size: 10px;
    }

    /* Canvas area */
    .canvas-container {
        flex: 1;
        background: #f8f9fa;
        padding: 20px;
        overflow: auto;
    }

    /* Toolbar */
    .toolbar {
        background: white;
        padding: 12px 20px;
        border-radius: 40px;
        display: flex;
        gap: 8px;
        align-items: center;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        margin-bottom: 20px;
        width: fit-content;
    }

    .tool-btn {
        width: 40px;
        height: 40px;
        border-radius: 50%;
        border: none;
        background: #f5f5f5;
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
        transition: all 0.2s;
    }

    .tool-btn:hover {
        background: #e0e0e0;
    }

    .tool-btn.active {
        background: #A23B72;
        color: white;
    }

    /* History panel */
    .history-panel {
        width: 280px;
        background: white;
        padding: 20px;
        border-left: 1px solid #e0e0e0;
        overflow-y: auto;
    }

    .history-title {
        font-size: 16px;
        font-weight: 600;
        margin-bottom: 16px;
        color: var(--text-primary, #1a202c);
    }

    .history-item {
        background: #f8f9fa;
        border-radius: 8px;
        padding: 8px;
        margin-bottom: 12px;
        cursor: pointer;
        transition: all 0.2s;
    }

    .history-item:hover {
        background: #e9ecef;
        transform: scale(1.02);
    }

    /* Prompt area */
    .prompt-area {
        background: white;
        padding: 16px 20px;
        border-top: 1px solid #e0e0e0;
        display: flex;
        gap: 12px;
        align-items: center;
    }

    /* Reference images section */
    .reference-section {
        background: white;
        border-radius: 8px;
        padding: 16px;
        margin-top: 16px;
    }

    .reference-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        cursor: pointer;
        padding: 8px;
        border-radius: 4px;
    }

    .reference-header:hover {
        background: #f8f9fa;
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
        color: var(--text-tertiary, #4a5568);
    }
</style>
""", unsafe_allow_html=True)