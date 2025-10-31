import os
import sys

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                             QGroupBox, QGridLayout)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

class SettingWidget(QWidget):
    """Setting 위젯"""
    def __init__(self, main_app=None):
        super().__init__()
        self.main_app = main_app
        self.init_ui()
        self.load_user_data()
        
    def init_ui(self):
        layout = QVBoxLayout()
        
        title = QLabel('Setting')
        title.setFont(QFont("Noto Sans KR", 16, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #2E86AB; margin: 10px; padding: 10px;")
        layout.addWidget(title)
        
        account_group = QGroupBox("계정 정보")
        account_layout = QGridLayout()
        
        account_layout.addWidget(QLabel('이름:'), 0, 0)
        self.username_label = QLabel('로딩 중...')
        account_layout.addWidget(self.username_label, 0, 1)
        
        account_layout.addWidget(QLabel('이메일:'), 1, 0)
        self.email_label = QLabel('로딩 중...')
        account_layout.addWidget(self.email_label, 1, 1)
        
        logout_btn = QPushButton('로그아웃')
        logout_btn.clicked.connect(self.handle_logout)
        logout_btn.setFixedWidth(80)  # 고정 너비 설정
        logout_btn.setStyleSheet("""
            QPushButton {
                background-color: #A23B72;
                color: white;
                padding: 8px 15px;
                border: none;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #8E3160;
            }
        """)
        
        # 오른쪽 정렬을 위한 레이아웃
        logout_layout = QHBoxLayout()
        logout_layout.addStretch()
        logout_layout.addWidget(logout_btn)
        account_layout.addLayout(logout_layout, 2, 1)
        
        account_group.setLayout(account_layout)
        layout.addWidget(account_group)
        
        project_group = QGroupBox("프로젝트 설정")
        project_layout = QGridLayout()
        
        project_layout.addWidget(QLabel('프로젝트명:'), 0, 0)
        self.project_name_label = QLabel('프로젝트 없음')
        project_layout.addWidget(self.project_name_label, 0, 1)
        
        change_btn = QPushButton('변경')
        change_btn.clicked.connect(self.handle_project_change)
        
        # 버튼 크기와 스타일 설정
        change_btn.setFixedWidth(80)
        
        change_btn.setStyleSheet("""
            QPushButton { 
                background-color: #A23B72; 
                color: white; 
                padding: 8px 15px; 
                border: none; 
                border-radius: 5px; 
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #8E3160;
            }
        """)
        
        # 오른쪽 정렬을 위한 레이아웃 (변경 버튼만)
        change_layout = QHBoxLayout()
        change_layout.addStretch()
        change_layout.addWidget(change_btn)
        
        project_layout.addLayout(change_layout, 1, 1)
        
        project_group.setLayout(project_layout)
        layout.addWidget(project_group)
        
        layout.addStretch()
        self.setLayout(layout)
    
    def handle_logout(self):
        """로그아웃 처리"""
        from PyQt5.QtWidgets import QMessageBox
        
        reply = QMessageBox.question(self, '로그아웃', '로그아웃 하시겠습니까?',
                                   QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            if self.main_app:
                self.main_app.handle_logout()
    
    def handle_project_change(self):
        """프로젝트 변경 처리"""
        if self.main_app:
            self.main_app.show_project_change_dialog()
            # 프로젝트 변경 후 데이터 다시 로드
            self.load_user_data()
    
    def load_user_data(self):
        """사용자 데이터 및 프로젝트 정보 로드"""
        if self.main_app and self.main_app.user_manager:
            # 현재 로그인된 사용자 정보 가져오기
            current_user = self.main_app.user_manager.get_current_user()
            if current_user:
                self.username_label.setText(current_user.get('username', '알 수 없음'))
                self.email_label.setText(current_user.get('email', '알 수 없음'))
            else:
                self.username_label.setText('로그인 필요')
                self.email_label.setText('로그인 필요')
            
            # 현재 프로젝트 정보 가져오기
            if hasattr(self.main_app, 'current_project') and self.main_app.current_project:
                project_title = self.main_app.current_project.get('title') or self.main_app.current_project.get('name', '알 수 없음')
                self.project_name_label.setText(project_title)
            else:
                self.project_name_label.setText('프로젝트 없음')
        else:
            self.username_label.setText('데이터 없음')
            self.email_label.setText('데이터 없음')
            self.project_name_label.setText('프로젝트 없음')


def main():
    """Setting 위젯 독립 실행"""
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
    window.setWindowTitle('Setting Widget Test')
    window.setGeometry(100, 100, 840, 840)
    
    # 테스트를 위한 더미 메인 앱 객체
    class DummyMainApp:
        def __init__(self):
            self.user_manager = None
            self.current_project = None
    
    dummy_main_app = DummyMainApp()
    setting_widget = SettingWidget(dummy_main_app)
    window.setCentralWidget(setting_widget)
    
    window.show()
    
    return app.exec_()


if __name__ == '__main__':
    sys.exit(main())