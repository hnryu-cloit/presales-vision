import sys
import os
import json

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLineEdit, QLabel, QTextEdit, QFormLayout,
    QGroupBox, QStackedWidget, QFrame, QGridLayout, QFileDialog,
    QScrollArea, QDialog, QMessageBox, QListWidget, QListWidgetItem,
    QInputDialog, QTreeWidget, QTreeWidgetItem, QHeaderView)
from PyQt5.QtGui import QFont, QPixmap, QIcon
from PyQt5.QtCore import Qt, QThread, pyqtSignal, pyqtSlot, QTimer, QObject

class ClickableLabel(QLabel):
    clicked = pyqtSignal(int)

    def __init__(self, text="", index=-1, parent=None):
        super().__init__(text, parent)
        self.index = index

    def mousePressEvent(self, event):
        self.clicked.emit(self.index)
        super().mousePressEvent(event)


from common.gemini import Gemini
from common import config
from generate import ImageGenerator
from analyzer import VisionAnalyzer
from admin.path_manager import path_manager
from ui.authDialog import LoginWidget, RegisterDialog, UserManager, ProjectItemWidget, ProjectManager, ProjectSelectionDialog
from ui.otherDialog import SettingWidget




class AnalysisThread(QThread):
    analysis_ready = pyqtSignal(list)
    error_occurred = pyqtSignal(str)

    def __init__(self, analyzer, **kwargs):
        super().__init__()
        self.analyzer = analyzer
        self.kwargs = kwargs

    def run(self):
        try:
            result = self.analyzer.analyze(**self.kwargs)
            self.analysis_ready.emit(result)
        except Exception as e:
            self.error_occurred.emit(f"An error occurred during analysis: {e}")

class ImageGenerationThread(QThread):
    images_ready = pyqtSignal(list)
    error_occurred = pyqtSignal(str)

    def __init__(self, generator, mode, **kwargs):
        super().__init__()
        self.generator = generator
        self.mode = mode
        self.kwargs = kwargs

    def run(self):
        try:
            if self.mode == "change_attributes": result = self.generator.change_attributes(**self.kwargs)
            elif self.mode == "create_thumbnail": result = self.generator.create_thumbnail_with_metadata(**self.kwargs)
            elif self.mode == "apply_style": result = self.generator.apply_style_from_reference(**self.kwargs)
            elif self.mode == "replace_object": result = self.generator.replace_object_in_reference(**self.kwargs)
            elif self.mode == "create_scene": result = self.generator.create_interior_scene(**self.kwargs)
            else: self.error_occurred.emit(f"Unknown generation mode: {self.mode}"); return
            self.images_ready.emit(result)
        except Exception as e:
            self.error_occurred.emit(f"An error occurred during image generation: {e}")


class AIGeneratorApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ITCEN CLOIT")
        self.setWindowIcon(QIcon("../favicon.png"))
        self.setGeometry(100, 100, 1200, 800)

        self.user_manager = UserManager()
        self.project_manager = ProjectManager(self.user_manager)
        self.current_project = None
        self.analysis_results = None

        self.init_ui()

    def init_ui(self):
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QHBoxLayout(self.central_widget)
        self.main_layout.setSpacing(0)
        self.main_layout.setContentsMargins(0, 0, 0, 0)

        self.gemini_client = Gemini()
        self.generation_mode = None
        self.image_generator = None # Will be initialized after project selection
        self.analyzer = None # Will be initialized after project selection

        self.loading_text_index = 0
        self.loading_texts = [
            "입력 이미지 데이터 분석중...",
            "이미지 특징 추출 중...",
            "레퍼런스 이미지 분석중...",
            "최종 결과 조합 중...",
            "조금만 기다려주세요, 거의 완성되었습니다!"
        ]
        self.animation_timer = QTimer(self)
        self.animation_timer.timeout.connect(self.update_loading_animation)

        self.create_sidebar()
        self.create_main_content_area()
        self.content_stack.setCurrentWidget(self.login_page)

    def handle_login_success(self):
        self.show_project_selection_dialog()

    def show_project_selection_dialog(self):
        dialog = ProjectSelectionDialog(self.project_manager, self)
        if dialog.exec_() == QDialog.Accepted:
            selected_project = dialog.get_selected_project()
            if selected_project:
                self.load_project(selected_project)

    def load_project(self, project_info):
        self.current_project = project_info

        project_path = self.current_project['path']
        path_manager.set_current_project_root(project_path)

        # Initialize managers that depend on project path
        self.output_dir = path_manager.get_generated_images_dir()
        self.meta_dir = path_manager.get_meta_dir()

        self.image_generator = ImageGenerator(output_dir=self.output_dir)
        self.analyzer = VisionAnalyzer(input_dir=project_path, output_dir=self.meta_dir)

        # Update UI and switch view
        self.setting_page.load_user_data()
        self.content_stack.setCurrentWidget(self.workflow_widget)
        self.workflow_stack.setCurrentWidget(self.page1)
        self.update_workflow_ui(0)

    def handle_logout(self):
        self.user_manager.logout()
        self.current_project = None
        self.content_stack.setCurrentWidget(self.login_page)

    def show_project_change_dialog(self):
        self.show_project_selection_dialog()

    # --- Sidebar and Content Area Creation ---
    def create_sidebar(self):
        sidebar = QFrame()
        sidebar.setFixedWidth(250)
        sidebar.setStyleSheet("QFrame { background: #273444; border: none; }")
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(20, 30, 20, 20)
        sidebar_layout.setSpacing(5)

        title_label = QLabel("CEN AI Studio")
        title_label.setFont(QFont("Noto Sans KR", 18, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("QLabel { color: #FFFFFF; font-weight: bold; margin-bottom: 10px; padding: 10px; }")
        sidebar_layout.addWidget(title_label)
        sidebar_layout.addSpacing(5)

        self.sidebar_labels = [
            ClickableLabel("Step 1: 옵션 선택", index=0),
            ClickableLabel("Step 2: 이미지 생성", index=1),
            ClickableLabel("Step 3: 이미지 편집", index=2),
            ClickableLabel("Step 4: 결과 확인", index=3),
            ClickableLabel("Step 5: 분석 확인", index=4)
        ]
        for label in self.sidebar_labels:
            label.setFont(QFont("Noto Sans KR", 16, QFont.Medium))
            label.setStyleSheet("QLabel { color: #A0AEC0; padding: 12px 15px; border-radius: 6px; background: transparent; font-size: 16px; font-weight: 400; }")
            label.clicked.connect(self.go_to_step)
            sidebar_layout.addWidget(label)

        sidebar_layout.addStretch(1)

        # Settings Button
        self.settings_button = QPushButton("Setting")
        self.settings_button.setFont(QFont("Noto Sans KR", 16, QFont.Medium))
        self.settings_button.clicked.connect(self.show_settings_page)
        self.settings_button.setStyleSheet('''
            QPushButton { 
                color: #A0AEC0; 
                text-align: left; 
                padding: 12px 15px; 
                border:none; 
                border-radius: 6px;
                font-size: 16px; font-weight: 400;
                background: transparent;
            }
            QPushButton:hover { background-color: rgba(255, 255, 255, 0.1); }
        ''')
        sidebar_layout.addWidget(self.settings_button)

        copyright_label = QLabel("Copyright © 2025\nITCEN CLOIT\nAll rights reserved.")
        copyright_label.setFont(QFont("Noto Sans KR", 11)); copyright_label.setAlignment(Qt.AlignCenter)
        copyright_label.setWordWrap(True)
        copyright_label.setStyleSheet("QLabel { color: #8A9EB2; padding: 15px 10px; font-weight: 300; }")
        sidebar_layout.addWidget(copyright_label)
        self.main_layout.addWidget(sidebar)

    def create_main_content_area(self):
        main_content_container = QWidget(); main_content_container.setStyleSheet("background: #f8f9fa;")
        container_layout = QVBoxLayout(main_content_container); container_layout.setContentsMargins(0,0,0,0)
        self.content_stack = QStackedWidget(); container_layout.addWidget(self.content_stack)

        # Page 0: Login
        self.login_page = LoginWidget(self.user_manager)
        self.login_page.login_success.connect(self.handle_login_success)
        self.content_stack.addWidget(self.login_page)

        # Page 1: Main Workflow
        self.workflow_widget = QWidget()
        workflow_layout = QVBoxLayout(self.workflow_widget)
        workflow_layout.setContentsMargins(30, 30, 30, 30)
        workflow_layout.setSpacing(10)

        self.workflow_stack = QStackedWidget()
        self.page1 = self.create_step1_page()
        self.page2 = self.create_step3_page()
        self.page3 = self.create_step4_page()
        self.page4 = self.create_step5_page()
        self.page5 = self.create_analysis_results_page()

        self.workflow_stack.addWidget(self.page1);
        self.workflow_stack.addWidget(self.page2);
        self.workflow_stack.addWidget(self.page3);
        self.workflow_stack.addWidget(self.page4);
        self.workflow_stack.addWidget(self.page5)
        workflow_layout.addWidget(self.workflow_stack)
        nav_layout = QHBoxLayout()
        self.home_button = QPushButton("홈화면")
        self.home_button.setStyleSheet('''
            QPushButton {
                background: #6c757d; color: white; border: none; border-radius: 6px;
                padding: 10px 20px; font-size: 13px; font-weight: 500; min-width: 60px;
            }
            QPushButton:hover { background: #5a6268; }
            QPushButton:pressed { background: #494f54; }
        ''')
        self.home_button.clicked.connect(self.go_to_home_screen)
        nav_layout.addWidget(self.home_button)
        nav_layout.addStretch(1)

        self.prev_button = QPushButton("← 이전"); self.next_button = QPushButton("다음 →")
        for btn in [self.prev_button, self.next_button]:
            btn.setStyleSheet('''
                QPushButton {
                    background: #A23B72; color: white; border: none; border-radius: 6px;
                    padding: 10px 20px; font-size: 13px; font-weight: 500; min-width: 60px;
                }
                QPushButton:hover { background: #8A2F5F; }
                QPushButton:pressed { background: #6D2349; }
                QPushButton:disabled { background: #6c757d; color: #dee2e6; }
            ''')
        self.prev_button.clicked.connect(self.go_to_prev_step); self.next_button.clicked.connect(self.go_to_next_step)
        nav_layout.addWidget(self.prev_button); nav_layout.addSpacing(15); nav_layout.addWidget(self.next_button)
        workflow_layout.addLayout(nav_layout)
        self.content_stack.addWidget(self.workflow_widget)
        # Page 2: Settings
        self.setting_page = SettingWidget(self)
        self.content_stack.addWidget(self.setting_page)
        self.main_layout.addWidget(main_content_container)

    def show_settings_page(self):
        if self.user_manager.get_current_user():
            self.setting_page.load_user_data()
            self.content_stack.setCurrentWidget(self.setting_page)
            self.update_workflow_ui(-1)
        else:
            QMessageBox.warning(self, "로그인 필요", "설정 페이지를 보려면 먼저 로그인해야 합니다.")

    def create_step1_page(self):
        scroll_area = QScrollArea(); scroll_area.setWidgetResizable(True); scroll_area.setFrameShape(QFrame.NoFrame); scroll_area.setStyleSheet("QScrollArea { background: transparent; }")
        page = QWidget(); page.setStyleSheet("background: transparent;"); layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 15, 0, 0); layout.setSpacing(18)
        title = QLabel("AI 이미지 생성 옵션"); title.setStyleSheet("QLabel { font-size: 22px; font-weight: 700; color: #212529; margin-bottom: 0px; padding: 0px 0px 10px 0px; border-bottom: 3px solid #007bff; }"); layout.addWidget(title)
        options_group = QGroupBox("생성 기능 선택"); options_group.setStyleSheet("QGroupBox { border: 2px solid #e8f5e9; border-radius: 12px; margin-top: 8px; padding: 20px 15px 15px 15px; font-weight: 600; font-size: 14px; color: #2e7d32; background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #ffffff, stop:1 #f9fdf9); } QGroupBox::title { background: transparent; padding: 5px 10px; color: #2e7d32; }")
        options_layout = QGridLayout(options_group)
        self.option_buttons = {"analyze_product": QPushButton("제품 분석"),"change_attributes": QPushButton("속성 변경"),"create_thumbnail": QPushButton("썸네일 생성"),"apply_style": QPushButton("스타일 적용"),"replace_object": QPushButton("객체 교체"),"create_scene": QPushButton("스튜디오 촬영")}
        positions = [(i, j) for i in range(2) for j in range(3)]
        for (i, j), (mode, btn) in zip(positions, self.option_buttons.items()):
            btn.setStyleSheet("QPushButton { background: white; color: #495057; border: 2px solid #dee2e6; border-radius: 10px; padding: 12px 18px; font-size: 13px; font-weight: 600; min-width: 120px; } QPushButton:hover { background: #f8f9fa; border-color: #007bff; } QPushButton:checked { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #667eea, stop:1 #764ba2); color: white; border-color: #667eea; }")
            btn.setCheckable(True); btn.clicked.connect(lambda checked, m=mode: self.set_generation_mode(m)); options_layout.addWidget(btn, i, j)
        layout.addWidget(options_group)
        self.dynamic_options_widget = QWidget(); self.dynamic_options_layout = QVBoxLayout(self.dynamic_options_widget); self.dynamic_options_layout.setContentsMargins(0,0,0,0); layout.addWidget(self.dynamic_options_widget)
        layout.addStretch(1); scroll_area.setWidget(page); return scroll_area

    def create_analysis_results_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(15, 15, 15, 15)

        # Image frame
        self.analysis_image_label = QLabel()
        self.analysis_image_label.setAlignment(Qt.AlignCenter)
        self.analysis_image_label.setMinimumHeight(250)
        self.analysis_image_label.setStyleSheet("border: 1px solid #ddd; border-radius: 8px; background-color: #fdfdfd;")
        layout.addWidget(self.analysis_image_label)

        # Table frame
        table_group = QGroupBox("분석 결과")
        table_group.setStyleSheet("QGroupBox { font-weight: bold; } QGroupBox::title { font-size: 20px; }")
        table_layout = QVBoxLayout(table_group)
        
        self.analysis_tree = QTreeWidget()
        self.analysis_tree.setColumnCount(3)
        self.analysis_tree.setHeaderLabels(['Field', 'Value', 'Reason'])
        self.analysis_tree.header().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.analysis_tree.header().setStretchLastSection(True)
        
        table_layout.addWidget(self.analysis_tree)
        layout.addWidget(table_group, 7)

        # Description frame
        desc_group = QGroupBox("제품 설명")
        desc_group.setStyleSheet("QGroupBox { font-weight: bold; } QGroupBox::title { font-size: 20px; }")
        desc_layout = QVBoxLayout(desc_group)
        self.analysis_description_text = QTextEdit()
        self.analysis_description_text.setReadOnly(True)
        desc_layout.addWidget(self.analysis_description_text)
        layout.addWidget(desc_group, 3)

        return page

    @pyqtSlot(list)
    def on_analysis_ready(self, results):
        self.analysis_results = results
        self.animation_timer.stop()
        self.workflow_stack.setCurrentWidget(self.page5)
        self.update_workflow_ui(4)
        if not results:
            QMessageBox.warning(self, "오류", "분석 결과가 없습니다.")
            self.go_to_prev_step()
            return

        # For simplicity, displaying the first result if multiple are returned
        result = results[0]
        
        # --- Populate UI with result ---
        # 1. Display Image
        pixmap = QPixmap(result['image_path'])
        self.analysis_image_label.setPixmap(pixmap.scaled(self.analysis_image_label.width(), 300, Qt.KeepAspectRatio, Qt.SmoothTransformation))

        # 2. Populate Tree Widget
        self.analysis_tree.clear()
        try:
            attributes = json.loads(result.get('attributes', '{}'))
            description_data = json.loads(result.get('description', '{}'))
        except json.JSONDecodeError:
            attributes = {}
            description_data = {}

        category = result.get('category', '')
        category_attributes = config.PRODUCT_ATTRIBUTE.get(category, {})

        rows_data = [
            ('filename', result.get('filename', ''), '-'),
            ('category', result.get('category', ''), '-'),
            ('sub_category', result.get('sub_category', ''), '-'),
        ]

        for attr_key in category_attributes.keys():
            value, reason = self._extract_attribute_value_reason(attributes, attr_key)
            if value and value.strip():
                rows_data.append((attr_key, value, reason))

        common_attrs = ['스타일', '색상', '무늬', '타겟 고객', '타겟 연령층']
        for attr_key in common_attrs:
            if attr_key not in category_attributes:
                value, reason = self._extract_attribute_value_reason(attributes, attr_key)
                if value and value.strip():
                    rows_data.append((attr_key, value, reason))
        
        processed_keys = {row[0] for row in rows_data}
        for attr_key, attr_data in attributes.items():
            if attr_key not in processed_keys:
                value, reason = self._parse_attribute_data(attr_data, attr_key)
                if value and value.strip():
                    rows_data.append((attr_key, value, reason))

        for i, (field, value, reason) in enumerate(rows_data):
            if value and value.strip():
                item = QTreeWidgetItem(self.analysis_tree, [str(field), str(value), str(reason)])
                if i % 2 == 1:
                    for j in range(3):
                        item.setBackground(j, Qt.lightGray)


        # 3. Display Description
        description_content = description_data.get('description', '설명 정보 없음')
        self.analysis_description_text.setText(description_content)

        self.workflow_stack.setCurrentWidget(self.page5)
        self.update_workflow_ui(4)

    def _extract_attribute_value_reason(self, attributes, attr_key):
        """주어진 속성 키에 대한 값과 이유를 추출"""
        value = ''
        reason = ''

        # 1. 직접 매치 시도
        if attr_key in attributes:
            attr_data = attributes[attr_key]
            value, reason = self._parse_attribute_data(attr_data, attr_key)
            if value:
                return value, reason

        # 2. 키 매핑을 통한 매치 시도
        key_mappings = {
            '색상': ['color', '컬러', 'colour'],
            '주요 소재': ['material', '소재', 'materials', '재료', '상판 소재', '프레임 소재'],
            '유형': ['type', '타입'],
            '형태': ['shape', 'form'],
            '침구 사이즈': ['size', '사이즈', '크기', '침구사이즈'],
            '단 수': ['단수', '단', 'tier', 'level'],
            '우드톤': ['wood_tone', 'woodtone', '우드', 'wood'],
            '도어 형태': ['door_type', 'door', '도어', '문'],
            '다리': ['leg', 'legs', '다리', '받침'],
            '바퀴': ['wheel', 'wheels', '바퀴', '캐스터'],
            '서랍': ['drawer', 'drawers', '서랍'],
            '헤드 유무': ['head', '헤드', 'headboard', '헤드보드'],
            '프레임 형태': ['frame', '프레임', 'frame_type'],
            '스타일': ['style'],
            '무늬': ['pattern', '패턴'],
            '타겟 고객': ['target', '타겟'],
            '타겟 연령층': ['age', '연령', 'age_group']
        }

        possible_keys = key_mappings.get(attr_key, [])
        for mapped_key in possible_keys:
            if mapped_key in attributes:
                attr_data = attributes[mapped_key]
                value, reason = self._parse_attribute_data(attr_data, attr_key)
                if value:
                    return value, reason

        # 3. 대소문자 및 공백 무시한 매치 시도
        attr_key_clean = attr_key.lower().replace(' ', '').replace('·', '')
        for key in attributes.keys():
            key_clean = key.lower().replace(' ', '').replace('·', '')
            if key_clean == attr_key_clean:
                attr_data = attributes[key]
                value, reason = self._parse_attribute_data(attr_data, attr_key)
                if value:
                    return value, reason

        return '', f'{attr_key} 정보 없음'

    def _parse_attribute_data(self, attr_data, attr_key):
        """속성 데이터에서 값과 이유를 파싱"""
        value = ''
        reason = ''

        if isinstance(attr_data, dict):

            value = attr_data.get('value', '')
            reason = attr_data.get('reason', '')
            # 값이 없으면 전체 딕셔너리에서 의미있는 값 찾기
            if not value:
                meaningful_values = [v for v in attr_data.values() if v and str(v).strip() and str(v) != 'null']
                if meaningful_values:
                    value = str(meaningful_values[0])
        else:
            value = str(attr_data) if attr_data else ''

        # 기본 이유 설정
        if value and not reason:
            reason = f'{attr_key} 분석 결과'

        # 의미없는 값 필터링
        if value and (value.startswith('{') or value == 'null' or value.lower() == 'none'):
            value = ''

        return value.strip(), reason.strip()

    def set_generation_mode(self, mode):
        self.generation_mode = mode
        for m, btn in self.option_buttons.items():
            if m != mode: btn.setChecked(False)
        self.update_dynamic_options()

    def update_dynamic_options(self):
        while self.dynamic_options_layout.count():
            child = self.dynamic_options_layout.takeAt(0)
            if child.widget(): child.widget().deleteLater()
        if self.generation_mode is None: return
        if self.generation_mode == 'analyze_product':
            self.main_product_group = self.create_image_input_group("분석할 상품 이미지", "main_product", max_images=5)
            self.dynamic_options_layout.addWidget(self.main_product_group); return
        self.main_product_group = self.create_image_input_group("메인 상품 이미지", "main_product", max_images=1 if self.generation_mode != 'create_scene' else 5)
        self.dynamic_options_layout.addWidget(self.main_product_group)
        if self.generation_mode in ['apply_style', 'replace_object', 'create_thumbnail']:
            self.reference_group = self.create_image_input_group("레퍼런스 이미지", "reference", max_images=5)
            self.dynamic_options_layout.addWidget(self.reference_group)
        if self.generation_mode == 'change_attributes':
            self.instructions_group = QGroupBox("변경 지시사항"); self.instructions_layout = QVBoxLayout(self.instructions_group)
            self.instructions_input = QTextEdit(); self.instructions_input.setPlaceholderText("예: 제품을 우측 컷으로 변경해주세요.")
            self.instructions_layout.addWidget(self.instructions_input); self.dynamic_options_layout.addWidget(self.instructions_group)

    def create_image_input_group(self, title, key, max_images=3):
        group_box = QGroupBox(title); group_box.setStyleSheet("QGroupBox { border: 2px solid #e3f2fd; border-radius: 12px; margin-top: 8px; padding: 20px 15px 15px 15px; font-weight: 600; font-size: 14px; color: #1976d2; background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #ffffff, stop:1 #f8fbff); } QGroupBox::title { background: transparent; padding: 5px 10px; color: #1976d2;}")
        layout = QVBoxLayout(group_box); scroll_area = QScrollArea(); scroll_area.setFrameShape(QFrame.NoFrame); scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded); scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff); scroll_area.setFixedHeight(110)
        image_grid_widget = QWidget(); image_grid_layout = self.create_image_grid_layout(); image_grid_widget.setLayout(image_grid_layout)
        scroll_area.setWidget(image_grid_widget); layout.addWidget(scroll_area)
        setattr(image_grid_widget, 'image_paths', []); setattr(image_grid_widget, 'max_images', max_images); setattr(group_box, 'grid_widget', image_grid_widget)
        self.update_image_grid(image_grid_widget); return group_box

    def create_image_grid_layout(self):
        layout = QHBoxLayout(); layout.setContentsMargins(0, 0, 0, 0); layout.setSpacing(10); layout.addStretch(); return layout

    def create_image_card(self, image_path, grid_widget):
        card = QWidget(); card.setFixedSize(96, 96); card.setStyleSheet("QWidget { border: 2px solid #e9ecef; border-radius: 8px; background-color: white; } QWidget:hover { border-color: #667eea; }")
        layout = QVBoxLayout(card); layout.setContentsMargins(3, 3, 3, 3); img_label = QLabel()
        pixmap = QPixmap(image_path); scaled_pixmap = pixmap.scaled(90, 90, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        img_label.setPixmap(scaled_pixmap); img_label.setAlignment(Qt.AlignCenter); layout.addWidget(img_label)
        delete_btn = QPushButton("✕", card); delete_btn.setFixedSize(22, 22); delete_btn.move(card.width() - delete_btn.width() - 1, 1)
        delete_btn.setStyleSheet("QPushButton { border: none; background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #f857a6, stop:1 #ff5858); color: white; font-weight: bold; font-size: 12px; border-radius: 11px; } QPushButton:hover { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #ff5858, stop:1 #f857a6); }")
        delete_btn.clicked.connect(lambda: self.remove_image_card(image_path, grid_widget)); return card

    def create_add_button(self, grid_widget):
        add_card = QWidget(); add_card.setFixedSize(96, 96); add_card.setStyleSheet("QWidget {  border: 2px dashed #adb5bd; border-radius: 8px;  background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #ffffff, stop:1 #f8f9fa); } QWidget:hover {  border-color: #667eea;  background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #f8f9ff, stop:1 #e9ecff); }")
        layout = QVBoxLayout(add_card); add_label = QLabel("+"); add_label.setAlignment(Qt.AlignCenter)
        add_label.setStyleSheet("border: none; background-color: transparent; color: #667eea; font-size: 28px; font-weight: bold;"); layout.addWidget(add_label)
        add_card.mousePressEvent = lambda event: self.add_images_to_grid(grid_widget); return add_card

    def add_images_to_grid(self, grid_widget):
        max_images = getattr(grid_widget, 'max_images', 3)
        files, _ = QFileDialog.getOpenFileNames(self, "이미지 선택", "", "Image files (*.png *.jpg *.jpeg)")
        if files:
            current_count = len(grid_widget.image_paths); available_slots = max_images - current_count
            if available_slots <= 0: QMessageBox.warning(self, "최대 개수 초과", f"최대 {max_images}개까지만 등록할 수 있습니다."); return
            if len(files) > available_slots: files = files[:available_slots]; QMessageBox.information(self, "일부 파일 선택", f"최대 개수 제한으로 {available_slots}개 파일만 선택되었습니다.")
            grid_widget.image_paths.extend(files)
        self.update_image_grid(grid_widget)

    def remove_image_card(self, image_path, grid_widget):
        if image_path in grid_widget.image_paths: grid_widget.image_paths.remove(image_path); self.update_image_grid(grid_widget)

    def update_image_grid(self, grid_widget):
        layout = grid_widget.layout()
        max_images = getattr(grid_widget, 'max_images', 3)
        while layout.count():
            child = layout.takeAt(0)
            if child.widget(): child.widget().deleteLater()
        for image_path in grid_widget.image_paths: card = self.create_image_card(image_path, grid_widget); layout.addWidget(card)
        if len(grid_widget.image_paths) < max_images: add_btn = self.create_add_button(grid_widget); layout.addWidget(add_btn)
        layout.addStretch()

    def create_step3_page(self):
        page = QWidget(); layout = QVBoxLayout(page)
        layout.setAlignment(Qt.AlignCenter)
        self.status_label = QLabel("AI가 이미지를 생성하고 있습니다...")
        self.status_label.setStyleSheet("font-size: 16px; font-weight: 500; color: #495057;")
        layout.addWidget(self.status_label); return page

    def create_step4_page(self):
        page = QWidget(); layout = QVBoxLayout(page); title = QLabel("Step 3: 이미지 편집"); layout.addWidget(title); return page

    def create_step5_page(self):
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)
        page = QWidget()
        layout = QVBoxLayout(page)
        title = QLabel("Step 4: 최종 결과 확인")
        title.setStyleSheet("font-size: 20px; font-weight: 600; color: #495057;")
        layout.addWidget(title)
        group = QGroupBox("")
        self.results_grid_layout = QGridLayout(group)
        layout.addWidget(group)
        layout.addStretch(1); scroll_area.setWidget(page); return scroll_area

    def show_large_image(self, pixmap):
        dialog = QDialog(self)
        dialog.setWindowTitle("이미지 크게 보기")
        layout = QVBoxLayout(dialog); label = QLabel()
        label.setPixmap(pixmap.scaled(800, 800, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        layout.addWidget(label); dialog.exec_()

    @pyqtSlot(list)
    def on_final_save_completed(self, final_image_paths):
        while self.results_grid_layout.count():
            child = self.results_grid_layout.takeAt(0)
            if child.widget(): child.widget().deleteLater()
        for i, image_path in enumerate(final_image_paths):
            pixmap = QPixmap(image_path)
            if pixmap.isNull(): continue
            image_container = QFrame(); image_container.setFrameShape(QFrame.StyledPanel); container_layout = QVBoxLayout(image_container)
            image_label = QLabel(); image_label.setPixmap(pixmap.scaled(300, 300, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            image_label.setAlignment(Qt.AlignCenter); image_label.mousePressEvent = lambda event, p=pixmap: self.show_large_image(p); image_label.setCursor(Qt.PointingHandCursor)
            path_label = QLabel(os.path.basename(image_path)); path_label.setAlignment(Qt.AlignCenter); path_label.setWordWrap(True)
            container_layout.addWidget(image_label); container_layout.addWidget(path_label)
            row, col = i // 3, i % 3; self.results_grid_layout.addWidget(image_container, row, col)
        self.workflow_stack.setCurrentWidget(self.page4); self.update_workflow_ui(3)

    def update_workflow_ui(self, step_index):
        self.home_button.setVisible(step_index > 0 and step_index != 1)
        if step_index == 0:
            self.reset_step1_state()

        self.prev_button.setVisible(step_index > 0 and step_index != 2); self.next_button.setVisible(step_index != -1 and step_index != 3)
        for i, label in enumerate(self.sidebar_labels):
            is_current = (i == step_index); is_done = (i < step_index)
            if is_current: style = "color: white; background: rgba(255, 255, 255, 0.2); border-left: 3px solid #007bff;"
            elif is_done: style = "color: rgba(255, 255, 255, 0.8); background: rgba(255, 255, 255, 0.1); border-left: 3px solid #28a745;"
            else: style = "color: rgba(255, 255, 255, 0.6); background: rgba(255, 255, 255, 0.05);"
            label.setStyleSheet(f"QLabel {{ padding: 12px 15px; border-radius: 6px; margin: 3px 0; font-size: 16px; font-weight: {500 if is_current else 400}; {style} }}")
        is_settings_current = (step_index == -1)
        self.settings_button.setStyleSheet(f'''QPushButton {{ color: {"white" if is_settings_current else "#A0AEC0"}; background-color: { "rgba(255, 255, 255, 0.2)" if is_settings_current else "transparent"}; text-align: left; padding: 12px 15px; border:none; border-radius: 6px; font-size: 16px; font-weight: {500 if is_settings_current else 400}; }} QPushButton:hover {{ background-color: rgba(255, 255, 255, 0.1); }}''')
        
        self.prev_button.setEnabled(step_index > 0)
        if step_index == 4: # 분석 확인 step
            self.prev_button.setText("저장")
            self.prev_button.setEnabled(True)
        else:
            self.prev_button.setText("← 이전")

        is_last_step = step_index == len(self.sidebar_labels) - 1
        self.next_button.setEnabled(step_index < len(self.sidebar_labels) -1)
        if step_index == 0: self.next_button.setText("시작")
        elif step_index == 2: self.next_button.setText("최종 저장")
        elif is_last_step: self.next_button.setText("다시하기")
        else: self.next_button.setText("다음 →")

    def go_to_next_step(self):
        all_workflow_pages = [self.page1, self.page2, self.page3, self.page4, self.page5]
        try: current_workflow_step = all_workflow_pages.index(self.workflow_stack.currentWidget())
        except ValueError: current_workflow_step = -1
        if current_workflow_step == len(all_workflow_pages) - 1:
            self.workflow_stack.setCurrentWidget(self.page1); self.update_workflow_ui(0); return
        if current_workflow_step == 0:
            if not self.generation_mode: QMessageBox.warning(self, "오류", "생성 기능을 선택해주세요."); return
            main_images = self.main_product_group.grid_widget.image_paths
            if not main_images: QMessageBox.warning(self, "오류", "메인 상품 이미지를 추가해주세요."); return
            kwargs = {}
            if self.generation_mode == 'analyze_product':
                kwargs = {'image_paths': main_images, 'show_ui': False }
                self.workflow_stack.setCurrentWidget(self.page2); self.update_workflow_ui(1)
                self.prev_button.setVisible(False); self.next_button.setVisible(False)
                self.analysis_thread = AnalysisThread(self.analyzer, **kwargs); self.analysis_thread.analysis_ready.connect(self.on_analysis_ready); self.analysis_thread.error_occurred.connect(self.on_generation_error); self.analysis_thread.finished.connect(self.analysis_thread.deleteLater)
                self.loading_text_index = 0; self.update_loading_animation(); self.animation_timer.start(2000); self.analysis_thread.start(); return
            if self.generation_mode == 'change_attributes':
                if not self.instructions_input.toPlainText().strip(): QMessageBox.warning(self, "오류", "변경 지시사항을 입력해주세요."); return
                kwargs['instructions'] = self.instructions_input.toPlainText().strip().split('\n')
                kwargs['image_path'] = main_images[0]
            elif self.generation_mode == 'create_thumbnail':
                if not main_images: QMessageBox.warning(self, "오류", "메인 상품 이미지를 추가해주세요."); return
                image_path = main_images[0]
                metadata_path = os.path.join(self.meta_dir, os.path.splitext(os.path.basename(image_path))[0] + '.json')
                if not os.path.exists(metadata_path): QMessageBox.warning(self, "오류", f"메타데이터 파일이 없습니다: {metadata_path}"); return
                kwargs['image_path'] = image_path
                kwargs['metadata_path'] = metadata_path
            elif self.generation_mode in ['apply_style', 'replace_object']:
                if hasattr(self, 'reference_group') and not self.reference_group.grid_widget.image_paths: QMessageBox.warning(self, "오류", "레퍼런스 이미지를 추가해주세요."); return
                kwargs['product_image_path'] = main_images[0]
                kwargs['reference_image_paths'] = self.reference_group.grid_widget.image_paths
            elif self.generation_mode == 'create_scene':
                kwargs['product_image_paths'] = main_images
            self.workflow_stack.setCurrentWidget(self.page2); self.update_workflow_ui(1)
            self.prev_button.setVisible(False); self.next_button.setVisible(False)
            kwargs['show_ui'] = False
            self.image_thread = ImageGenerationThread(self.image_generator, self.generation_mode, **kwargs); self.image_thread.images_ready.connect(self.on_images_ready); self.image_thread.error_occurred.connect(self.on_generation_error); self.image_thread.finished.connect(self.image_thread.deleteLater)
            self.loading_text_index = 0; self.update_loading_animation(); self.animation_timer.start(2000); self.image_thread.start()
        elif current_workflow_step == 2:
            if hasattr(self, 'editor_widget'): self.editor_widget.open_final_save_dialog()

    def save_analysis_result(self):
        if self.analysis_results:
            for result in self.analysis_results:
                self.analyzer.save_result_json(result)
            QMessageBox.information(self, "저장 완료", "분석 결과가 성공적으로 저장되었습니다.")
        else:
            QMessageBox.warning(self, "저장 실패", "저장할 분석 결과가 없습니다.")

    def go_to_prev_step(self):
        current_widget = self.workflow_stack.currentWidget()
        all_workflow_pages = [self.page1, self.page2, self.page3, self.page4, self.page5]
        if current_widget in all_workflow_pages:
            current_workflow_step = all_workflow_pages.index(current_widget)
            if current_workflow_step == 4: # step 5 (분석 확인)
                self.save_analysis_result()
                return
            if current_workflow_step > 0:
                prev_step = current_workflow_step - 1
                self.workflow_stack.setCurrentWidget(all_workflow_pages[prev_step])
                self.update_workflow_ui(prev_step)
        else: self.workflow_stack.setCurrentWidget(self.page1); self.update_workflow_ui(0)

    def go_to_home_screen(self):
        self.workflow_stack.setCurrentWidget(self.page1)
        self.update_workflow_ui(0)

    def go_to_step(self, index):
        all_workflow_pages = [self.page1, self.page2, self.page3, self.page4, self.page5]
        if 0 <= index < len(all_workflow_pages):
            self.workflow_stack.setCurrentWidget(all_workflow_pages[index])
            self.update_workflow_ui(index)

    def reset_step1_state(self):
        self.generation_mode = None
        for btn in self.option_buttons.values():
            btn.setChecked(False)
        while self.dynamic_options_layout.count():
            child = self.dynamic_options_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

    def update_loading_animation(self):
        self.status_label.setText(self.loading_texts[self.loading_text_index]); self.loading_text_index = (self.loading_text_index + 1) % len(self.loading_texts)

    @pyqtSlot(str)
    def on_generation_error(self, error_message):
        self.animation_timer.stop(); QMessageBox.critical(self, "Generation Error", error_message); self.go_to_prev_step()

    @pyqtSlot(list)
    def on_images_ready(self, saved_image_paths):
        self.animation_timer.stop()
        if not saved_image_paths: QMessageBox.warning(self, "오류", "생성된 이미지가 없습니다."); self.go_to_prev_step(); return
        self.generated_image_path = saved_image_paths[0]
        if not hasattr(self, 'editor_widget'):
            from editor import AiEditorWidget
            old_page3 = self.page3; self.workflow_stack.removeWidget(old_page3); old_page3.deleteLater()
            self.editor_widget = AiEditorWidget(self); self.editor_widget.finalSaveCompleted.connect(self.on_final_save_completed)
            self.page3 = self.editor_widget
            self.workflow_stack.insertWidget(2, self.editor_widget)
        self.editor_widget.load_image(self.generated_image_path); self.all_generated_images = saved_image_paths
        self.workflow_stack.setCurrentWidget(self.editor_widget); self.update_workflow_ui(2); self.next_button.setText("결과 저장")

def main():
    app = QApplication(sys.argv)
    font = QFont("Noto Sans KR", 10); app.setFont(font); app.setStyle('Fusion')
    ex = AIGeneratorApp(); ex.show(); sys.exit(app.exec_())

if __name__ == '__main__':
    main()