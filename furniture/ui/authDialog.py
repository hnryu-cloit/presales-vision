import os
import sys
from datetime import datetime

import sqlite3
import hashlib
import json

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                             QLineEdit, QMessageBox, QDialog, QListWidget, QListWidgetItem,
                             QInputDialog)
from PyQt5.QtCore import Qt, pyqtSignal, QObject
from PyQt5.QtGui import QFont


def get_output_summary(project_path):
    """특정 프로젝트 경로에 대한 각 기능별 산출물 개수를 계산합니다."""
    functions_to_check = {
        'scenes': '공간',
        'furnitures': '가구',
        'generated_images': '결과물',
    }
    output_counts = {}
    for func_code in functions_to_check.keys():
        func_dir = os.path.join(project_path, func_code)
        count = 0
        if os.path.isdir(func_dir):
            try:
                # '.DS_Store'와 같은 숨김 파일을 제외하고 집계
                items = [item for item in os.listdir(func_dir) if not item.startswith('.')]
                count = len(items)
            except OSError:
                count = 0  # 권한 문제 등 발생 시 0으로 처리
        output_counts[func_code] = count
    return output_counts

class LoginWidget(QWidget):
    """로그인 위젯"""
    login_success = pyqtSignal()

    def __init__(self, user_manager=None):
        super().__init__()
        self.user_manager = user_manager or UserManager()
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setSpacing(20)

        center_layout = QHBoxLayout()
        center_layout.addStretch()

        login_container = QWidget()
        login_container.setStyleSheet("""
                    QWidget { 
                        background-color: white; 
                        border-radius: 13px; 
                        padding: 32px; 
                    }""")
        login_container.setFixedWidth(320)  # 400 * 0.8 = 320
        login_container.setFixedHeight(304)  # 380 * 0.8 = 304

        container_layout = QVBoxLayout(login_container)
        container_layout.setSpacing(16)  # 20 * 0.8 = 16
        container_layout.setContentsMargins(32, 32, 32, 32)  # 40 * 0.8 = 32

        login_title = QLabel('로그인')
        login_title.setAlignment(Qt.AlignCenter)
        login_title.setStyleSheet("""
            QLabel {
                font-size: 19px;
                font-weight: bold;
                color: #333; 
                margin-bottom: 8px; 
            }""")  # 24px * 0.8 = 19px, 10px * 0.8 = 8px
        container_layout.addWidget(login_title)

        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText('이메일')
        self.email_input.setMinimumHeight(44)  # 55 * 0.8 = 44
        self.email_input.setStyleSheet("""
            QLineEdit { 
                padding: 12px 16px; 
                font-size: 13px; 
                border: 2px solid #e0e0e0; 
                border-radius: 10px; 
                background-color: #f8f9fa; 
                color: #333; 
            } 
            QLineEdit:focus { 
                border-color: #4285f4; 
                background-color: white; 
            } 
            QLineEdit::placeholder { 
                color: #999; 
            }""")  # 15px*0.8=12px, 20px*0.8=16px, 16px*0.8=13px, 12px*0.8=10px
        container_layout.addWidget(self.email_input)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText('비밀번호')
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setMinimumHeight(44)  # 55 * 0.8 = 44
        self.password_input.setStyleSheet("""
            QLineEdit { 
                padding: 12px 16px; 
                font-size: 13px; 
                border: 2px solid #e0e0e0; 
                border-radius: 10px; 
                background-color: #f8f9fa; 
                color: #333; 
            } 
            QLineEdit:focus { 
                border-color: #4285f4; 
                background-color: white; 
            } 
            QLineEdit::placeholder {
                color: #999; 
            }""")  # 15px*0.8=12px, 20px*0.8=16px, 16px*0.8=13px, 12px*0.8=10px
        container_layout.addWidget(self.password_input)

        container_layout.addSpacing(15)

        self.login_btn = QPushButton('로그인')
        self.login_btn.clicked.connect(self.handle_login)
        self.login_btn.setMinimumHeight(44)  # 55 * 0.8 = 44
        self.login_btn.setStyleSheet("""
            QPushButton { 
                background-color: #4285f4; 
                color: white; 
                padding: 12px; 
                border: none; 
                border-radius: 10px; 
                font-weight: bold; 
                font-size: 13px; 
                margin-top: 8px; 
            } 
            QPushButton:hover {
                background-color: #3367d6; 
            }
            QPushButton:pressed {
                background-color: #2a56c6; 
            }""")  # 15px*0.8=12px, 12px*0.8=10px, 16px*0.8=13px, 10px*0.8=8px
        container_layout.addWidget(self.login_btn)

        self.register_btn = QPushButton('회원가입')
        self.register_btn.clicked.connect(self.show_register_dialog)
        self.register_btn.setMinimumHeight(44)  # 55 * 0.8 = 44
        self.register_btn.setStyleSheet("""
            QPushButton { 
                background-color: transparent;
                color: #4285f4; 
                padding: 12px; 
                border: 2px solid #4285f4; 
                border-radius: 10px; 
                font-weight: bold; 
                font-size: 13px; 
                margin-top: 4px; 
            } 
            QPushButton:hover { 
                background-color: rgba(66, 133, 244, 0.1); 
            } 
            QPushButton:pressed {
                background-color: rgba(66, 133, 244, 0.2); 
            }""")  # 15px*0.8=12px, 12px*0.8=10px, 16px*0.8=13px, 5px*0.8=4px
        container_layout.addWidget(self.register_btn)

        center_layout.addWidget(login_container)
        center_layout.addStretch()

        main_layout.addStretch()
        main_layout.addLayout(center_layout)
        main_layout.addStretch()

        self.setLayout(main_layout)

        self.email_input.returnPressed.connect(self.handle_login)
        self.password_input.returnPressed.connect(self.handle_login)

    def handle_login(self):
        email = self.email_input.text().strip()
        password = self.password_input.text().strip()

        if not email:
            QMessageBox.warning(self, '로그인 오류', '이메일을 입력해주세요.')
            return

        if not password:
            QMessageBox.warning(self, '로그인 오류', '비밀번호를 입력해주세요.')
            return

        # UserManager를 통한 실제 인증
        if self.user_manager.authenticate(email, password):
            user = self.user_manager.get_current_user()
            QMessageBox.information(self, '로그인 성공', f'{user["username"]}님 환영합니다!')
            self.login_success.emit()
        else:
            QMessageBox.warning(self, '로그인 실패', '이메일 또는 비밀번호가 올바르지 않습니다.')

    def show_register_dialog(self):
        dialog = RegisterDialog(self.user_manager, self)
        dialog.exec_()


