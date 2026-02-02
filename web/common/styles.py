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
    /* Main colors */
    :root {
        --primary-color: #A23B72;
        --sidebar-bg: #273444;
        --main-bg: #f8f9fa;
    }

    /* Apply main gradient background to the entire app view container */
    [data-testid="stAppViewContainer"] {
        background: radial-gradient(120% 100% at 50% -20%, rgba(86, 157, 255, 0.15) 0%, rgba(0, 85, 233, 0.08) 30%, rgba(0, 85, 233, 0) 60%), radial-gradient(80% 80% at 80% 80%, rgba(106, 20, 217, 0.12) 0%, rgba(0, 203, 200, 0.08) 40%, rgba(0, 203, 200, 0) 70%), linear-gradient(180deg, #FFFFFF 0%, rgba(240, 245, 255, 0.6) 25%, rgba(227, 238, 255, 0.7) 50%, rgba(217, 230, 255, 0.5) 75%, #FFFFFF 100%);
    }

    /* Main content area should have no background so the stAppViewContainer background shows through */
    [data-testid="stAppViewContainer"] > .main {
        background-color: transparent; /* Ensure no opaque background */
        padding-top: 72px; /* Add padding to push content below the new header */
    }

    /* New Header Style */
    [data-testid="stAppViewContainer"] > .main > [data-testid="stBlock"]:first-child {
        display: flex;
        flex-direction: row;
        justify-content: space-between;
        align-items: center;
        padding: 24px 32px 25px;
        position: absolute;
        width: 100%; /* Use 100% for responsiveness */
        height: 72px;
        right: 0px;
        top: 0px;
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(10px);
        z-index: 100; /* High z-index to stay on top */
    }

    /* New Sidebar Style */
    [data-testid="stSidebar"] {
        display: flex;
        flex-direction: column;
        align-items: flex-start;
        padding: 0px;
        position: absolute;
        width: 280px;
        height: calc(100vh - 72px); /* Full height minus header */
        left: 0px;
        top: 72px;
        overflow-y: auto; /* Changed to auto for vertical scrolling */
        overflow-x: hidden;
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(10px);
        border: none; /* Override default border */
        color: #000; /* Default text color for light background */
    }

    /* Sidebar Text Coloring */
    [data-testid="stSidebar"] h3 { /* Main Text: "최근 프로젝트" */
        color: #0950E8;
    }

    /* Adjust radio button styling for new sidebar background (Main Text) */
    [data-testid="stSidebar"] .st-emotion-cache-1gwan56 { /* Selector for radio button labels */
        color: #0950E8;
    }

    [data-testid="stSidebar"] .project-title { /* Main Text: Project names */
        color: #0950E8;
    }

    [data-testid="stSidebar"] .project-date { /* Sub Text: Project dates */
        color: #5F1BDB;
    }

    /* Sub Text: Copyright information */
    [data-testid="stSidebar"] > div > div:nth-last-child(1) > div > div > div[data-testid="stMarkdownContainer"] {
        color: #5F1BDB;
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
        color: #273444;
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
        border: 2px dashed #ccc;
        border-radius: 12px;
        min-height: 500px;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        color: #999;
    }
</style>
""", unsafe_allow_html=True)