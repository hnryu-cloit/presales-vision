import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLineEdit, QLabel, QTextEdit, QFormLayout, 
    QGroupBox, QStackedWidget, QFrame, QGridLayout, QFileDialog, QScrollArea, QCheckBox, QMessageBox
)
from PyQt5.QtGui import QFont, QPixmap
from PyQt5.QtCore import Qt, QThread, pyqtSignal, pyqtSlot, QTimer

from common.gemini import Gemini
from generate import ImageGenerator


class ImageGenerationThread(QThread):
    """백그라운드에서 이미지 생성을 처리하는 스레드"""
    images_ready = pyqtSignal(list)

    def __init__(self, gemini_client, prompt, image_files):
        super().__init__()
        self.gemini_client = gemini_client
        self.prompt = prompt
        self.image_files = image_files

    def run(self):
        try:
            image_parts, _ = self.gemini_client.call_image_generator(
                prompt=self.prompt,
                image_files=self.image_files
            )
            self.images_ready.emit(image_parts)
        except Exception as e:
            print(f"Image generation failed: {e}")
            self.images_ready.emit([]) # 실패 시 빈 리스트 전달


class AIGeneratorApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Copyright © 2025 ITCEN CLOIT All rights reserved.")
        self.setGeometry(100, 100, 1200, 800)

        # 전체 애플리케이션 스타일 설정
        self.setStyleSheet("""
            QMainWindow {
                background: #f8f9fa;
            }
        """)

        self.main_widget = QWidget()
        self.setCentralWidget(self.main_widget)
        self.main_layout = QHBoxLayout(self.main_widget)
        self.main_layout.setSpacing(0)
        self.main_layout.setContentsMargins(0,0,0,0)

        self.keyword_widgets = {}
        self.final_prompt = ""
        self.product_image_path = None
        self.gemini_client = Gemini()
        self.image_generator = ImageGenerator()

        # 로딩 애니메이션 설정
        self.loading_text_index = 0
        self.loading_texts = [
            "AI 모델에 연결하는 중...",
            "프롬프트 분석 및 이미지 구상 중...",
            "메인 이미지 생성 중...",
            "배경 및 소품 렌더링 중...",
            "최종 결과 조합 중..."
        ]
        self.animation_timer = QTimer(self)
        self.animation_timer.timeout.connect(self.update_loading_animation)

        self.init_ui()

    def init_ui(self):
        self.create_sidebar()
        self.create_main_content_area()
        
        self.stacked_widget.setCurrentIndex(0)
        self.update_workflow_ui(0)

    def create_sidebar(self):
        sidebar = QFrame()
        sidebar.setFixedWidth(250)
        sidebar.setStyleSheet("""
            QFrame {
                background: #343a40;
                border: none;
                border-right: 1px solid #dee2e6;
            }
        """)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(20, 30, 20, 30)
        sidebar_layout.setSpacing(20)

        title_label = QLabel("CEN AI STUDIO")
        title_label.setFont(QFont("Apple SD Gothic Neo", 18, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("""
            QLabel {
                color: white;
                font-weight: bold;
                margin-bottom: 10px;
                padding: 10px;
            }
        """)

        self.sidebar_labels = [
            QLabel("Step 1: 키워드 입력"),
            QLabel("Step 2: 프롬프트 검토"),
            QLabel("Step 3: 이미지 생성"),
            QLabel("Step 4: 결과 확인")
        ]

        sidebar_layout.addWidget(title_label)
        sidebar_layout.addSpacing(30)

        for i, label in enumerate(self.sidebar_labels):
            label.setFont(QFont("Apple SD Gothic Neo", 12, QFont.Medium))
            label.setAlignment(Qt.AlignCenter)
            label.setWordWrap(True)
            label.setStyleSheet("""
                QLabel {
                    color: rgba(255, 255, 255, 0.9);
                    padding: 12px 15px;
                    border-radius: 6px;
                    background: rgba(255, 255, 255, 0.05);
                    margin: 3px 0;
                    font-weight: 400;
                }
            """)
            sidebar_layout.addWidget(label)

        sidebar_layout.addStretch(1)
        self.main_layout.addWidget(sidebar)

    def create_main_content_area(self):
        main_content = QWidget()
        main_content.setStyleSheet("""
            QWidget {
                background: #f8f9fa;
            }
        """)
        main_content_layout = QVBoxLayout(main_content)
        main_content_layout.setContentsMargins(30, 30, 30, 30)
        main_content_layout.setSpacing(20)

        self.stacked_widget = QStackedWidget()
        self.page1 = self.create_step1_page()
        self.page2 = self.create_step2_page()
        self.page3 = self.create_step3_page()
        self.page4 = self.create_step4_page()
        self.stacked_widget.addWidget(self.page1)
        self.stacked_widget.addWidget(self.page2)
        self.stacked_widget.addWidget(self.page3)
        self.stacked_widget.addWidget(self.page4)
        main_content_layout.addWidget(self.stacked_widget)

        nav_layout = QHBoxLayout()
        nav_layout.addStretch(1)
        self.prev_button = QPushButton("← 이전")
        self.next_button = QPushButton("다음 →")

        for btn in [self.prev_button, self.next_button]:
            btn.setStyleSheet("""
                QPushButton {
                    background: #007bff;
                    color: white;
                    border: none;
                    border-radius: 6px;
                    padding: 10px 20px;
                    font-size: 13px;
                    font-weight: 500;
                    min-width: 90px;
                }
                QPushButton:hover {
                    background: #0056b3;
                }
                QPushButton:pressed {
                    background: #004085;
                }
                QPushButton:disabled {
                    background: #6c757d;
                    color: #dee2e6;
                }
            """)

        self.prev_button.clicked.connect(self.go_to_prev_step)
        self.next_button.clicked.connect(self.go_to_next_step)
        nav_layout.addWidget(self.prev_button)
        nav_layout.addSpacing(15)
        nav_layout.addWidget(self.next_button)
        main_content_layout.addLayout(nav_layout)

        self.main_layout.addWidget(main_content)

    def create_step1_page(self):
        # 스크롤 영역 생성
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)
        scroll_area.setStyleSheet("QScrollArea { background: transparent; }")

        page = QWidget()
        page.setStyleSheet("""
            QWidget {
                background: transparent;
            }
        """)
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 20, 0, 0)
        layout.setSpacing(25)

        # 페이지 타이틀
        title = QLabel("AI 이미지 생성 - 키워드 입력")
        title.setStyleSheet("""
            QLabel {
                font-size: 20px;
                font-weight: 600;
                color: #495057;
                margin-bottom: 15px;
                padding-bottom: 8px;
                border-bottom: 2px solid #e9ecef;
            }
        """)
        layout.addWidget(title)

        group_box = QGroupBox("생성할 이미지의 핵심 키워드를 입력하세요")
        group_box.setStyleSheet("""
            QGroupBox {
                border: 1px solid #dee2e6;
                border-radius: 8px;
                margin-top: 10px;
                padding: 15px;
                font-weight: 500;
                font-size: 13px;
                color: #495057;
                background: white;
            }
            QGroupBox::title {
                background: transparent;
                padding: 0 8px;
                color: #495057;
            }
        """)
        form_layout = QFormLayout()
        form_layout.setSpacing(15)

        keywords_to_ask = {
            "product": "제품"
        }

        # 제품명 입력
        self.create_input_row("제품명*", "product", form_layout, is_required=True)

        # 주변 사물/소품
        self.create_input_row("주변 사물/소품", "props", form_layout)

        # 배경/표면
        self.create_input_row("배경/표면", "background", form_layout)

        # 분위기/조명
        self.create_input_row("분위기/조명", "mood", form_layout)

        group_box.setLayout(form_layout)
        layout.addWidget(group_box)

        # 레퍼런스 이미지 섹션 - 다른 섹션과 동일한 스타일
        ref_group = QGroupBox("레퍼런스 이미지 (선택사항)")
        ref_group.setStyleSheet("""
            QGroupBox {
                border: 1px solid #dee2e6;
                border-radius: 8px;
                margin-top: 10px;
                padding: 15px;
                font-weight: 500;
                font-size: 13px;
                color: #495057;
                background: white;
            }
            QGroupBox::title {
                background: transparent;
                padding: 0 8px;
                color: #495057;
            }
        """)
        ref_layout = QVBoxLayout(ref_group)

        # 파일 목록 표시 영역
        ref_grid_container = QWidget()
        ref_grid_layout = QVBoxLayout(ref_grid_container)
        ref_grid_layout.setContentsMargins(0, 0, 0, 0)

        ref_grid_label = QLabel("이미지 등록(최대 5개):")
        ref_grid_label.setStyleSheet("color: #495057; font-size: 12px; font-weight: 500;")
        ref_grid_layout.addWidget(ref_grid_label)

        # 스크롤 영역
        ref_scroll_area = QScrollArea()
        ref_scroll_area.setFrameShape(QFrame.NoFrame)
        ref_scroll_area.setWidgetResizable(True)
        ref_scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        ref_scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        ref_scroll_area.setFixedHeight(100)

        self.reference_images_widget = QWidget()
        self.reference_layout = self.create_image_grid_layout()
        self.reference_images_widget.setLayout(self.reference_layout)

        ref_scroll_area.setWidget(self.reference_images_widget)
        ref_grid_layout.addWidget(ref_scroll_area)

        ref_layout.addWidget(ref_grid_container)
        layout.addWidget(ref_group)

        # 속성 설정
        setattr(self.reference_images_widget, 'image_paths', [])
        setattr(self.reference_images_widget, 'max_images', 5)
        self.reference_images = []

        self.update_reference_grid()

        # 옵션 설정 섹션
        options_group = QGroupBox("생성 옵션")
        options_group.setStyleSheet("""
            QGroupBox {
                border: 1px solid #dee2e6;
                border-radius: 8px;
                margin-top: 10px;
                padding: 15px;
                font-weight: 500;
                font-size: 13px;
                color: #495057;
                background: white;
            }
            QGroupBox::title {
                background: transparent;
                padding: 0 8px;
                color: #495057;
            }
        """)
        options_layout = QVBoxLayout(options_group)

        # 옵션 버튼들
        option_buttons_layout = QHBoxLayout()

        self.btn_style_transfer = QPushButton("🎨 스타일(속성) 변경")
        self.btn_object_replace = QPushButton("🔄 객체 교체")
        self.btn_scene_create = QPushButton("❤️ 썸네일 생성")
        self.btn_custom_prompt = QPushButton("✏️ 기타 사용자 입력")

        option_buttons = [self.btn_style_transfer, self.btn_object_replace, self.btn_scene_create, self.btn_custom_prompt]
        for btn in option_buttons:
            btn.setStyleSheet("""
                QPushButton {
                    background: #e9ecef;
                    color: #495057;
                    border: 1px solid #ced4da;
                    border-radius: 4px;
                    padding: 6px 12px;
                    font-size: 11px;
                    font-weight: 500;
                    min-width: 80px;
                }
                QPushButton:hover {
                    background: #dee2e6;
                }
                QPushButton:checked {
                    background: #007bff;
                    color: white;
                    border-color: #007bff;
                }
            """)
            btn.setCheckable(True)
            option_buttons_layout.addWidget(btn)

        self.btn_custom_prompt.clicked.connect(self.toggle_custom_prompt)
        option_buttons_layout.addStretch()

        # 커스텀 프롬프트 입력 영역
        self.custom_prompt_widget = QWidget()
        custom_prompt_layout = QVBoxLayout(self.custom_prompt_widget)
        custom_prompt_layout.setContentsMargins(0, 10, 0, 0)

        custom_label = QLabel("사용자 정의 프롬프트:")
        custom_label.setStyleSheet("color: #495057; font-weight: 500;")

        self.custom_prompt_input = QTextEdit()
        self.custom_prompt_input.setFixedHeight(80)
        self.custom_prompt_input.setPlaceholderText("원하는 이미지 생성 프롬프트를 직접 입력하세요...")
        self.custom_prompt_input.setStyleSheet("""
            QTextEdit {
                border: 1px solid #ced4da;
                border-radius: 4px;
                padding: 8px;
                font-size: 12px;
                background: white;
            }
            QTextEdit:focus {
                border-color: #007bff;
                outline: none;
            }
        """)

        custom_prompt_layout.addWidget(custom_label)
        custom_prompt_layout.addWidget(self.custom_prompt_input)
        self.custom_prompt_widget.setVisible(False)

        options_layout.addLayout(option_buttons_layout)
        options_layout.addWidget(self.custom_prompt_widget)
        layout.addWidget(options_group)

        layout.addStretch(1)

        # 스크롤 영역에 페이지 설정
        scroll_area.setWidget(page)
        return scroll_area

    def create_step2_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 20, 0, 0)
        layout.setSpacing(25)

        # 페이지 타이틀
        title = QLabel("AI 이미지 생성 - 프롬프트 검토")
        title.setStyleSheet("""
            QLabel {
                font-size: 20px;
                font-weight: 600;
                color: #495057;
                margin-bottom: 15px;
                padding-bottom: 8px;
                border-bottom: 2px solid #e9ecef;
            }
        """)
        layout.addWidget(title)

        group_box = QGroupBox("AI가 생성한 프롬프트")
        group_box.setStyleSheet("""
            QGroupBox {
                border: 1px solid #dee2e6;
                border-radius: 8px;
                margin-top: 10px;
                padding: 15px;
                font-weight: 500;
                font-size: 13px;
                color: #495057;
                background: white;
            }
            QGroupBox::title {
                background: transparent;
                padding: 0 8px;
                color: #495057;
            }
        """)
        group_layout = QVBoxLayout(group_box)

        self.prompt_editor = QTextEdit()
        self.prompt_editor.setStyleSheet("""
            QTextEdit {
                border: 1px solid #ced4da;
                border-radius: 4px;
                padding: 12px;
                font-size: 12px;
                font-family: 'Apple SD Gothic Neo', 'Malgun Gothic', sans-serif;
                background: white;
                line-height: 1.4;
            }
            QTextEdit:focus {
                border-color: #007bff;
                outline: none;
            }
        """)
        self.prompt_editor.setMinimumHeight(200)

        group_layout.addWidget(self.prompt_editor)
        layout.addWidget(group_box)
        layout.addStretch(1)
        return page

    def create_step3_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 20, 0, 0)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(30)

        # 로딩 아이콘 영역
        loading_container = QWidget()
        loading_container.setFixedSize(150, 150)
        loading_container.setStyleSheet("""
            QWidget {
                background: #6c757d;
                border-radius: 75px;
            }
        """)

        loading_layout = QVBoxLayout(loading_container)
        loading_icon = QLabel("⏳")
        loading_icon.setAlignment(Qt.AlignCenter)
        loading_icon.setStyleSheet("""
            QLabel {
                background: transparent;
                font-size: 40px;
                color: white;
            }
        """)
        loading_layout.addWidget(loading_icon)

        self.status_label = QLabel("AI가 이미지를 생성하고 있습니다...")
        self.status_label.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: 500;
                color: #495057;
                text-align: center;
                padding: 15px;
                background: white;
                border-radius: 6px;
                border: 1px solid #dee2e6;
            }
        """)
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setWordWrap(True)

        layout.addWidget(loading_container, 0, Qt.AlignCenter)
        layout.addWidget(self.status_label)
        layout.addStretch(1)
        return page

    def create_step4_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 20, 0, 0)
        layout.setSpacing(25)

        # 페이지 타이틀
        title = QLabel("AI 이미지 생성 - 결과 확인")
        title.setStyleSheet("""
            QLabel {
                font-size: 20px;
                font-weight: 600;
                color: #495057;
                margin-bottom: 15px;
                padding-bottom: 8px;
                border-bottom: 2px solid #e9ecef;
            }
        """)
        layout.addWidget(title)

        group = QGroupBox("생성된 이미지 결과")
        group.setStyleSheet("""
            QGroupBox {
                border: 1px solid #dee2e6;
                border-radius: 8px;
                margin-top: 10px;
                padding: 15px;
                font-weight: 500;
                font-size: 13px;
                color: #495057;
                background: white;
            }
            QGroupBox::title {
                background: transparent;
                padding: 0 8px;
                color: #495057;
            }
        """)
        self.grid_layout = QGridLayout(group)
        self.grid_layout.setSpacing(20)
        layout.addWidget(group)
        layout.addStretch(1)
        return page

    def create_input_row(self, title, key, form_layout, is_required=False):
        """단순화된 입력 행 생성"""
        
        title_label = QLabel(title)
        if is_required:
            title_label.setStyleSheet("color: red; font-weight: bold;")

        container_widget = QWidget()
        main_layout = QVBoxLayout(container_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(10)

        # 입력란
        line_edit = QLineEdit()
        line_edit.setStyleSheet("""
            QLineEdit {
                border: 1px solid #ced4da;
                border-radius: 4px;
                padding: 8px 12px;
                font-size: 12px;
                background: white;
            }
            QLineEdit:focus {
                border-color: #007bff;
                outline: none;
            }
        """)

        # 파일 목록 표시 영역
        grid_container = QWidget()
        grid_layout = QVBoxLayout(grid_container)
        grid_layout.setContentsMargins(0, 0, 0, 0)

        grid_label = QLabel(f"이미지 등록(최대 3개):")
        grid_label.setStyleSheet("color: #495057; font-size: 12px; font-weight: 500;")
        grid_layout.addWidget(grid_label)

        # 스크롤 영역
        scroll_area = QScrollArea()
        scroll_area.setFrameShape(QFrame.NoFrame)
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setFixedHeight(100)

        image_grid_widget = QWidget()
        image_grid_layout = self.create_image_grid_layout()
        image_grid_widget.setLayout(image_grid_layout)

        scroll_area.setWidget(image_grid_widget)
        grid_layout.addWidget(scroll_area)

        main_layout.addWidget(line_edit)
        main_layout.addWidget(grid_container)

        form_layout.addRow(title_label, container_widget)

        # 속성 설정
        setattr(image_grid_widget, 'image_paths', [])
        setattr(image_grid_widget, 'max_images', 3)
        setattr(image_grid_widget, 'input_widget', line_edit)

        # 위젯 저장
        self.keyword_widgets[key] = line_edit
        if not hasattr(self, 'file_widgets'):
            self.file_widgets = {}
        self.file_widgets[key] = image_grid_widget

        self.update_image_grid(image_grid_widget)

        return image_grid_widget

    def create_image_grid_layout(self):
        """이미지 그리드 레이아웃 생성"""
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        layout.addStretch()
        return layout

    def create_image_card(self, image_path, grid_widget):
        """이미지 카드 생성"""
        card = QWidget()
        card.setFixedSize(80, 80)
        card.setStyleSheet("""
            QWidget {
                border: 2px solid #DDD;
                border-radius: 5px;
                background-color: white;
            }
            QWidget:hover {
                border-color: #A23B72;
            }
        """)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(0)

        img_label = QLabel()
        img_label.setFixedSize(76, 76)
        img_label.setAlignment(Qt.AlignCenter)
        img_label.setStyleSheet("border: none; background-color: #F8F8F8;")
        layout.addWidget(img_label)

        pixmap = QPixmap(image_path)
        if not pixmap.isNull():
            scaled_pixmap = pixmap.scaled(img_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            img_label.setPixmap(scaled_pixmap)
        else:
            img_label.setText("이미지\n오류")
            img_label.setStyleSheet("border: none; background-color: #F8F8F8; color: #D00; font-size: 10px;")

        # 삭제 버튼
        delete_btn = QPushButton("✕", card)
        delete_btn.setFixedSize(20, 20)
        delete_btn.move(img_label.width() - delete_btn.width() - 2, 2)
        delete_btn.setToolTip("이미지 삭제")
        delete_btn.setStyleSheet("""
            QPushButton {
                border: none;
                background-color: rgba(255, 0, 0, 0.8);
                color: white;
                font-weight: bold;
                font-size: 12px;
                border-radius: 10px;
            }
            QPushButton:hover {
                background-color: rgba(255, 0, 0, 1.0);
            }
        """)
        delete_btn.clicked.connect(lambda: self.remove_image_card(image_path, grid_widget))

        return card

    def create_add_button(self, grid_widget):
        """추가 버튼 생성"""
        add_card = QWidget()
        add_card.setFixedSize(80, 80)
        add_card.setStyleSheet("""
            QWidget {
                border: 2px dashed #AAA;
                border-radius: 5px;
                background-color: #F8F8F8;
            }
            QWidget:hover {
                border-color: #A23B72;
                background-color: #F0F0F0;
            }
        """)

        layout = QVBoxLayout(add_card)
        layout.setContentsMargins(0, 0, 0, 0)

        add_label = QLabel("+")
        add_label.setAlignment(Qt.AlignCenter)
        add_label.setStyleSheet("""
            border: none;
            background-color: transparent;
            color: #888;
            font-size: 24px;
            font-weight: bold;
        """)

        add_card.mousePressEvent = lambda event: self.add_images_to_grid(grid_widget)
        layout.addWidget(add_label)

        return add_card

    def add_images_to_grid(self, grid_widget):
        """그리드에 이미지 추가"""
        max_images = getattr(grid_widget, 'max_images', 3)
        files, _ = QFileDialog.getOpenFileNames(self, "이미지 선택", "", "Image files (*.png *.jpg *.jpeg)")
        if files:
            current_count = len(grid_widget.image_paths)
            available_slots = max_images - current_count
            if available_slots <= 0:
                QMessageBox.warning(self, "최대 개수 초과", f"최대 {max_images}개까지만 등록할 수 있습니다.")
                return
            if len(files) > available_slots:
                files = files[:available_slots]
                QMessageBox.information(self, "일부 파일 선택", f"최대 개수 제한으로 {available_slots}개 파일만 선택되었습니다.")
            grid_widget.image_paths.extend(files)

        self.update_image_grid(grid_widget)

    def remove_image_card(self, image_path, grid_widget):
        """이미지 카드 제거"""
        if image_path in grid_widget.image_paths:
            grid_widget.image_paths.remove(image_path)
            self.update_image_grid(grid_widget)

    def update_image_grid(self, grid_widget):
        """이미지 그리드 업데이트"""
        layout = grid_widget.layout()
        max_images = getattr(grid_widget, 'max_images', 3)

        # 기존 위젯 제거
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        # 이미지 카드 추가
        for image_path in grid_widget.image_paths:
            card = self.create_image_card(image_path, grid_widget)
            layout.addWidget(card)

        # 추가 버튼 (최대 개수 미만인 경우만)
        if len(grid_widget.image_paths) < max_images:
            add_btn = self.create_add_button(grid_widget)
            layout.addWidget(add_btn)

        layout.addStretch()

    def update_reference_grid(self):
        """레퍼런스 이미지 그리드 업데이트"""
        layout = self.reference_layout
        max_images = getattr(self.reference_images_widget, 'max_images', 5)

        # 기존 위젯 제거
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        # reference_images를 reference_images_widget.image_paths에 동기화
        self.reference_images_widget.image_paths = self.reference_images.copy()

        # 이미지 카드 추가
        for image_path in self.reference_images_widget.image_paths:
            card = self.create_image_card(image_path, self.reference_images_widget)
            layout.addWidget(card)

        # 추가 버튼 (최대 개수 미만인 경우만)
        if len(self.reference_images_widget.image_paths) < max_images:
            add_btn = self.create_add_button(self.reference_images_widget)
            layout.addWidget(add_btn)

        layout.addStretch()

    def show_image_popup(self, image_path):
        """이미지 팝업창 표시"""


        dialog = QDialog(self)
        dialog.setWindowTitle("이미지 미리보기")
        dialog.setFixedSize(600, 600)

        layout = QVBoxLayout(dialog)

        img_label = QLabel()
        img_label.setAlignment(Qt.AlignCenter)

        pixmap = QPixmap(image_path)
        if not pixmap.isNull():
            scaled_pixmap = pixmap.scaled(550, 550, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            img_label.setPixmap(scaled_pixmap)
        else:
            img_label.setText("이미지를 불러올 수 없습니다")

        layout.addWidget(img_label)
        dialog.exec_()

    def select_image(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "이미지 선택", "", "Image Files (*.png *.jpg *.jpeg *.bmp)")
        if file_name:
            self.product_image_path = file_name
            self.lbl_image_path.setText(file_name.split('/')[-1])
            self.lbl_image_path.setStyleSheet("""
                QLabel {
                    color: #155724;
                    font-size: 12px;
                    font-weight: 500;
                    padding: 10px;
                    background: #d4edda;
                    border-radius: 4px;
                    border: 1px solid #c3e6cb;
                }
            """)

            # 이미지 미리보기 표시
            pixmap = QPixmap(file_name)
            if not pixmap.isNull():
                scaled_pixmap = pixmap.scaled(self.image_preview.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.image_preview.setPixmap(scaled_pixmap)
                self.image_preview.setStyleSheet("""
                    QLabel {
                        border: 2px solid #28a745;
                        border-radius: 8px;
                        background: white;
                    }
                """)

    def add_reference_images(self):
        """레퍼런스 이미지 추가"""
        files, _ = QFileDialog.getOpenFileNames(self, "레퍼런스 이미지 선택", "", "Image Files (*.png *.jpg *.jpeg *.bmp)")
        if files:
            for file_path in files:
                if file_path not in self.reference_images:
                    self.reference_images.append(file_path)
                    self.add_reference_thumbnail(file_path)

    def add_reference_thumbnail(self, image_path):
        """레퍼런스 이미지 썸네일 추가"""
        thumbnail_widget = QWidget()
        thumbnail_widget.setFixedSize(80, 80)
        thumbnail_widget.setStyleSheet("""
            QWidget {
                border: 2px solid #DDD;
                border-radius: 5px;
                background: white;
            }
            QWidget:hover {
                border-color: #A23B72;
            }
        """)

        layout = QVBoxLayout(thumbnail_widget)
        layout.setContentsMargins(2, 2, 2, 2)

        img_label = QLabel()
        img_label.setFixedSize(76, 76)
        img_label.setAlignment(Qt.AlignCenter)
        img_label.setStyleSheet("border: none; background-color: #F8F8F8;")

        pixmap = QPixmap(image_path)
        if not pixmap.isNull():
            scaled_pixmap = pixmap.scaled(img_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            img_label.setPixmap(scaled_pixmap)
        else:
            img_label.setText("이미지\n오류")
            img_label.setStyleSheet("border: none; background-color: #F8F8F8; color: #D00; font-size: 10px;")

        # 미리보기 버튼
        preview_btn = QPushButton("👁", thumbnail_widget)
        preview_btn.setFixedSize(20, 20)
        preview_btn.move(2, 2)
        preview_btn.setToolTip("미리보기")
        preview_btn.setStyleSheet("""
            QPushButton {
                border: none;
                background-color: rgba(0, 123, 255, 0.8);
                color: white;
                font-weight: bold;
                font-size: 12px;
                border-radius: 10px;
            }
            QPushButton:hover {
                background-color: rgba(0, 123, 255, 1.0);
            }
        """)
        preview_btn.clicked.connect(lambda: self.show_image_popup(image_path))

        # 삭제 버튼
        del_btn = QPushButton("✕", thumbnail_widget)
        del_btn.setFixedSize(20, 20)
        del_btn.move(img_label.width() - del_btn.width() - 2, 2)
        del_btn.setToolTip("이미지 삭제")
        del_btn.setStyleSheet("""
            QPushButton {
                border: none;
                background-color: rgba(255, 0, 0, 0.8);
                color: white;
                font-weight: bold;
                font-size: 12px;
                border-radius: 10px;
            }
            QPushButton:hover {
                background-color: rgba(255, 0, 0, 1.0);
            }
        """)
        del_btn.clicked.connect(lambda: self.remove_reference_image(image_path, thumbnail_widget))

        layout.addWidget(img_label)
        self.reference_layout.addWidget(thumbnail_widget)

    def remove_reference_image(self, image_path, widget):
        """레퍼런스 이미지 제거"""
        if image_path in self.reference_images:
            self.reference_images.remove(image_path)
        widget.deleteLater()

    def toggle_custom_prompt(self):
        """커스텀 프롬프트 입력 영역 토글"""
        if self.btn_custom_prompt.isChecked():
            self.custom_prompt_widget.setVisible(True)
            # 다른 옵션 버튼들 해제
            self.btn_style_transfer.setChecked(False)
            self.btn_object_replace.setChecked(False)
            self.btn_scene_create.setChecked(False)
        else:
            self.custom_prompt_widget.setVisible(False)

    def update_workflow_ui(self, step_index):
        for i, label in enumerate(self.sidebar_labels):
            if i == step_index:
                label.setStyleSheet("""
                    QLabel {
                        color: white;
                        padding: 12px 15px;
                        border-radius: 6px;
                        background: rgba(255, 255, 255, 0.2);
                        margin: 3px 0;
                        font-weight: 500;
                        border-left: 3px solid #007bff;
                    }
                """)
            elif i < step_index:
                label.setStyleSheet("""
                    QLabel {
                        color: rgba(255, 255, 255, 0.8);
                        padding: 12px 15px;
                        border-radius: 6px;
                        background: rgba(255, 255, 255, 0.1);
                        margin: 3px 0;
                        font-weight: 400;
                        border-left: 3px solid #28a745;
                    }
                """)
            else:
                label.setStyleSheet("""
                    QLabel {
                        color: rgba(255, 255, 255, 0.6);
                        padding: 12px 15px;
                        border-radius: 6px;
                        background: rgba(255, 255, 255, 0.05);
                        margin: 3px 0;
                        font-weight: 400;
                    }
                """)

        self.prev_button.setEnabled(step_index > 0)
        self.next_button.setEnabled(step_index < self.stacked_widget.count() - 1)

        if step_index == self.stacked_widget.count() - 1:
            self.next_button.setText("✓ 완료")
        else:
            self.next_button.setText("다음 →")

    def go_to_next_step(self):
        current_index = self.stacked_widget.currentIndex()

        if current_index == 0:
            if not self.file_widgets['product'].image_paths:
                QMessageBox.warning(self, "이미지 필요", "제품 이미지를 선택해야 다음 단계로 진행할 수 있습니다.")
                return
            keywords = {key: widget.text() for key, widget in self.keyword_widgets.items()}
            generated_prompt = self.generate_prompt_with_ai(keywords)
            self.prompt_editor.setText(generated_prompt)

        elif current_index == 1:
            self.final_prompt = self.prompt_editor.toPlainText()
            self.stacked_widget.setCurrentIndex(2)
            self.update_workflow_ui(2)

            # 선택된 생성 옵션에 따라 이미지 파일 목록 구성
            generation_mode = "basic"
            if self.btn_style_transfer.isChecked():
                generation_mode = "style_transfer"
            elif self.btn_object_replace.isChecked():
                generation_mode = "object_replace"
            elif self.btn_scene_create.isChecked():
                generation_mode = "scene_create"

            image_files = []
            main_product_images = self.file_widgets['product'].image_paths
            reference_images = self.reference_images_widget.image_paths

            if generation_mode in ["style_transfer", "object_replace"]:
                image_files.extend(main_product_images)
                image_files.extend(reference_images)
            elif generation_mode == "scene_create":
                for key, widget in self.file_widgets.items():
                    image_files.extend(widget.image_paths)
            else: # basic or custom
                image_files.extend(main_product_images)

            self.image_thread = ImageGenerationThread(self.gemini_client, self.final_prompt, image_files)
            self.image_thread.images_ready.connect(self.on_images_ready)
            self.image_thread.finished.connect(self.image_thread.deleteLater)
            
            self.loading_text_index = 0
            self.update_loading_animation()
            self.animation_timer.start(2000) # 2초마다 텍스트 변경
            self.image_thread.start()
            return # 스레드 시작 후 UI는 대기 

        if current_index < self.stacked_widget.count() - 1:
            self.stacked_widget.setCurrentIndex(current_index + 1)
            self.update_workflow_ui(current_index + 1)

    def go_to_prev_step(self):
        current_index = self.stacked_widget.currentIndex()
        if current_index > 0:
            self.stacked_widget.setCurrentIndex(current_index - 1)
            self.update_workflow_ui(current_index - 1)

    def generate_prompt_with_ai(self, keywords):
        # 커스텀 프롬프트가 선택되고 입력된 경우
        if self.btn_custom_prompt.isChecked() and self.custom_prompt_input.toPlainText().strip():
            return self.custom_prompt_input.toPlainText().strip()

        # 선택된 생성 옵션 확인
        generation_mode = "basic"
        if self.btn_style_transfer.isChecked():
            generation_mode = "style_transfer"
        elif self.btn_object_replace.isChecked():
            generation_mode = "object_replace"
        elif self.btn_scene_create.isChecked():
            generation_mode = "scene_create"

        # image_generator를 사용하여 프롬프트 생성
        generated_prompt = self.image_generator.create_prompt(generation_mode, keywords)
        return generated_prompt

    def update_loading_animation(self):
        self.status_label.setText(self.loading_texts[self.loading_text_index])
        self.loading_text_index = (self.loading_text_index + 1) % len(self.loading_texts)

    @pyqtSlot(list)
    def on_images_ready(self, image_parts):
        self.animation_timer.stop()
        
        # Clear previous images
        while self.grid_layout.count():
            child = self.grid_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        # Display new images
        for i, image_data in enumerate(image_parts):
            pixmap = QPixmap()
            pixmap.loadFromData(image_data.data)

            # 이미지 컨테이너
            image_container = QWidget()
            image_container.setStyleSheet("""
                QWidget {
                    background: white;
                    border: 1px solid #dee2e6;
                    border-radius: 8px;
                    padding: 8px;
                }
                QWidget:hover {
                    border-color: #007bff;
                    box-shadow: 0 2px 8px rgba(0, 123, 255, 0.2);
                }
            """)
            container_layout = QVBoxLayout(image_container)
            container_layout.setContentsMargins(8, 8, 8, 8)

            image_label = QLabel()
            image_label.setPixmap(pixmap.scaled(200, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            image_label.setAlignment(Qt.AlignCenter)
            image_label.setStyleSheet("""
                QLabel {
                    border: 1px solid #e9ecef;
                    border-radius: 4px;
                    background: #f8f9fa;
                }
            """)

            # 이미지 번호 라벨
            number_label = QLabel(f"결과 {i+1}")
            number_label.setAlignment(Qt.AlignCenter)
            number_label.setStyleSheet("""
                QLabel {
                    font-weight: 500;
                    color: #6c757d;
                    margin-top: 6px;
                    border: none;
                    background: transparent;
                    font-size: 12px;
                }
            """)

            container_layout.addWidget(image_label)
            container_layout.addWidget(number_label)

            row = i // 2
            col = i % 2
            self.grid_layout.addWidget(image_container, row, col)

        self.stacked_widget.setCurrentIndex(3)
        self.update_workflow_ui(3)


if __name__ == '__main__':
    app = QApplication(sys.argv)

    # 폰트 설정 (나눔고딕을 우선으로 시도)
    font = QFont("NanumGothic", 10)
    if font.family() != "NanumGothic":
        # 나눔고딕이 없으면 맑은 고딕으로 대체
        font = QFont("Malgun Gothic", 9)  # Windows
    
    app.setFont(font)


    # 애플리케이션 스타일 설정
    app.setStyle('Fusion')

    ex = AIGeneratorApp()
    ex.show()
    sys.exit(app.exec_())