class RegisterDialog(QDialog):
    """회원가입 다이얼로그"""

    def __init__(self, user_manager, parent=None):
        super().__init__(parent)
        self.user_manager = user_manager
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('회원가입')
        self.setFixedSize(400, 400)
        self.setModal(True)

        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(20, 20, 20, 20)

        # 제목
        title = QLabel('회원가입')
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont("Noto Sans KR", 18, QFont.Bold))
        title.setStyleSheet("color: #333; margin-bottom: 20px;")
        layout.addWidget(title)

        # 입력 필드들
        self.username_edit = QLineEdit()
        self.username_edit.setPlaceholderText('사용자명')
        self.username_edit.setMinimumHeight(40)
        layout.addWidget(self.username_edit)

        self.email_edit = QLineEdit()
        self.email_edit.setPlaceholderText('이메일')
        self.email_edit.setMinimumHeight(40)
        layout.addWidget(self.email_edit)

        self.password_edit = QLineEdit()
        self.password_edit.setPlaceholderText('비밀번호')
        self.password_edit.setEchoMode(QLineEdit.Password)
        self.password_edit.setMinimumHeight(40)
        layout.addWidget(self.password_edit)

        self.password_confirm_edit = QLineEdit()
        self.password_confirm_edit.setPlaceholderText('비밀번호 확인')
        self.password_confirm_edit.setEchoMode(QLineEdit.Password)
        self.password_confirm_edit.setMinimumHeight(40)
        layout.addWidget(self.password_confirm_edit)

        self.company_edit = QLineEdit()
        self.company_edit.setPlaceholderText('회사/소속')
        self.company_edit.setMinimumHeight(40)
        layout.addWidget(self.company_edit)

        # 버튼들
        button_layout = QHBoxLayout()

        cancel_button = QPushButton('취소')
        cancel_button.setMinimumHeight(40)
        cancel_button.clicked.connect(self.reject)
        cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #757575;
                color: white;
                border: none;
                border-radius: 6px;
                font-weight: bold;
                padding:10px;
            }
            QPushButton:hover {
                background-color: #616161;
            }
        """)
        button_layout.addWidget(cancel_button)

        signup_button = QPushButton('회원가입')
        signup_button.setMinimumHeight(40)
        signup_button.clicked.connect(self.handle_signup)
        signup_button.setStyleSheet("""
            QPushButton {
                background-color: #4285f4;
                color: white;
                border: none;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #3367d6;
            }
        """)
        button_layout.addWidget(signup_button)

        layout.addLayout(button_layout)
        self.setLayout(layout)

        # 공통 스타일
        self.setStyleSheet("""
            QLineEdit {
                padding: 10px;
                border: 2px solid #e0e0e0;
                border-radius: 6px;
                font-size: 14px;
                background-color: #f8f9fa;
            }
            QLineEdit:focus {
                border-color: #4285f4;
                background-color: white;
            }
        """)

    def handle_signup(self):
        # 입력 검증
        username = self.username_edit.text().strip()
        email = self.email_edit.text().strip()
        password = self.password_edit.text()
        password_confirm = self.password_confirm_edit.text()
        company = self.company_edit.text().strip()

        if not username or not email or not password:
            QMessageBox.warning(self, '입력 오류', '사용자명, 이메일, 비밀번호는 필수 항목입니다.')
            return

        if password != password_confirm:
            QMessageBox.warning(self, '입력 오류', '비밀번호와 비밀번호 확인이 일치하지 않습니다.')
            return

        if len(password) < 6:
            QMessageBox.warning(self, '입력 오류', '비밀번호는 최소 6자 이상이어야 합니다.')
            return

        # 회원가입 시도
        success, message = self.user_manager.register_user(username, email, password, company)
        print(f"register_user 결과: success={success}, message={message}")

        if success:
            QMessageBox.information(self, '회원가입 완료', message)
            self.accept()
        else:
            QMessageBox.warning(self, '회원가입 실패', message)


class UserManager(QObject):
    """사용자 인증 및 관리 클래스"""

    login_success = pyqtSignal(dict)  # 사용자 정보 전달

    def __init__(self):
        super().__init__()
        from furniture.admin.path_manager import path_manager
        self.db_path = os.path.join(path_manager.get_app_data_dir(), 'users.db')
        self.current_user = None
        self.init_database()

    def init_database(self):
        """사용자 데이터베이스 초기화"""
        # data 폴더 생성은 path_manager에서 처리합니다.
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 사용자 테이블 생성
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                company TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP,
                is_active BOOLEAN DEFAULT TRUE
            )
        ''')

        # 기본 관리자 계정 생성
        cursor.execute('SELECT COUNT(*) FROM users WHERE username = ?', ('admin',))
        if cursor.fetchone()[0] == 0:
            admin_password = self.hash_password('123456')
            cursor.execute('''
                INSERT INTO users (username, email, password_hash, company)
                VALUES (?, ?, ?, ?)
            ''', ('admin', 'admin@itcen.com', admin_password, 'admin'))

        conn.commit()
        conn.close()

    def hash_password(self, password):
        """비밀번호 해시화"""
        return hashlib.sha256(password.encode()).hexdigest()

    def authenticate(self, username, password):
        """사용자 인증"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        password_hash = self.hash_password(password)
        cursor.execute('''
            SELECT id, username, email, company 
            FROM users 
            WHERE (username = ? OR email = ?) AND password_hash = ? AND is_active = TRUE
        ''', (username, username, password_hash))

        user = cursor.fetchone()

        if user:
            # 로그인 시간 업데이트
            cursor.execute('UPDATE users SET last_login = ? WHERE id = ?',
                           (datetime.now(), user[0]))
            conn.commit()

            self.current_user = {
                'id': user[0],
                'username': user[1],
                'email': user[2],
                'company': user[3]
            }
            conn.close()
            return True

        conn.close()
        return False

    def register_user(self, username, email, password, company=''):
        """새 사용자 등록"""
        print(f"register_user 시작: username={username}, email={email}, company={company}")

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            password_hash = self.hash_password(password)
            cursor.execute('''
                INSERT INTO users (username, email, password_hash, company)
                VALUES (?, ?, ?, ?)
            ''', (username, email, password_hash, company))

            conn.commit()
            conn.close()
            return True, "회원가입이 완료되었습니다."

        except sqlite3.IntegrityError as e:
            conn.close()
            if 'username' in str(e):
                return False, "이미 존재하는 사용자명입니다."
            elif 'email' in str(e):
                return False, "이미 등록된 이메일입니다."
            else:
                return False, "회원가입 중 오류가 발생했습니다."
        except Exception as e:
            print(f"일반 예외 발생: {e}")  # 디버깅용
            conn.close()
            return False, f"회원가입 중 오류가 발생했습니다: {str(e)}"

    def change_password(self, current_password, new_password):
        """비밀번호 변경"""
        if not self.current_user:
            return False, "로그인이 필요합니다."

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 현재 비밀번호 확인
        current_hash = self.hash_password(current_password)
        cursor.execute('''
            SELECT id FROM users 
            WHERE id = ? AND password_hash = ?
        ''', (self.current_user['id'], current_hash))

        if not cursor.fetchone():
            conn.close()
            return False, "현재 비밀번호가 올바르지 않습니다."

        try:
            # 새 비밀번호로 업데이트
            new_hash = self.hash_password(new_password)
            cursor.execute('''
                UPDATE users SET password_hash = ? WHERE id = ?
            ''', (new_hash, self.current_user['id']))

            conn.commit()
            conn.close()
            return True, "비밀번호가 성공적으로 변경되었습니다."

        except Exception as e:
            conn.close()
            return False, f"비밀번호 변경 중 오류가 발생했습니다: {str(e)}"

    def get_current_user(self):
        """현재 로그인된 사용자 정보 반환"""
        return self.current_user

    def logout(self):
        """로그아웃"""
        self.current_user = None


