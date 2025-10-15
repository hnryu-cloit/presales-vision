import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLineEdit, QLabel, QTextEdit, QFormLayout,
    QGroupBox, QStackedWidget, QFrame, QGridLayout, QFileDialog, QScrollArea, QDialog, QMessageBox
)
from PyQt5.QtGui import QFont, QPixmap
from PyQt5.QtCore import Qt, QThread, pyqtSignal, pyqtSlot, QTimer

from common.gemini import Gemini
from generate import ImageGenerator


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
            if self.mode == "change_attributes":
                result = self.generator.change_attributes(**self.kwargs)
            elif self.mode == "create_thumbnail":
                result = self.generator.create_thumbnail_with_metadata(**self.kwargs)
            elif self.mode == "apply_style":
                result = self.generator.apply_style_from_reference(**self.kwargs)
            elif self.mode == "replace_object":
                result = self.generator.replace_object_in_reference(**self.kwargs)
            elif self.mode == "create_scene":
                result = self.generator.create_beauty_scene(**self.kwargs)
            else:
                self.error_occurred.emit(f"Unknown generation mode: {self.mode}")
                return

            self.images_ready.emit(result)
        except Exception as e:
            self.error_occurred.emit(f"An error occurred during image generation: {e}")


class AIGeneratorApp(QMainWindow):
    FEATURE_TOOLTIPS = {
        "속성 변경": {
            "short": "촬영 방향, 색상, 조명 등 변경 (제품 형태 유지)",
            "detail": "촬영 방향, 색상, 조명 등을 자유롭게 수정하면서 제품의 고유한 형태와 디자인은 그대로 유지합니다."
        },
        "썸네일 생성": {
            "short": "상세페이지 분석, 최적화 썸네일 이미지 생성",
            "detail": "상세페이지 이미지를 분석하여 SNS, 광고에 최적화된 고퀄리티 썸네일을 자동으로 만들어드립니다."
        },
        "스타일 적용": {
            "short": "레퍼런스 이미지의 조명/색감/분위기 복제 적용",
            "detail": "마음에 드는 이미지의 조명, 색감, 분위기를 분석하여 내 제품에 동일한 스타일을 적용합니다."
        },
        "객체 교체": {
            "short": "레퍼런스 이미지 속 특정 제품을 자사 제품으로 자연스럽게 합성",
            "detail": "레퍼런스 이미지의 특정 제품 위치에 자사 제품을 자연스럽게 합성합니다. 조명과 그림자까지 자동 조정됩니다."
        },
        "스튜디오 촬영": {
            "short": "여러 제품을 하나의 공간에 배치한 제품 연출 스틸컷 생성",
            "detail": "여러 제품을 하나의 공간(스튜디오, 화장대, 욕실 등)에 배치한 자연스러운 생활 장면을 만들어드립니다."
        }
    }

    def __init__(self):
        super().__init__()
        self.setWindowTitle("ITCEN CLOIT")
        self.setGeometry(100, 100, 900, 800)

        self.setStyleSheet("""
            QMainWindow {
                background: #f8f9fa;
            }
            QToolTip {
                color: black;
                background: white;
                background-color: white;
                border: 1px solid #aaaaaa;
                padding: 8px;
                font-size: 12px;
            }
        """)

        self.main_widget = QWidget()
        self.setCentralWidget(self.main_widget)
        self.main_layout = QHBoxLayout(self.main_widget)
        self.main_layout.setSpacing(0)
        self.main_layout.setContentsMargins(0, 0, 0, 0)

        self.keyword_widgets = {}
        self.final_prompt = ""
        self.product_image_path = None
        self.gemini_client = Gemini()
        self.image_generator = ImageGenerator()
        self.generation_mode = None

        self.loading_text_index = 0
        self.loading_texts = [
            "입력 이미지 데이터 분석중...",
            "레퍼런스 이미지 분석중...",
            "최종 결과 조합 중...",
            "조금만 기다려주세요, 거의 완성되었습니다!"
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
                background: #273444;
                border: none;
            }
        """)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(20, 30, 20, 20)
        sidebar_layout.setSpacing(5)

        title_label = QLabel("CEN AI STUDIO")
        title_label.setFont(QFont("Noto Sans KR", 18, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("""
            QLabel {
                color: #FFFFFF;
                font-weight: bold;
                margin-bottom: 10px;
                padding: 10px;
            }
        """)

        self.sidebar_labels = [
            QLabel("Step 1: 옵션 선택"),
            QLabel("Step 2: 이미지 생성"),
            QLabel("Step 3: 이미지 편집"),
            QLabel("Step 4: 결과 확인")
        ]

        sidebar_layout.addWidget(title_label)
        sidebar_layout.addSpacing(5)

        for i, label in enumerate(self.sidebar_labels):
            label.setFont(QFont("Noto Sans KR", 12, QFont.Medium))
            label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            label.setWordWrap(True)
            label.setStyleSheet("""
                QLabel {
                    color: #A0AEC0;
                    padding: 6px 15px;
                    border-radius: 6px;
                    background: transparent;
                    font-weight: 400;
                }
            """)
            sidebar_layout.addWidget(label)

        sidebar_layout.addStretch(1)

        copyright_label = QLabel("Copyright © 2025\nITCEN CLOIT\nAll rights reserved.")
        copyright_label.setFont(QFont("Noto Sans KR", 11))
        copyright_label.setAlignment(Qt.AlignCenter)
        copyright_label.setWordWrap(True)
        copyright_label.setStyleSheet("""
            QLabel {
                color: #8A9EB2;
                padding: 15px 10px;
                font-weight: 300;
            }
        """)
        sidebar_layout.addWidget(copyright_label)
        self.main_layout.addWidget(sidebar)

    def create_main_content_area(self):
        main_content = QWidget()
        main_content.setStyleSheet("background: #f8f9fa;")
        main_content_layout = QVBoxLayout(main_content)
        main_content_layout.setContentsMargins(30, 30, 30, 30)
        main_content_layout.setSpacing(10)

        self.stacked_widget = QStackedWidget()
        self.page1 = self.create_step1_page()
        self.page2 = self.create_step3_page() # Page 2 is now the loading page
        self.page3 = self.create_step4_page() # Page 3 is now the editing page
        self.page4 = self.create_step5_page() # Page 4 is now the results page
        self.stacked_widget.addWidget(self.page1)
        self.stacked_widget.addWidget(self.page2)
        self.stacked_widget.addWidget(self.page3)
        self.stacked_widget.addWidget(self.page4)
        main_content_layout.addWidget(self.stacked_widget)

        nav_layout = QHBoxLayout()
        nav_layout.addStretch(1)
        self.prev_button = QPushButton("← 이전")
        self.next_button = QPushButton("생성 →")

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
                    min-width: 60px;
                }
                QPushButton:hover { background: #0056b3; }
                QPushButton:pressed { background: #004085; }
                QPushButton:disabled { background: #6c757d; color: #dee2e6; }
            """)

        self.prev_button.clicked.connect(self.go_to_prev_step)
        self.next_button.clicked.connect(self.go_to_next_step)
        nav_layout.addWidget(self.prev_button)
        nav_layout.addSpacing(15)
        nav_layout.addWidget(self.next_button)
        main_content_layout.addLayout(nav_layout)
        self.main_layout.addWidget(main_content)

    def create_step1_page(self):
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)
        scroll_area.setStyleSheet("QScrollArea { background: transparent; }")

        page = QWidget()
        page.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 15, 0, 0)
        layout.setSpacing(18)

        title = QLabel("AI 이미지 생성 옵션")
        title.setStyleSheet("""
            QLabel {
                font-size: 22px; font-weight: 700; color: #212529;
                margin-bottom: 0px; padding: 0px 0px 10px 0px;
                border-bottom: 3px solid #007bff;
            }
        """)
        layout.addWidget(title)

        # Generation Options
        options_group = QGroupBox("생성 기능 선택")
        options_group.setStyleSheet(""" 
            QGroupBox { 
                border: 2px solid #e8f5e9; border-radius: 12px; margin-top: 8px;
                padding: 20px 15px 15px 15px; font-weight: 600; font-size: 14px;
                color: #2e7d32; background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #ffffff, stop:1 #f9fdf9);
            }
            QGroupBox::title { background: transparent; padding: 5px 10px; color: #2e7d32; }
        """)
        options_layout = QGridLayout(options_group)

        self.option_buttons = {
            "change_attributes": QPushButton("속성 변경"),
            "create_thumbnail": QPushButton("썸네일 생성"),
            "apply_style": QPushButton("스타일 적용"),
            "replace_object": QPushButton("객체 교체"),
            "create_scene": QPushButton("스튜디오 촬영")
        }

        positions = [(i, j) for i in range(2) for j in range(3)]
        for (i, j), (mode, btn) in zip(positions, self.option_buttons.items()):
            btn.setStyleSheet("""
                QPushButton {
                    background: white; color: #495057; border: 2px solid #dee2e6; border-radius: 10px;
                    padding: 12px 18px; font-size: 13px; font-weight: 600; min-width: 120px;
                }
                QPushButton:hover { background: #f8f9fa; border-color: #007bff; }
                QPushButton:checked { 
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #667eea, stop:1 #764ba2);
                    color: white; border-color: #667eea;
                }
            """)
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked, m=mode: self.set_generation_mode(m))

            options_layout.addWidget(btn, i, j)

        layout.addWidget(options_group)

        # Dynamic Options Area
        self.dynamic_options_widget = QWidget()
        self.dynamic_options_layout = QVBoxLayout(self.dynamic_options_widget)
        self.dynamic_options_layout.setContentsMargins(0,0,0,0)
        layout.addWidget(self.dynamic_options_widget)

        layout.addStretch(1)
        scroll_area.setWidget(page)
        return scroll_area

    def set_generation_mode(self, mode):
        self.generation_mode = mode
        for m, btn in self.option_buttons.items():
            if m != mode:
                btn.setChecked(False)
        self.update_dynamic_options()

    def update_dynamic_options(self):
        # Clear previous dynamic widgets
        while self.dynamic_options_layout.count():
            child = self.dynamic_options_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        if self.generation_mode is None:
            return

        # Main Product Image
        self.main_product_group = self.create_image_input_group(
            "메인 상품 이미지", "main_product", 
            max_images=1 if self.generation_mode != 'create_scene' else 5
        )
        self.dynamic_options_layout.addWidget(self.main_product_group)

        # Reference Image (if applicable)
        if self.generation_mode in ['apply_style', 'replace_object', 'create_thumbnail']:
            self.reference_group = self.create_image_input_group("레퍼런스 이미지", "reference", max_images=5)
            self.dynamic_options_layout.addWidget(self.reference_group)

        # Instructions (if applicable)
        if self.generation_mode == 'change_attributes':
            self.instructions_group = QGroupBox("변경 지시사항")
            self.instructions_layout = QVBoxLayout(self.instructions_group)
            self.instructions_input = QTextEdit()
            self.instructions_input.setPlaceholderText("예: 제품을 우측 컷으로 변경해주세요.")
            self.instructions_layout.addWidget(self.instructions_input)
            self.dynamic_options_layout.addWidget(self.instructions_group)

    def create_image_input_group(self, title, key, max_images=3):
        group_box = QGroupBox(title)
        group_box.setStyleSheet("""
            QGroupBox {
                border: 2px solid #e3f2fd;
                border-radius: 12px;
                margin-top: 8px;
                padding: 20px 15px 15px 15px;
                font-weight: 600;
                font-size: 14px;
                color: #1976d2;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #ffffff, stop:1 #f8fbff);
            }
            QGroupBox::title {
                background: transparent;
                padding: 5px 10px;
                color: #1976d2;
            }
        """)

        layout = QVBoxLayout(group_box)

        scroll_area = QScrollArea()
        scroll_area.setFrameShape(QFrame.NoFrame)
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setFixedHeight(110)

        image_grid_widget = QWidget()
        image_grid_layout = self.create_image_grid_layout()
        image_grid_widget.setLayout(image_grid_layout)
        scroll_area.setWidget(image_grid_widget)
        layout.addWidget(scroll_area)

        setattr(image_grid_widget, 'image_paths', [])
        setattr(image_grid_widget, 'max_images', max_images)
        setattr(group_box, 'grid_widget', image_grid_widget)

        self.update_image_grid(image_grid_widget)
        return group_box
    
    def create_image_grid_layout(self):
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        layout.addStretch()
        return layout

    def create_image_card(self, image_path, grid_widget):
        card = QWidget()
        card.setFixedSize(96, 96)
        card.setStyleSheet("""
            QWidget {
                border: 2px solid #e9ecef;
                border-radius: 8px;
                background-color: white;
            }
            QWidget:hover {
                border-color: #667eea;
            }
        """)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(3, 3, 3, 3)

        img_label = QLabel()
        pixmap = QPixmap(image_path)
        scaled_pixmap = pixmap.scaled(90, 90, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        img_label.setPixmap(scaled_pixmap)
        img_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(img_label)

        delete_btn = QPushButton("✕", card)
        delete_btn.setFixedSize(22, 22)
        delete_btn.move(card.width() - delete_btn.width() - 1, 1)
        delete_btn.setStyleSheet("""
            QPushButton {
                border: none;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #f857a6, stop:1 #ff5858);
                color: white;
                font-weight: bold;
                font-size: 12px;
                border-radius: 11px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #ff5858, stop:1 #f857a6);
            }
        """)
        delete_btn.clicked.connect(lambda: self.remove_image_card(image_path, grid_widget))
        return card

    def create_add_button(self, grid_widget):
        add_card = QWidget()
        add_card.setFixedSize(96, 96)
        add_card.setStyleSheet("""
            QWidget { 
                border: 2px dashed #adb5bd; border-radius: 8px; 
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #ffffff, stop:1 #f8f9fa);
            }
            QWidget:hover { 
                border-color: #667eea; 
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #f8f9ff, stop:1 #e9ecff);
            }
        """)
        layout = QVBoxLayout(add_card)
        add_label = QLabel("+")
        add_label.setAlignment(Qt.AlignCenter)
        add_label.setStyleSheet("border: none; background-color: transparent; color: #667eea; font-size: 28px; font-weight: bold;")
        layout.addWidget(add_label)
        add_card.mousePressEvent = lambda event: self.add_images_to_grid(grid_widget)
        return add_card

    def add_images_to_grid(self, grid_widget):
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
        if image_path in grid_widget.image_paths:
            grid_widget.image_paths.remove(image_path)
            self.update_image_grid(grid_widget)

    def update_image_grid(self, grid_widget):
        layout = grid_widget.layout()
        max_images = getattr(grid_widget, 'max_images', 3)

        # Clear all items from the layout
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        for image_path in grid_widget.image_paths:
            card = self.create_image_card(image_path, grid_widget)
            layout.addWidget(card)

        if len(grid_widget.image_paths) < max_images:
            add_btn = self.create_add_button(grid_widget)
            layout.addWidget(add_btn)

        layout.addStretch()





    def create_step3_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setAlignment(Qt.AlignCenter)
        self.status_label = QLabel("AI가 이미지를 생성하고 있습니다...")
        self.status_label.setStyleSheet("font-size: 16px; font-weight: 500; color: #495057;")
        layout.addWidget(self.status_label)
        return page

    def create_step4_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        title = QLabel("Step 3: 이미지 편집")
        layout.addWidget(title)
        # Add image editing widgets here later
        return page

    def create_step5_page(self):
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)

        page = QWidget()
        layout = QVBoxLayout(page)
        
        title = QLabel("Step 4: 최종 결과 확인")
        title.setStyleSheet("font-size: 20px; font-weight: 600; color: #495057;")
        layout.addWidget(title)
        
        group = QGroupBox("저장된 최종 이미지")
        self.results_grid_layout = QGridLayout(group)
        layout.addWidget(group)

        scroll_area.setWidget(page)
        return scroll_area

    def show_large_image(self, pixmap):
        dialog = QDialog(self)
        dialog.setWindowTitle("이미지 크게 보기")
        layout = QVBoxLayout(dialog)
        label = QLabel()
        label.setPixmap(pixmap.scaled(800, 800, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        layout.addWidget(label)
        dialog.exec_()

    @pyqtSlot(list)
    def on_final_save_completed(self, final_image_paths):
        # Clear previous results
        while self.results_grid_layout.count():
            child = self.results_grid_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        # Populate the grid with final images
        for i, image_path in enumerate(final_image_paths):
            pixmap = QPixmap(image_path)
            if pixmap.isNull():
                continue

            image_container = QFrame()
            image_container.setFrameShape(QFrame.StyledPanel)
            container_layout = QVBoxLayout(image_container)
            
            image_label = QLabel()
            image_label.setPixmap(pixmap.scaled(250, 250, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            image_label.setAlignment(Qt.AlignCenter)
            image_label.mousePressEvent = lambda event, p=pixmap: self.show_large_image(p)
            image_label.setCursor(Qt.PointingHandCursor)

            path_label = QLabel(os.path.basename(image_path))
            path_label.setAlignment(Qt.AlignCenter)
            path_label.setWordWrap(True)

            container_layout.addWidget(image_label)
            container_layout.addWidget(path_label)

            row, col = i // 3, i % 3 # 3 columns grid
            self.results_grid_layout.addWidget(image_container, row, col)

        # Go to the results page
        self.stacked_widget.setCurrentIndex(3)
        self.update_workflow_ui(3)


    def update_workflow_ui(self, step_index):
        for i, label in enumerate(self.sidebar_labels):
            is_current = (i == step_index)
            is_done = (i < step_index)
            if is_current:
                style = "color: white; background: rgba(255, 255, 255, 0.2); border-left: 3px solid #007bff;"
            elif is_done:
                style = "color: rgba(255, 255, 255, 0.8); background: rgba(255, 255, 255, 0.1); border-left: 3px solid #28a745;"
            else:
                style = "color: rgba(255, 255, 255, 0.6); background: rgba(255, 255, 255, 0.05);"

            label.setStyleSheet(f"""
                QLabel {{
                    padding: 12px 15px;
                    border-radius: 6px;
                    margin: 3px 0;
                    font-weight: {500 if is_current else 400};
                    {style}
                }}
            """)

        self.prev_button.setEnabled(step_index > 0)
        self.next_button.setEnabled(step_index < self.stacked_widget.count() - 1 and step_index != 2)
        
        if step_index == 0:
            self.next_button.setText("생성 →")
        elif step_index == 2: # Editor page
            self.next_button.setText("결과 확인 →")
        elif step_index == self.stacked_widget.count() - 1: # Results page
            self.next_button.setText("다시하기")
        else:
            self.next_button.setText("다음 →")

    def go_to_next_step(self):
        current_index = self.stacked_widget.currentIndex()
        if current_index == self.stacked_widget.count() - 1:
            self.stacked_widget.setCurrentIndex(0)
            self.update_workflow_ui(0)
            return

        if current_index == 0:
            if not self.generation_mode:
                QMessageBox.warning(self, "오류", "생성 기능을 선택해주세요.")
                return
            
            main_images = self.main_product_group.grid_widget.image_paths
            if not main_images:
                QMessageBox.warning(self, "오류", "메인 상품 이미지를 추가해주세요.")
                return

            if self.generation_mode == 'change_attributes':
                if not self.instructions_input.toPlainText().strip():
                    QMessageBox.warning(self, "오류", "변경 지시사항을 입력해주세요.")
                    return
            
            if self.generation_mode in ['apply_style', 'replace_object']:
                if hasattr(self, 'reference_group'):
                    ref_images = self.reference_group.grid_widget.image_paths
                    if not ref_images:
                        QMessageBox.warning(self, "오류", "레퍼런스 이미지를 추가해주세요.")
                        return
                else:
                    QMessageBox.warning(self, "오류", "레퍼런스 이미지를 추가해주세요.")
                    return

            # Start generation immediately
            kwargs = {}
            if self.generation_mode == 'change_attributes':
                kwargs['image_paths'] = main_images
                kwargs['instructions'] = self.instructions_input.toPlainText().strip().split('\n')
            elif self.generation_mode == 'create_thumbnail':
                kwargs['image_paths'] = main_images
                if hasattr(self, 'reference_group'):
                    kwargs['reference_image_paths'] = self.reference_group.grid_widget.image_paths
            elif self.generation_mode == 'apply_style':
                kwargs['product_image_paths'] = main_images
                kwargs['reference_image_paths'] = self.reference_group.grid_widget.image_paths
            elif self.generation_mode == 'replace_object':
                kwargs['product_image_paths'] = main_images
                kwargs['reference_image_paths'] = self.reference_group.grid_widget.image_paths
            elif self.generation_mode == 'create_scene':
                kwargs['product_image_paths'] = main_images

            self.stacked_widget.setCurrentIndex(1) # Go to loading page
            self.update_workflow_ui(1)

            self.image_thread = ImageGenerationThread(self.image_generator, self.generation_mode, **kwargs)
            self.image_thread.images_ready.connect(self.on_images_ready)
            self.image_thread.error_occurred.connect(self.on_generation_error)
            self.image_thread.finished.connect(self.image_thread.deleteLater)

            self.loading_text_index = 0
            self.update_loading_animation()
            self.animation_timer.start(2000)
            self.image_thread.start()

        elif current_index == 1:
            # This is the loading page, button should be disabled.
            pass

        elif current_index == 2:
            # This is the editor page. The transition is now handled by the finalSaveCompleted signal.
            # The default next button is disabled, so this part should not be reached.
            pass

        elif current_index == 3:
            # 결과 페이지에서 다시하기
            self.stacked_widget.setCurrentIndex(0)
            self.update_workflow_ui(0)

    def go_to_prev_step(self):
        current_index = self.stacked_widget.currentIndex()
        if current_index > 0:
            self.stacked_widget.setCurrentIndex(current_index - 1)
            self.update_workflow_ui(current_index - 1)

    def update_loading_animation(self):
        self.status_label.setText(self.loading_texts[self.loading_text_index])
        self.loading_text_index = (self.loading_text_index + 1) % len(self.loading_texts)

    @pyqtSlot(str)
    def on_generation_error(self, error_message):
        self.animation_timer.stop()
        QMessageBox.critical(self, "Generation Error", error_message)
        self.go_to_prev_step()

    @pyqtSlot(list)
    def on_images_ready(self, saved_image_paths):
        self.animation_timer.stop()

        if not saved_image_paths:
            QMessageBox.warning(self, "오류", "생성된 이미지가 없습니다.")
            self.go_to_prev_step()
            return

        # 첫 번째 생성된 이미지를 편집 페이지에 로드
        self.generated_image_path = saved_image_paths[0]
        
        # Step 3 페이지(편집 페이지)에 AiEditorWidget이 없다면 추가
        if not hasattr(self, 'editor_widget'):
            from editor import AiEditorWidget
            
            # 기존 page3 제거
            old_page3 = self.stacked_widget.widget(2)
            self.stacked_widget.removeWidget(old_page3)
            old_page3.deleteLater()
            
            # AiEditorWidget 추가
            self.editor_widget = AiEditorWidget(self)
            self.editor_widget.finalSaveCompleted.connect(self.on_final_save_completed)
            self.stacked_widget.insertWidget(2, self.editor_widget)
        
        # 생성된 이미지를 편집기에 로드
        self.editor_widget.load_image(self.generated_image_path)
        
        # 모든 생성된 이미지 경로 저장 (나중에 결과 페이지에서 사용)
        self.all_generated_images = saved_image_paths
        
        # 편집 페이지로 이동
        self.stacked_widget.setCurrentIndex(2)
        self.update_workflow_ui(2)
        
        # 네비게이션 버튼 텍스트 업데이트
        self.next_button.setText("결과 확인 →")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    font = QFont("Noto Sans KR", 10)
    app.setFont(font)
    app.setStyle('Fusion')
    ex = AIGeneratorApp()
    ex.show()
    sys.exit(app.exec_())
