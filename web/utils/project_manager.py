# -*- coding: utf-8 -*-
"""
Project Manager

Handle saving and loading of editor projects.
"""

import os
import json
from datetime import datetime
from typing import Dict, List, Optional
from PIL import Image
import base64
import io


class ProjectManager:
    """Manage project saving, loading, and listing."""

    def __init__(self, workspace_dir: str):
        """
        Initialize project manager.

        Args:
            workspace_dir: Path to user's workspace directory
        """
        self.workspace_dir = workspace_dir
        self.projects_dir = os.path.join(workspace_dir, 'projects')
        os.makedirs(self.projects_dir, exist_ok=True)

    def save_project(
        self,
        project_name: str,
        canvas_image: Image.Image,
        canvas_history: List[Image.Image],
        reference_images: List[Image.Image],
        metadata: Optional[Dict] = None
    ) -> str:
        """
        Save current editor state as a project.

        Args:
            project_name: Name of the project
            canvas_image: Current canvas image
            canvas_history: List of canvas history images
            reference_images: List of reference images
            metadata: Additional metadata

        Returns:
            Path to saved project file
        """
        # Create project directory
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = "".join(c for c in project_name if c.isalnum() or c in (' ', '-', '_')).strip()
        project_dir = os.path.join(self.projects_dir, f"{safe_name}_{timestamp}")
        os.makedirs(project_dir, exist_ok=True)

        # Save canvas image
        canvas_path = os.path.join(project_dir, 'canvas.png')
        if canvas_image:
            canvas_image.save(canvas_path)

        # Save canvas history
        history_dir = os.path.join(project_dir, 'history')
        os.makedirs(history_dir, exist_ok=True)
        history_paths = []

        for idx, hist_img in enumerate(canvas_history):
            hist_path = os.path.join(history_dir, f'history_{idx:03d}.png')
            hist_img.save(hist_path)
            history_paths.append(f'history_{idx:03d}.png')

        # Save reference images
        reference_dir = os.path.join(project_dir, 'references')
        os.makedirs(reference_dir, exist_ok=True)
        reference_paths = []

        for idx, ref_img in enumerate(reference_images):
            ref_path = os.path.join(reference_dir, f'reference_{idx:03d}.png')
            ref_img.save(ref_path)
            reference_paths.append(f'reference_{idx:03d}.png')

        # Create project metadata
        project_data = {
            'name': project_name,
            'created_at': timestamp,
            'modified_at': timestamp,
            'canvas_image': 'canvas.png' if canvas_image else None,
            'history_images': history_paths,
            'reference_images': reference_paths,
            'metadata': metadata or {}
        }

        # Save project file
        project_file = os.path.join(project_dir, 'project.json')
        with open(project_file, 'w', encoding='utf-8') as f:
            json.dump(project_data, f, ensure_ascii=False, indent=2)

        return project_file

    def load_project(self, project_path: str) -> Optional[Dict]:
        """
        Load a project from file.

        Args:
            project_path: Path to project.json file

        Returns:
            Dictionary with project data including loaded images
        """
        try:
            # Load project metadata
            with open(project_path, 'r', encoding='utf-8') as f:
                project_data = json.load(f)

            project_dir = os.path.dirname(project_path)

            # Load canvas image
            canvas_image = None
            if project_data.get('canvas_image'):
                canvas_path = os.path.join(project_dir, project_data['canvas_image'])
                if os.path.exists(canvas_path):
                    canvas_image = Image.open(canvas_path)

            # Load history images
            canvas_history = []
            for hist_filename in project_data.get('history_images', []):
                hist_path = os.path.join(project_dir, 'history', hist_filename)
                if os.path.exists(hist_path):
                    canvas_history.append(Image.open(hist_path))

            # Load reference images
            reference_images = []
            for ref_filename in project_data.get('reference_images', []):
                ref_path = os.path.join(project_dir, 'references', ref_filename)
                if os.path.exists(ref_path):
                    reference_images.append(Image.open(ref_path))

            return {
                'name': project_data.get('name', 'Untitled'),
                'created_at': project_data.get('created_at'),
                'modified_at': project_data.get('modified_at'),
                'canvas_image': canvas_image,
                'canvas_history': canvas_history,
                'reference_images': reference_images,
                'metadata': project_data.get('metadata', {}),
                'project_path': project_path
            }

        except Exception as e:
            print(f"Error loading project: {str(e)}")
            return None

    def list_projects(self) -> List[Dict]:
        """
        List all projects in workspace.

        Returns:
            List of project info dictionaries
        """
        projects = []

        if not os.path.exists(self.projects_dir):
            return projects

        for item in os.listdir(self.projects_dir):
            item_path = os.path.join(self.projects_dir, item)

            if os.path.isdir(item_path):
                project_file = os.path.join(item_path, 'project.json')

                if os.path.exists(project_file):
                    try:
                        with open(project_file, 'r', encoding='utf-8') as f:
                            project_data = json.load(f)

                        # Get thumbnail (canvas image)
                        thumbnail = None
                        if project_data.get('canvas_image'):
                            canvas_path = os.path.join(item_path, project_data['canvas_image'])
                            if os.path.exists(canvas_path):
                                thumbnail = canvas_path

                        projects.append({
                            'name': project_data.get('name', 'Untitled'),
                            'created_at': project_data.get('created_at'),
                            'modified_at': project_data.get('modified_at'),
                            'project_path': project_file,
                            'thumbnail': thumbnail,
                            'folder_name': item
                        })

                    except Exception as e:
                        print(f"Error reading project {item}: {str(e)}")

        # Sort by modified date (newest first)
        projects.sort(key=lambda x: x.get('modified_at', ''), reverse=True)

        return projects

    def delete_project(self, project_path: str) -> bool:
        """
        Delete a project.

        Args:
            project_path: Path to project.json file

        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            project_dir = os.path.dirname(project_path)

            if os.path.exists(project_dir):
                import shutil
                shutil.rmtree(project_dir)
                return True

        except Exception as e:
            print(f"Error deleting project: {str(e)}")

        return False

    def update_project(
        self,
        project_path: str,
        canvas_image: Optional[Image.Image] = None,
        canvas_history: Optional[List[Image.Image]] = None,
        reference_images: Optional[List[Image.Image]] = None,
        metadata: Optional[Dict] = None
    ) -> bool:
        """
        Update an existing project.

        Args:
            project_path: Path to project.json file
            canvas_image: Updated canvas image
            canvas_history: Updated canvas history
            reference_images: Updated reference images
            metadata: Updated metadata

        Returns:
            True if updated successfully, False otherwise
        """
        try:
            # Load existing project data
            with open(project_path, 'r', encoding='utf-8') as f:
                project_data = json.load(f)

            project_dir = os.path.dirname(project_path)

            # Update canvas image if provided
            if canvas_image:
                canvas_path = os.path.join(project_dir, 'canvas.png')
                canvas_image.save(canvas_path)

            # Update history if provided
            if canvas_history is not None:
                history_dir = os.path.join(project_dir, 'history')

                # Clear old history
                if os.path.exists(history_dir):
                    import shutil
                    shutil.rmtree(history_dir)

                os.makedirs(history_dir, exist_ok=True)
                history_paths = []

                for idx, hist_img in enumerate(canvas_history):
                    hist_path = os.path.join(history_dir, f'history_{idx:03d}.png')
                    hist_img.save(hist_path)
                    history_paths.append(f'history_{idx:03d}.png')

                project_data['history_images'] = history_paths

            # Update reference images if provided
            if reference_images is not None:
                reference_dir = os.path.join(project_dir, 'references')

                # Clear old references
                if os.path.exists(reference_dir):
                    import shutil
                    shutil.rmtree(reference_dir)

                os.makedirs(reference_dir, exist_ok=True)
                reference_paths = []

                for idx, ref_img in enumerate(reference_images):
                    ref_path = os.path.join(reference_dir, f'reference_{idx:03d}.png')
                    ref_img.save(ref_path)
                    reference_paths.append(f'reference_{idx:03d}.png')

                project_data['reference_images'] = reference_paths

            # Update metadata if provided
            if metadata is not None:
                project_data['metadata'].update(metadata)

            # Update modified timestamp
            project_data['modified_at'] = datetime.now().strftime("%Y%m%d_%H%M%S")

            # Save updated project file
            with open(project_path, 'w', encoding='utf-8') as f:
                json.dump(project_data, f, ensure_ascii=False, indent=2)

            return True

        except Exception as e:
            print(f"Error updating project: {str(e)}")
            return False

    def export_project(self, project_path: str, export_path: str) -> bool:
        """
        Export project as ZIP file.

        Args:
            project_path: Path to project.json file
            export_path: Path to save ZIP file

        Returns:
            True if exported successfully, False otherwise
        """
        try:
            import shutil

            project_dir = os.path.dirname(project_path)
            shutil.make_archive(
                export_path.replace('.zip', ''),
                'zip',
                project_dir
            )

            return True

        except Exception as e:
            print(f"Error exporting project: {str(e)}")
            return False