class ProjectItemWidget(QWidget):
    def __init__(self, project_data):
        super().__init__()
        self.project_data = project_data
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(15, 10, 15, 10)
        main_layout.setSpacing(5)

        # 첫 번째 줄: 프로젝트명, 생성일, 수정일
        top_layout = QHBoxLayout()
        title_label = QLabel(f"<b>{self.project_data.get('title', 'N/A')}</b>")
        title_label.setFont(QFont("Noto Sans KR", 11, QFont.Bold))
        top_layout.addWidget(title_label)
        top_layout.addStretch()

        # 날짜 정보를 담을 VBox 레이아웃
        date_layout = QVBoxLayout()
        date_layout.setSpacing(2)  # 날짜 간 간격

        created_at = self.project_data.get('created_at', 'N/A')
        if 'T' in created_at:  # ISO 포맷 날짜 처리
            created_at = created_at.split('T')[0]
        date_label = QLabel(f"생성 일시: {created_at}")
        date_label.setStyleSheet("color: #666; font-size: 9pt;")
        date_label.setAlignment(Qt.AlignRight)
        date_layout.addWidget(date_label)

        updated_at = self.project_data.get('updated_at', 'N/A')
        update_date_label = QLabel(f"수정 일시: {updated_at}")
        update_date_label.setStyleSheet("color: #666; font-size: 9pt;")
        update_date_label.setAlignment(Qt.AlignRight)
        date_layout.addWidget(update_date_label)

        top_layout.addLayout(date_layout)
        main_layout.addLayout(top_layout)

        # 두 번째 줄: 산출물 현황 (한 줄)
        summary_data = self.project_data.get('output_summary', {})
        display_names = {
            'scenes': '공간',
            'furnitures': '가구',
            'generated_images': '결과물'
        }
        
        summary_parts = []
        for code, name in display_names.items():
            count = summary_data.get(code, 0)
            summary_parts.append(f"{name}: {count}개")
        
        summary_text = ' | '.join(summary_parts)
        summary_label = QLabel(summary_text)
        summary_label.setStyleSheet("color: #333; font-size: 9pt; padding-top: 4px;")
        main_layout.addWidget(summary_label)

        self.setLayout(main_layout)


