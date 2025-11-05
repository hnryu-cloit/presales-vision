# -*- coding: utf-8 -*-
"""
애플리케이션 및 프로젝트의 모든 경로를 관리하는 중앙 클래스입니다.
이 클래스는 싱글톤으로 구현되어 애플리케이션 전체에서 단일 인스턴스를 공유합니다.

주요 기능:
- 애플리케이션의 주요 디렉토리(data, output) 경로 관리
- 현재 활성화된 프로젝트의 루트 디렉토리 및 하위 디렉토리 경로 관리
- __init__에서 경로를 받아 현재 프로젝트를 설정하는 기능 제공
"""

import os
from datetime import datetime
from typing import Optional, Dict, Any

class PathManager:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(PathManager, cls).__new__(cls)
        return cls._instance

    def __init__(self, project_root: str = None, user_id: str = None):
        if hasattr(self, '_initialized') and self._initialized:
            if project_root:
                self.set_current_project_root(project_root)
            if user_id:
                self._user_id = user_id
            return

        self._app_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        self._current_project_root = None
        self._project_info = {}
        self._user_id = user_id or os.getenv('USER_ID', 'guest')
        
        if project_root:
            self.set_current_project_root(project_root)
        self._initialized = True

    def get_app_root(self) -> str:
        return self._app_root

    def get_app_data_dir(self) -> str:
        data_dir = os.path.join(self.get_app_root(), 'data')
        os.makedirs(data_dir, exist_ok=True)
        return data_dir

    def get_app_storage_dir(self) -> str:
        """storage 디렉토리 경로 반환"""
        storage_dir = os.path.join(self.get_app_root(), 'storage')
        os.makedirs(storage_dir, exist_ok=True)
        return storage_dir
        
    def get_app_output_dir(self) -> str:
        """하위 호환성을 위해 유지"""
        output_dir = os.path.join(self.get_app_root(), 'output')
        os.makedirs(output_dir, exist_ok=True)
        return output_dir

    def set_current_project_root(self, root_dir: str):
        if root_dir:
            self._current_project_root = os.path.abspath(root_dir)
            self.ensure_project_structure()

    def get_current_project_root(self) -> Optional[str]:
        return self._current_project_root

    def create_new_project_root(self, project_name: str = None, user_id: str = None) -> str:
        """새로운 프로젝트를 output/{user_id}/{project_name} 구조로 생성"""
        if not project_name:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            project_name = f"project_{timestamp}"
            
        if user_id:
            self._user_id = user_id

        # output/{user_id}/{project_name} 구조 생성
        output_dir = self.get_app_output_dir()
        user_dir = os.path.join(output_dir, self._user_id)
        project_root = os.path.join(user_dir, project_name)
        
        os.makedirs(project_root, exist_ok=True)
        self.set_current_project_root(project_root)

        self._project_info = {
            "project_name": project_name,
            "user_id": self._user_id,
            "creation_date": datetime.now().isoformat(),
            "root_path": project_root
        }
        return project_root

    def _create_service_subdirs(self, base_path: str):
        """Helper function to create image and temp subdirectories."""
        os.makedirs(os.path.join(base_path, 'image'), exist_ok=True)
        os.makedirs(os.path.join(base_path, 'temp'), exist_ok=True)

    def ensure_project_structure(self):
        """가구 프로젝트 폴더 구조에 맞게 디렉토리 생성"""
        if not self._current_project_root:
            return

        # 기본 프로젝트 구조 생성
        base_dirs = [
            'generated_images', # 생성된 이미지
            'history',          # 작업 이력
            'meta'              # 메타 데이터
        ]

        for dir_path in base_dirs:
            full_path = os.path.join(self._current_project_root, dir_path)
            os.makedirs(full_path, exist_ok=True)

    def get_project_subdir(self, *path_parts: str) -> Optional[str]:
        if not self._current_project_root:
            return None
        dir_path = os.path.join(self._current_project_root, *path_parts)
        os.makedirs(dir_path, exist_ok=True)
        return dir_path
        


    def get_generated_images_dir(self) -> Optional[str]:
        return self.get_project_subdir('generated_images')

    def get_history_dir(self) -> Optional[str]:
        return self.get_project_subdir('history')

    def get_meta_dir(self) -> Optional[str]:
        return self.get_project_subdir('meta')
        



path_manager = PathManager()