class ProjectManager(QObject):
    """프로젝트 관리 클래스"""

    project_selected = pyqtSignal(dict)
    projects_updated = pyqtSignal()

    def __init__(self, user_manager):
        super().__init__()
        self.user_manager = user_manager
        self.current_project = None

    def create_new_project(self, project_name=None):
        """새 프로젝트 생성"""
        from furniture.admin.path_manager import path_manager
        user = self.user_manager.get_current_user()
        if not user:
            return False, "로그인이 필요합니다."

        if not project_name:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            project_name = f"project_{timestamp}"

        # 프로젝트 폴더명 정리
        project_name = "".join(c for c in project_name if c.isalnum() or c in (' ', '-', '_')).strip()
        if not project_name:
            return False, "올바른 프로젝트명을 입력해주세요."

        try:
            username = user.get('username', 'guest')
            
            # PathManager를 사용하여 프로젝트 경로 생성
            project_path = path_manager.create_new_project_root(project_name=project_name, user_id=username)

            # 프로젝트 메타데이터 생성 및 저장
            project_meta = {
                'name': project_name,
                'owner_id': user['id'],
                'owner_username': user['username'],
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'title': project_name,
                'description': '',
                'status': 'created',
            }

            meta_path = os.path.join(project_path, 'project_meta.json')
            with open(meta_path, 'w', encoding='utf-8') as f:
                json.dump(project_meta, f, ensure_ascii=False, indent=2)

            self.current_project = {
                'name': project_name,
                'path': project_path,
                'folder_path': project_path,
                'meta': project_meta
            }

            self.projects_updated.emit()
            return True, f"프로젝트 '{project_name}'이 생성되었습니다."

        except FileExistsError:
            return False, "이미 존재하는 프로젝트명입니다."
        except Exception as e:
            return False, f"프로젝트 생성 중 오류가 발생했습니다: {str(e)}"

    def load_project(self, project_info):
        """기존 프로젝트 로드"""
        try:
            if 'path' in project_info and 'folder_path' not in project_info:
                project_info['folder_path'] = project_info['path']

            # path_manager에 현재 프로젝트 루트 설정
            from furniture.admin.path_manager import path_manager
            project_path = project_info.get('path') or project_info.get('folder_path')
            if project_path:
                path_manager.set_current_project_root(project_path)

            self.current_project = project_info
            self.project_selected.emit(project_info)
            return True, f"프로젝트 '{project_info['title']}'을 로드했습니다."
        except Exception as e:
            return False, f"프로젝트 로드 중 오류가 발생했습니다: {str(e)}"

    def get_user_projects(self):
        """현재 사용자의 프로젝트 목록 반환"""
        from furniture.admin.path_manager import path_manager
        user = self.user_manager.get_current_user()
        if not user:
            return []

        username = user.get('username', 'guest')
        user_projects_dir = os.path.join(path_manager.get_app_output_dir(), username)

        projects = []
        if not os.path.exists(user_projects_dir):
            return projects

        for project_folder in os.listdir(user_projects_dir):
            project_path = os.path.join(user_projects_dir, project_folder)
            if os.path.isdir(project_path):
                meta_file = os.path.join(project_path, 'project_meta.json')
                if os.path.exists(meta_file):
                    try:
                        with open(meta_file, 'r', encoding='utf-8') as f:
                            meta_data = json.load(f)

                        # 최종 수정일 계산
                        try:
                            mtime = os.path.getmtime(project_path)
                            updated_at = datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M:%S')
                        except OSError:
                            updated_at = '알 수 없음'

                        # 각 프로젝트의 산출물 현황 집계
                        output_summary = get_output_summary(project_path)

                        project_info = {
                            'name': project_folder,
                            'path': project_path,
                            'folder_path': project_path,
                            'title': meta_data.get('title', project_folder),
                            'created_at': meta_data.get('created_at', '알 수 없음'),
                            'updated_at': updated_at,
                            'output_summary': output_summary,
                            'data': {}
                        }
                        projects.append(project_info)
                    except (json.JSONDecodeError, FileNotFoundError):
                        continue

        return sorted(projects, key=lambda x: x['created_at'], reverse=True)

    def delete_project(self, project_path):
        """프로젝트 삭제"""
        try:
            import shutil
            shutil.rmtree(project_path)
            self.projects_updated.emit()
            return True, "프로젝트가 삭제되었습니다."
        except Exception as e:
            return False, f"프로젝트 삭제 중 오류가 발생했습니다: {str(e)}"

    def export_project(self, project_path, export_path):
        """프로젝트 내보내기"""
        try:
            import shutil
            shutil.make_archive(export_path, 'zip', project_path)
            return True, f"프로젝트가 {export_path}.zip으로 내보내졌습니다."
        except Exception as e:
            return False, f"프로젝트 내보내기 중 오류가 발생했습니다: {str(e)}"

    def get_current_project(self):
        """현재 프로젝트 정보 반환"""
        return self.current_project


class ProjectSelectionDialog(QDialog):
    """프로젝트 선택 다이얼로그"""

    def __init__(self, project_manager, parent=None):
        super().__init__(parent)
        self.project_manager = project_manager
        self.selected_project = None
        self.init_ui()
        self.load_projects()
        self.project_manager.projects_updated.connect(self.load_projects)

    def init_ui(self):
        self.setWindowTitle('프로젝트 선택')
        self.setFixedSize(600, 500)
        self.setModal(True)

        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)

        # 제목
        title = QLabel('프로젝트 선택')
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont("Noto Sans KR", 16, QFont.Bold))
        layout.addWidget(title)

        # 프로젝트 목록
        self.project_list = QListWidget()
        self.project_list.setMinimumHeight(300)
        self.project_list.itemDoubleClicked.connect(self.on_project_double_clicked)
        self.project_list.itemSelectionChanged.connect(self.on_project_selection_changed)
        self.project_list.setStyleSheet("""
            QListWidget::item { 
                border-bottom: 1px solid #e0e0e0; 
            }
            QListWidget::item:selected {
                background-color: #e3f2fd;
                color: black;
            }
        """)
        layout.addWidget(self.project_list)

        # 버튼들
        button_layout = QHBoxLayout()

        new_project_button = QPushButton('새 프로젝트')
        new_project_button.clicked.connect(self.create_new_project)
        new_project_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        button_layout.addWidget(new_project_button)

        self.delete_button = QPushButton('삭제')
        self.delete_button.clicked.connect(self.delete_selected_project)
        self.delete_button.setEnabled(False)
        self.delete_button.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #d32f2f;
            }
            QPushButton:disabled {
                background-color: #e0e0e0;
                color: #9e9e9e;
            }
        """)
        button_layout.addWidget(self.delete_button)

        button_layout.addStretch()

        select_button = QPushButton('선택')
        select_button.clicked.connect(self.select_project)
        select_button.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        button_layout.addWidget(select_button)

        cancel_button = QPushButton('취소')
        cancel_button.clicked.connect(self.reject)
        cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #757575;
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #616161;
            }
        """)
        button_layout.addWidget(cancel_button)

        layout.addLayout(button_layout)
        self.setLayout(layout)

    def on_project_selection_changed(self):
        self.delete_button.setEnabled(len(self.project_list.selectedItems()) > 0)

    def delete_selected_project(self):
        current_item = self.project_list.currentItem()
        if not current_item:
            return

        project_data = current_item.data(Qt.UserRole)
        project_name = project_data.get('name', 'N/A')
        project_path = project_data.get('path')

        if not project_path:
            QMessageBox.warning(self, '삭제 오류', '프로젝트 경로를 찾을 수 없습니다.')
            return

        reply = QMessageBox.question(self, '프로젝트 삭제 확인',
                                   f"'{project_name}' 프로젝트를 정말로 삭제하시겠습니까?\n이 작업은 되돌릴 수 없습니다.",
                                   QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            success, message = self.project_manager.delete_project(project_path)
            if success:
                QMessageBox.information(self, '프로젝트 삭제 완료', message)
                self.load_projects()
                # 만약 현재 열려있는 프로젝트가 삭제되었다면, 메인 앱에 알려야 함
                if self.parent() and hasattr(self.parent(), 'current_project') and self.parent().current_project and self.parent().current_project.get('path') == project_path:
                    self.parent().current_project = None
                    # SettingWidget UI 갱신을 위해 신호 발생 또는 직접 호출
                    if hasattr(self.parent(), 'content_stack'):
                        setting_widget = self.parent().content_stack.widget(6) # SettingWidget의 인덱스
                        if setting_widget and hasattr(setting_widget, 'load_user_data'):
                            setting_widget.load_user_data()

            else:
                QMessageBox.warning(self, '프로젝트 삭제 실패', message)

    def load_projects(self):
        """프로젝트 목록 로드"""
        self.project_list.clear()
        projects = self.project_manager.get_user_projects()

        for project in projects:
            item = QListWidgetItem(self.project_list)
            item.setData(Qt.UserRole, project)
            
            item_widget = ProjectItemWidget(project)
            item.setSizeHint(item_widget.sizeHint())
            
            self.project_list.addItem(item)
            self.project_list.setItemWidget(item, item_widget)

    def create_new_project(self):
        """새 프로젝트 생성"""
        project_name, ok = QInputDialog.getText(self, '새 프로젝트', '프로젝트명을 입력하세요:')

        if ok and project_name.strip():
            success, message = self.project_manager.create_new_project(project_name.strip())

            if success:
                QMessageBox.information(self, '프로젝트 생성', message)
                self.selected_project = self.project_manager.get_current_project()
                self.accept()
            else:
                QMessageBox.warning(self, '프로젝트 생성 실패', message)

    def select_project(self):
        """프로젝트 선택"""
        current_item = self.project_list.currentItem()
        if current_item:
            project_data = current_item.data(Qt.UserRole)
            success, message = self.project_manager.load_project(project_data)

            if success:
                self.selected_project = project_data
                self.accept()
            else:
                QMessageBox.warning(self, '프로젝트 로드 실패', message)
        else:
            QMessageBox.warning(self, '선택 오류', '프로젝트를 선택해주세요.')

    def on_project_double_clicked(self, item):
        """프로젝트 더블클릭으로 선택"""
        project_data = item.data(Qt.UserRole)
        success, message = self.project_manager.load_project(project_data)

        if success:
            self.selected_project = project_data
            self.accept()
        else:
            QMessageBox.warning(self, '프로젝트 로드 실패', message)

    def get_selected_project(self):
        """선택된 프로젝트 반환"""
        return self.selected_project


def main():
    """Auth 위젯 독립 실행"""
    from PyQt5.QtWidgets import QApplication, QMainWindow
    
    app = QApplication(sys.argv)
    
    # 폰트 설정
    font = QFont("Malgun Gothic", 9)  # Windows
    if font.family() == "Malgun Gothic":
        app.setFont(font)
    else:
        font = QFont("Apple SD Gothic Neo", 9)
        if font.family() != "Apple SD Gothic Neo":
            font = QFont("Noto Sans CJK KR", 9)
        app.setFont(font)
    
    app.setStyle('Fusion')
    
    window = QMainWindow()
    window.setWindowTitle('Auth Widget Test')
    window.setGeometry(100, 100, 840, 840)
    
    # 테스트를 위한 기본 설정
    user_manager = UserManager()
    login_widget = LoginWidget(user_manager)
    window.setCentralWidget(login_widget)
    
    window.show()
    
    return app.exec_()


if __name__ == '__main__':
    sys.exit(main())
