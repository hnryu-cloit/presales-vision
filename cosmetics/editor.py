import os
from io import BytesIO
from PIL import Image

from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFileDialog, QGroupBox, QComboBox, QTextEdit,QGraphicsView,
    QGraphicsScene, QGraphicsPixmapItem, QFrame,
    QSlider, QRadioButton, QButtonGroup, QFormLayout, QColorDialog, QAction, QMessageBox,
    QDialog, QScrollArea
)

from PyQt5.QtCore import Qt, QPoint, QRectF, pyqtSignal, QThread, QBuffer, QIODevice
from PyQt5.QtGui import  QPixmap, QImage, QPainter, QPen, QColor, QKeySequence, QIcon

from common import timefn

class ImagePopup(QDialog):
    def __init__(self, image_bytes, parent=None):
        super().__init__(parent)
        self.setWindowTitle("재생성된 이미지")
        self.setModal(True)
        self.image_bytes = image_bytes

        layout = QVBoxLayout(self)
        label = QLabel(self)

        self.pixmap = QPixmap()
        self.pixmap.loadFromData(image_bytes)

        label.setPixmap(self.pixmap.scaled(512, 512, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        layout.addWidget(label)

        # 버튼 레이아웃
        button_layout = QHBoxLayout()

        cancel_button = QPushButton("취소")
        cancel_button.clicked.connect(self.reject)

        confirm_button = QPushButton("확인")
        confirm_button.clicked.connect(self.accept)

        button_layout.addWidget(cancel_button)
        button_layout.addWidget(confirm_button)

        layout.addLayout(button_layout)
        self.setLayout(layout)


class PhotoViewer(QGraphicsView):
    brushSizeChanged = pyqtSignal(int)
    eraserSizeChanged = pyqtSignal(int)
    historyChanged = pyqtSignal(bool, bool) # undo_enabled, redo_enabled

    def __init__(self, parent=None):
        super().__init__(parent)
        self._scene = QGraphicsScene(self)
        self._photo = QGraphicsPixmapItem()
        self._scene.addItem(self._photo)
        self.setScene(self._scene)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        self.setRenderHint(QPainter.Antialiasing)
        self.setFrameShape(QFrame.NoFrame)

        # Drawing attributes
        self.drawing = False
        self.brush_size = 20
        self.eraser_size = 20
        self.draw_mode = 'brush'
        self.drawing_color = QColor(255, 0, 0, 128) # Store the actual color
        self.brush_color = self.drawing_color # The color currently in use
        self.last_point = QPoint()
        self.cursor_pos = QPoint()
        self.last_pan_pos = QPoint() # For panning

        # Mouse tracking for cursor
        self.setMouseTracking(True)

        self.setFocusPolicy(Qt.StrongFocus)

        # Mask layer
        self.mask_image = QImage()

        # Undo/Redo
        self.undo_stack = []
        self.redo_stack = []
        self.image_before_draw = None

    def set_photo(self, pixmap):
        self._photo.setPixmap(pixmap)
        self.mask_image = QImage(pixmap.size(), QImage.Format_ARGB32)
        self.mask_image.fill(Qt.transparent)

        # Reset history
        self.undo_stack = []
        self.redo_stack = []
        self.historyChanged.emit(False, False)

        self.setSceneRect(QRectF(pixmap.rect()))
        self.fitInView()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, '_photo') and not self._photo.pixmap().isNull():
            self.fitInView()

    def set_draw_mode(self, button):
        if button.text() == "브러시":
            self.draw_mode = 'brush'
        elif button.text() == "지우개":
            self.draw_mode = 'eraser'

    def fitInView(self, rect=None, flags=Qt.KeepAspectRatio):
        if rect is None:
            rect = self.sceneRect()
        if rect.isEmpty():
            return
        
        # Use the default implementation which is more robust and should not limit zooming.
        super().fitInView(rect, flags)

    def set_brush_size(self, size):
        self.brush_size = size

    def set_eraser_size(self, size):
        self.eraser_size = size

    def set_drawing_color(self, color):
        color.setAlpha(204) # Apply 20% transparency (80% opacity)
        self.drawing_color = color
        if self.draw_mode == 'brush':
            self.brush_color = self.drawing_color

    def undo(self):
        if self.undo_stack:
            self.redo_stack.append(self.mask_image.copy())
            self.mask_image = self.undo_stack.pop()
            self.viewport().update()
            self.historyChanged.emit(bool(self.undo_stack), True)

    def redo(self):
        if self.redo_stack:
            self.undo_stack.append(self.mask_image.copy())
            self.mask_image = self.redo_stack.pop()
            self.viewport().update()
            self.historyChanged.emit(True, bool(self.redo_stack))

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drawing = True
            self.last_point = self.mapToScene(event.pos()).toPoint()
            self.image_before_draw = self.mask_image.copy()
        elif event.button() == Qt.RightButton:
            self.last_pan_pos = event.pos() # Store position for panning
            event.accept() # Accept the event

    def mouseMoveEvent(self, event):
        self.cursor_pos = event.pos()

        if event.buttons() == Qt.RightButton and not self.last_pan_pos.isNull():
            # Panning
            delta = event.pos() - self.last_pan_pos
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - delta.x())
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() - delta.y())
            self.last_pan_pos = event.pos()
            event.accept()
        elif event.buttons() and Qt.LeftButton and self.drawing:
            # Drawing
            current_point = self.mapToScene(event.pos()).toPoint()
            painter = QPainter(self.mask_image)

            if self.draw_mode == 'eraser':
                painter.setCompositionMode(QPainter.CompositionMode_Clear)
                pen = QPen(Qt.transparent, self.eraser_size, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
            else: # Brush mode
                painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
                pen = QPen(self.brush_color, self.brush_size, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)

            painter.setPen(pen)
            painter.drawLine(self.last_point, current_point)

            self.last_point = current_point
            event.accept() # Accept drawing event

        self.viewport().update() # Update to draw cursor

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self.drawing:
            self.drawing = False
            # Check if the image was actually modified to avoid empty history states
            if self.image_before_draw is not None and self.image_before_draw != self.mask_image:
                self.undo_stack.append(self.image_before_draw)
                self.redo_stack.clear() # Clear redo stack on new action

                # Limit undo stack size
                if len(self.undo_stack) > 20:
                    self.undo_stack.pop(0)

                self.historyChanged.emit(True, False)
            event.accept() # Accept the event
        elif event.button() == Qt.RightButton:
            self.last_pan_pos = QPoint() # Clear pan position
            event.accept() # Accept the event

    def leaveEvent(self, event):
        self.cursor_pos = QPoint(-1, -1) # Move cursor off-screen
        self.viewport().update()
        super().leaveEvent(event)

    def paintEvent(self, event):
        super().paintEvent(event)

        painter = QPainter(self.viewport())

        # Draw mask
        if not self.mask_image.isNull():
            source_rect = self.mask_image.rect()
            target_rect = self.mapFromScene(self.sceneRect()).boundingRect()
            painter.drawImage(target_rect, self.mask_image, source_rect)

        # Draw cursor preview
        if self.cursor_pos.x() > 0:
            painter.setRenderHint(QPainter.Antialiasing)
            if self.draw_mode == 'brush':
                size = self.brush_size * self.transform().m11() # Adjust for zoom
                color = QColor(self.brush_color)
                color.setAlpha(128)
                painter.setBrush(color)
                painter.setPen(Qt.NoPen)
                painter.drawEllipse(self.cursor_pos, size / 2, size / 2)
            else: # Eraser
                size = self.eraser_size * self.transform().m11() # Adjust for zoom
                pen = QPen(Qt.black, 1, Qt.DashLine)
                painter.setPen(pen)
                painter.setBrush(Qt.NoBrush)
                painter.drawEllipse(self.cursor_pos, size / 2, size / 2)

    def wheelEvent(self, event):
        if event.modifiers() == Qt.ControlModifier:
            # Ctrl + Wheel for brush/eraser size
            delta = event.angleDelta().y()
            if self.draw_mode == 'brush':
                current_size = self.brush_size
                if delta > 0:
                    current_size += 1
                else:
                    current_size -= 1
                current_size = max(1, min(100, current_size)) # Clamp value
                self.brush_size = current_size
                self.brushSizeChanged.emit(current_size)
            else: # Eraser mode
                current_size = self.eraser_size
                if delta > 0:
                    current_size += 1
                else:
                    current_size -= 1
                current_size = max(1, min(100, current_size)) # Clamp value
                self.eraser_size = current_size
                self.eraserSizeChanged.emit(current_size)

            self.viewport().update() # Redraw cursor
            event.accept() # Accept the event to prevent further propagation
        elif event.modifiers() == Qt.NoModifier:
            # Mouse Wheel for zoom
            zoom_factor = 1.15 # Zoom in/out factor
            if event.angleDelta().y() > 0:
                self.scale(zoom_factor, zoom_factor) # Zoom in
            else:
                self.scale(1 / zoom_factor, 1 / zoom_factor) # Zoom out
            event.accept() # Accept the event
        else:
            super().wheelEvent(event)

class ThumbnailWidget(QFrame):
    removed = pyqtSignal(str) # Pass the image path on removal

    def __init__(self, image_path, parent=None):
        super().__init__(parent)
        self.image_path = image_path
        self.setFrameShape(QFrame.StyledPanel)
        self.setFixedSize(120, 140)

        layout = QVBoxLayout(self)

        # Image
        pixmap_label = QLabel()
        pixmap = QPixmap(image_path).scaled(100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        pixmap_label.setPixmap(pixmap)
        pixmap_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(pixmap_label)

        # Remove button
        remove_btn = QPushButton("삭제")
        remove_btn.clicked.connect(lambda: self.removed.emit(self.image_path))
        layout.addWidget(remove_btn)

class AiEditorWidget(QWidget):
    back_requested = pyqtSignal()
    def __init__(self, parent=None):
        super().__init__(parent)
        self.reference_paths = []
        self.original_image_path = None
        self.vision_editor = VisionEditor()

        # 카테고리별 레퍼런스 이미지 경로 저장
        self.pose_reference = None
        self.framing_reference = None
        self.angle_reference = None
        self.mood_reference = None

        self.init_ui()

    def init_ui(self):
        # The main layout is now a QVBoxLayout to accommodate the bottom bar
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(11, 11, 11, 11)

        # Content widget and layout
        content_widget = QWidget()
        content_layout = QHBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)

        # --- Left Panel ---
        left_container = QWidget()
        left_main_layout = QVBoxLayout(left_container)
        left_main_layout.setContentsMargins(0, 0, 0, 0)
        left_container.setFixedWidth(250)

        # 1. Tools Panel
        tools_panel = QGroupBox("도구")
        tools_layout = QVBoxLayout(tools_panel)

        # Brush/Eraser buttons
        self.brush_btn = QPushButton("브러시")
        self.brush_btn.setCheckable(True)
        self.brush_btn.setChecked(True)
        self.eraser_btn = QPushButton("지우개")
        self.eraser_btn.setCheckable(True)
        self.brush_group = QButtonGroup(self)
        self.brush_group.addButton(self.brush_btn)
        self.brush_group.addButton(self.eraser_btn)
        self.brush_group.setExclusive(True)
        tools_layout.addWidget(self.brush_btn)
        tools_layout.addWidget(self.eraser_btn)

        # Brush size slider
        tools_layout.addWidget(QLabel("브러시 크기"))
        self.brush_slider = QSlider(Qt.Horizontal)
        self.brush_slider.setRange(1, 100)
        self.brush_slider.setValue(20)
        tools_layout.addWidget(self.brush_slider)

        # Eraser size slider
        tools_layout.addWidget(QLabel("지우개 크기"))
        self.eraser_slider = QSlider(Qt.Horizontal)
        self.eraser_slider.setRange(1, 100)
        self.eraser_slider.setValue(20)
        tools_layout.addWidget(self.eraser_slider)

        # Color button
        self.color_btn = QPushButton("색상 변경")
        tools_layout.addWidget(self.color_btn)
        self.color_btn.clicked.connect(self.open_color_picker)


        # Undo/Redo buttons (moved inside tools_layout)
        undo_redo_layout = QHBoxLayout()
        self.undo_btn = QPushButton()
        self.undo_btn.setIcon(QIcon(os.path.join(os.path.dirname(os.path.abspath(__file__)),"../resource/icon/backward.png")))
        self.undo_btn.setToolTip("실행 취소 (Ctrl+Z)")
        self.redo_btn = QPushButton()
        self.redo_btn.setIcon(QIcon(os.path.join(os.path.dirname(os.path.abspath(__file__)),"../resource/icon/next.png")))
        self.redo_btn.setToolTip("다시 실행 (Ctrl+Y)")

        button_style = '''
            QPushButton {
                background-color: #FFFFFF;
                border: 1px solid #CCCCCC;
                border-radius: 4px;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #F0F0F0;
            }
            QPushButton:pressed {
                background-color: #E0E0E0;
            }
        '''
        self.undo_btn.setStyleSheet(button_style)
        self.redo_btn.setStyleSheet(button_style)

        undo_redo_layout.addWidget(self.undo_btn)
        undo_redo_layout.addWidget(self.redo_btn)
        tools_layout.addLayout(undo_redo_layout) # <--- ADDED HERE

        # 2. AI Editing Options Panel
        ai_options_panel = QGroupBox("AI 편집 옵션")
        ai_options_layout = QVBoxLayout(ai_options_panel)

        # 2.1 Segmentation & Masking
        seg_group = QGroupBox("영역 선택 및 마스크")
        seg_layout = QVBoxLayout(seg_group)

        self.segment_button = QPushButton("전경/배경 분리")
        seg_layout.addWidget(self.segment_button)
        self.mask_keep_radio = QRadioButton("선택 영역 유지")
        self.mask_change_radio = QRadioButton("선택 영역 변경")
        self.mask_change_radio.setChecked(True)

        seg_layout.addWidget(self.mask_keep_radio)
        seg_layout.addWidget(self.mask_change_radio)
        ai_options_layout.addWidget(seg_group)

        # 2.2 Detailed Controls
        details_group = QGroupBox("상세 옵션")
        details_layout = QFormLayout(details_group)
        details_layout.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)

        # Pose section
        self.pose_combo = QComboBox()
        self.pose_combo.addItems([
            "유지", "정자세", "걷는 포즈", "앉은 포즈", "기대는 포즈", 
            "손 모션 포함", "다이나믹 포즈"
        ])
        self.pose_detail = QTextEdit()
        self.pose_detail.setPlaceholderText("포즈에 대한 자세한 설명을 입력하세요.")
        self.pose_detail.setMaximumHeight(100)
        self.pose_detail.setVisible(False)
        self.pose_combo.currentTextChanged.connect(self.on_pose_changed)

        # Framing section  
        self.framing_combo = QComboBox()
        self.framing_combo.addItems([
            "기본 구도 유지", "전신", "상반신", "하반신", "클로즈업",
            "디테일 컷", "3/4 샷",
        ])
        self.framing_detail = QTextEdit()
        self.framing_detail.setPlaceholderText("구도에 대한 자세한 설명을 입력하세요.")
        self.framing_detail.setMaximumHeight(100)
        self.framing_detail.setVisible(False)
        self.framing_combo.currentTextChanged.connect(self.on_framing_changed)

        # Angle section
        self.angle_combo = QComboBox()
        self.angle_combo.addItems([
            "정면", "좌측면", "우측면", "45도 각도", "후면", 
            "하이 앵글", "로우 앵글", "디테일 앵글"
        ])
        self.angle_detail = QTextEdit()
        self.angle_detail.setPlaceholderText("촬영 각도에 대한 자세한 설명을 입력하세요.")
        self.angle_detail.setMaximumHeight(100)
        self.angle_detail.setVisible(False)
        self.angle_combo.currentTextChanged.connect(self.on_angle_changed)

        # Overall mood
        self.mode_combo = QComboBox()
        self.mode_combo.addItems([
            "유지",
            "심플/베이직",
            "모던/미니멀",
            "세련/럭셔리",
            "캐주얼/데일리",
            "스포티/액티브",
            "러블리/페미닌",
            "시크/도시적",
            "빈티지/레트로",
            "자연스러움/라이프스타일",
            "시즌감 (봄/여름/가을/겨울)",
            "직접입력"
        ])

        self.mood_detail = QTextEdit()
        self.mood_detail.setPlaceholderText("전체적인 분위기와 컨셉을 입력하세요.")
        self.mood_detail.setMaximumHeight(100)
        self.mood_detail.setVisible(False)
        self.mode_combo.currentTextChanged.connect(self.on_mode_changed)

        # Add all to layout
        details_layout.addRow("포즈:", self.pose_combo)
        details_layout.addRow("", self.pose_detail)
        # 포즈 레퍼런스 업로드 버튼
        self.pose_ref_btn = QPushButton("레퍼런스 업로드")
        self.pose_ref_btn.setVisible(False)
        self.pose_ref_btn.clicked.connect(lambda: self.upload_reference_image('pose'))
        details_layout.addRow("", self.pose_ref_btn)

        details_layout.addRow("구도:", self.framing_combo)
        details_layout.addRow("", self.framing_detail)
        # 구도 레퍼런스 업로드 버튼
        self.framing_ref_btn = QPushButton("레퍼런스 업로드")
        self.framing_ref_btn.setVisible(False)
        self.framing_ref_btn.clicked.connect(lambda: self.upload_reference_image('framing'))
        details_layout.addRow("", self.framing_ref_btn)

        details_layout.addRow("촬영 방향:", self.angle_combo)
        details_layout.addRow("", self.angle_detail)
        # 촬영 방향 레퍼런스 업로드 버튼
        self.angle_ref_btn = QPushButton("레퍼런스 업로드")
        self.angle_ref_btn.setVisible(False)
        self.angle_ref_btn.clicked.connect(lambda: self.upload_reference_image('angle'))
        details_layout.addRow("", self.angle_ref_btn)

        details_layout.addRow("분위기:", self.mode_combo)
        details_layout.addRow("", self.mood_detail)
        # 분위기 레퍼런스 업로드 버튼
        self.mood_ref_btn = QPushButton("레퍼런스 업로드")
        self.mood_ref_btn.setVisible(False)
        self.mood_ref_btn.clicked.connect(lambda: self.upload_reference_image('mood'))
        details_layout.addRow("", self.mood_ref_btn)
        ai_options_layout.addWidget(details_group)

        # 초기 상태에서 이미 입력된 내용이 있으면 표시
        self.update_all_visibility()
        
        # Add stretch to align bottom with reference image layout
        ai_options_layout.addStretch()

        # Add panels to left container
        left_main_layout.addWidget(tools_panel)
        left_main_layout.addWidget(ai_options_panel)

        # --- Center/Right Panel ---
        center_container = QWidget()
        center_layout = QVBoxLayout(center_container)
        center_layout.setContentsMargins(0, 0, 0, 0)

        # 1. Image Viewer
        image_viewer_group = QGroupBox("이미지 편집")
        image_viewer_layout = QVBoxLayout(image_viewer_group)
        self.image_viewer = PhotoViewer(self)
        self.brush_group.buttonClicked.connect(self.image_viewer.set_draw_mode)
        self.brush_slider.valueChanged.connect(self.image_viewer.set_brush_size)
        self.eraser_slider.valueChanged.connect(self.image_viewer.set_eraser_size)
        self.image_viewer.brushSizeChanged.connect(self.brush_slider.setValue)
        self.image_viewer.eraserSizeChanged.connect(self.eraser_slider.setValue)
        self.image_viewer.historyChanged.connect(self.update_history_buttons)

        self.undo_btn.clicked.connect(self.image_viewer.undo)
        self.redo_btn.clicked.connect(self.image_viewer.redo)

        self.update_history_buttons(False, False) # Set initial state

        self.setup_shortcuts()

        image_viewer_layout.addWidget(self.image_viewer)
        center_layout.addWidget(image_viewer_group)

        # 2. Reference Image
        max_images = 5
        ref_image_group = QGroupBox(f"레퍼런스 이미지(최대 {max_images}개)")
        ref_image_main_layout = QVBoxLayout(ref_image_group)
        
        # Scroll Area for the image grid
        scroll_area = QScrollArea()
        scroll_area.setFrameShape(QFrame.NoFrame)
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setFixedHeight(120)

        # Image grid widget
        self.image_grid_widget = QWidget()
        self.image_grid_layout = self.create_image_grid_layout()
        self.image_grid_widget.setLayout(self.image_grid_layout)
        
        scroll_area.setWidget(self.image_grid_widget)
        ref_image_main_layout.addWidget(scroll_area)
        
        # Set attributes for grid widget
        setattr(self.image_grid_widget, 'image_paths', [])
        setattr(self.image_grid_widget, 'max_images', max_images)
        self.update_image_grid(self.image_grid_widget)
        
        # Add stretch to align bottom with left panel
        ref_image_main_layout.addStretch()

        center_layout.addWidget(ref_image_group)

        # Set height ratio but allow ref_image_group to expand naturally
        center_layout.setStretchFactor(image_viewer_group, 17)  # 85%
        center_layout.setStretchFactor(ref_image_group, 0)   # Let it size naturally

        # Add left and center panels to the content layout
        content_layout.addWidget(left_container)
        content_layout.addWidget(center_container, 1)

        # --- Bottom Bar ---
        bottom_widget = QWidget()
        bottom_layout = QHBoxLayout(bottom_widget)
        bottom_layout.setContentsMargins(0, 0, 0, 0)

        self.apply_button = QPushButton("적용하기")
        self.apply_button.setIcon(QIcon("../resource/icon/checked.png"))
        self.apply_button.setStyleSheet("background-color: #A23B72; color: white; padding: 10px; font-weight: bold;")
        self.apply_button.clicked.connect(self.start_image_regeneration)

        self.register_button = QPushButton("등록하기")
        self.register_button.setIcon(QIcon("../resource/icon/upload.png"))
        self.register_button.setStyleSheet("background-color: #4CAF50; color: white; padding: 10px; font-weight: bold;")
        self.register_button.setVisible(False)  # 초기에는 숨김
        self.register_button.clicked.connect(self.register_image)

        bottom_layout.addStretch(1)
        bottom_layout.addWidget(self.apply_button)
        bottom_layout.addWidget(self.register_button)

        # --- Add widgets to main layout ---
        main_layout.addWidget(content_widget, 1)
        main_layout.addWidget(bottom_widget)

    def create_image_grid_layout(self):
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        layout.addStretch()
        return layout

    def create_image_card(self, image_path, grid_widget, tag=None):
        card = QWidget()
        card.setFixedSize(80, 100)  # 태그 공간을 위해 높이 증가
        card.setStyleSheet(
            """
            QWidget { border: 2px solid #DDD; border-radius: 5px; background-color: white; }
            QWidget:hover { border-color: #A23B72; }
            """)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(2)

        # 이미지 레이블
        img_label = QLabel()
        img_label.setFixedSize(76, 56)  # 태그 공간을 위해 높이 조정
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

        # 태그 레이블 (있을 경우)
        if tag:
            tag_label = QLabel(tag)
            tag_label.setFixedHeight(16)
            tag_label.setAlignment(Qt.AlignCenter)
            tag_label.setStyleSheet("""
                QLabel {
                    background-color: #A23B72;
                    color: white;
                    font-size: 10px;
                    font-weight: bold;
                    border-radius: 3px;
                    padding: 1px;
                }
            """)
            layout.addWidget(tag_label)

        # 삭제 버튼
        delete_btn = QPushButton("✕", img_label)
        delete_btn.setFixedSize(20, 20)
        delete_btn.move(img_label.width() - delete_btn.width() - 2, 2)
        delete_btn.setToolTip("이미지 삭제")
        delete_btn.setStyleSheet(
            """
            QPushButton { border: none; background-color: rgba(255, 0, 0, 0.8); color: white; font-weight: bold; font-size: 12px; border-radius: 10px; }
            QPushButton:hover { background-color: rgba(255, 0, 0, 1.0); }
            """)
        delete_btn.clicked.connect(lambda: self.remove_image_card(image_path, grid_widget))
        return card

    def create_add_button(self, grid_widget):
        add_card = QWidget()
        add_card.setFixedSize(80, 80)
        add_card.setStyleSheet(
            """
            QWidget { border: 2px dashed #AAA; border-radius: 5px; background-color: #F8F8F8; }
            QWidget:hover { border-color: #A23B72; background-color: #F0F0F0; }
            """)
        layout = QVBoxLayout(add_card)
        layout.setContentsMargins(0, 0, 0, 0)
        add_label = QLabel("+")
        add_label.setAlignment(Qt.AlignCenter)
        add_label.setStyleSheet("border: none; background-color: transparent; color: #888; font-size: 24px; font-weight: bold;")
        add_card.mousePressEvent = lambda event: self.add_images_to_grid(grid_widget)
        layout.addWidget(add_label)
        return add_card

    def add_images_to_grid(self, grid_widget):
        max_images = getattr(grid_widget, 'max_images', 5)
        files, _ = QFileDialog.getOpenFileNames(self, "레퍼런스 이미지 선택", "", "Image files (*.png *.jpg *.jpeg)")
        if files:
            current_count = len(grid_widget.image_paths)
            available_slots = max_images - current_count
            if available_slots <= 0:
                return
            
            files_to_add = files[:available_slots]
            for file_path in files_to_add:
                if file_path not in grid_widget.image_paths:
                    grid_widget.image_paths.append(file_path)
            
            self.update_image_grid(grid_widget)

    def remove_image_card(self, image_path, grid_widget):
        # 카테고리별 레퍼런스 이미지 확인 및 삭제
        if self.pose_reference == image_path:
            self.pose_reference = None
            self.pose_ref_btn.setText("레퍼런스 업로드")
        elif self.framing_reference == image_path:
            self.framing_reference = None
            self.framing_ref_btn.setText("레퍼런스 업로드")
        elif self.angle_reference == image_path:
            self.angle_reference = None
            self.angle_ref_btn.setText("레퍼런스 업로드")
        elif self.mood_reference == image_path:
            self.mood_reference = None
            self.mood_ref_btn.setText("레퍼런스 업로드")
        # 아이템 레퍼런스 이미지 확인 및 삭제
        elif image_path in grid_widget.image_paths:
            grid_widget.image_paths.remove(image_path)

        self.update_image_grid(grid_widget)

    def update_image_grid(self, grid_widget):
        layout = grid_widget.layout()
        # Clear all widgets
        for i in reversed(range(layout.count())):
            child = layout.itemAt(i).widget()
            if child:
                child.deleteLater()

        # Add category reference images with tags first
        category_images = []
        if self.pose_reference:
            category_images.append((self.pose_reference, "포즈"))
        if self.framing_reference:
            category_images.append((self.framing_reference, "구도"))
        if self.angle_reference:
            category_images.append((self.angle_reference, "촬영방향"))
        if self.mood_reference:
            category_images.append((self.mood_reference, "분위기"))

        for image_path, tag in category_images:
            card = self.create_image_card(image_path, grid_widget, tag)
            layout.insertWidget(layout.count() - 1, card)

        # Add item reference images (no tags)
        for image_path in grid_widget.image_paths:
            card = self.create_image_card(image_path, grid_widget)
            layout.insertWidget(layout.count() - 1, card)

        # Add the add button if not at max capacity for item references
        max_images = getattr(grid_widget, 'max_images', 5)
        if len(grid_widget.image_paths) < max_images:
            add_btn = self.create_add_button(grid_widget)
            layout.insertWidget(layout.count() - 1, add_btn)

    def open_color_picker(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.image_viewer.set_drawing_color(color)

    def update_history_buttons(self, undo_enabled, redo_enabled):
        self.undo_btn.setEnabled(undo_enabled)
        self.redo_btn.setEnabled(redo_enabled)

    def setup_shortcuts(self):
        undo_action = QAction(self)
        undo_action.setShortcut(QKeySequence.Undo)
        undo_action.triggered.connect(self.image_viewer.undo)
        self.addAction(undo_action)

        redo_action = QAction(self)
        redo_action.setShortcut(QKeySequence.Redo)
        redo_action.triggered.connect(self.image_viewer.redo)
        self.addAction(redo_action)

    def on_pose_changed(self, text):
        """포즈 콤보박스 변경시 상세 입력창 표시/숨김"""
        if text == "유지":
            self.pose_detail.setVisible(False)
            self.pose_ref_btn.setVisible(False)
        else:
            self.pose_detail.setVisible(True)
            self.pose_ref_btn.setVisible(True)

            # 다른 카테고리들은 내용이 있으면 유지, 없으면 숨김
            self.framing_detail.setVisible(bool(self.framing_detail.toPlainText().strip()) and self.framing_combo.currentText() != "기존 구도 유지")
            self.framing_ref_btn.setVisible(bool(self.framing_detail.toPlainText().strip()) and self.framing_combo.currentText() != "기존 구도 유지")
            self.angle_detail.setVisible(bool(self.angle_detail.toPlainText().strip()) and self.angle_combo.currentText() != "정면")
            self.angle_ref_btn.setVisible(bool(self.angle_detail.toPlainText().strip()) and self.angle_combo.currentText() != "정면")
            self.mood_detail.setVisible(bool(self.mood_detail.toPlainText().strip()) and self.mode_combo.currentText() != "유지")
            self.mood_ref_btn.setVisible(bool(self.mood_detail.toPlainText().strip()) and self.mode_combo.currentText() != "유지")

            # 각 포즈별 도움말 설정
            placeholders = {
                "정자세": "예: 자연스럽게 서있는 자세로, 어깨는 편안히 내리고...",
                "걷는 포즈": "예: 런웨이 느낌으로 자연스러운 보폭으로 걸어가는 모습...",
                "앉은 포즈": "예: 의자나 바닥에 앉아서, 다리 위치와 상체 자세는...",
                "기대는 포즈": "예: 벽이나 난간에 기대어서, 팔과 다리 위치는...",
                "손 모션 포함": "예: 허리에 손을 얹거나 주머니에 넣는 등의 자연스러운 손동작...",
                "다이나믹 포즈": "예: 점프하거나 턴하는 등 움직임이 느껴지는 역동적인 자세...",
                "라이프스타일 포즈": "예: 책을 읽거나 커피를 마시는 등 일상적인 행동하는 모습..."
            }
            self.pose_detail.setPlaceholderText(placeholders.get(text, "포즈에 대한 자세한 설명을 입력하세요..."))

    def on_framing_changed(self, text):
        """구도 콤보박스 변경시 상세 입력창 표시/숨김"""
        if text == "기존 구도 유지":
            self.framing_detail.setVisible(False)
            self.framing_ref_btn.setVisible(False)
        else:
            self.framing_detail.setVisible(True)
            self.framing_ref_btn.setVisible(True)

            # 다른 카테고리들은 내용이 있으면 유지, 없으면 숨김
            self.pose_detail.setVisible(bool(self.pose_detail.toPlainText().strip()) and self.pose_combo.currentText() != "유지")
            self.pose_ref_btn.setVisible(bool(self.pose_detail.toPlainText().strip()) and self.pose_combo.currentText() != "유지")
            self.angle_detail.setVisible(bool(self.angle_detail.toPlainText().strip()) and self.angle_combo.currentText() != "정면")
            self.angle_ref_btn.setVisible(bool(self.angle_detail.toPlainText().strip()) and self.angle_combo.currentText() != "정면")
            self.mood_detail.setVisible(bool(self.mood_detail.toPlainText().strip()) and self.mode_combo.currentText() != "유지")
            self.mood_ref_btn.setVisible(bool(self.mood_detail.toPlainText().strip()) and self.mode_combo.currentText() != "유지")

            # 각 구도별 도움말 설정
            placeholders = {
                "전신": "예: 머리부터 발끝까지 전체 의상이 다 보이도록...",
                "상반신": "예: 허리 위쪽 위주로 상의와 액세서리가 잘 보이도록...",
                "하반신": "예: 허리 아래쪽 위주로 하의와 신발이 강조되도록...",
                "클로즈업": "예: 얼굴과 상의 디테일이 잘 보이도록 가슴 위까지...",
                "디테일 컷": "예: 소매나 소재 질감, 패턴 등 특정 부위를 확대해서...",
                "3/4 샷": "예: 허벅지 위부터 머리까지 3/4 정도 비율로...",
                "라이프스타일 컷": "예: 배경 포함하여 상황과 분위기를 연출하는 구도로..."
            }
            self.framing_detail.setPlaceholderText(placeholders.get(text, "구도에 대한 자세한 설명을 입력하세요..."))

    def on_angle_changed(self, text):
        """촬영 방향 콤보박스 변경시 상세 입력창 표시/숨김"""
        if text == "정면":
            self.angle_detail.setVisible(False)
            self.angle_ref_btn.setVisible(False)
        else:
            self.angle_detail.setVisible(True)
            self.angle_ref_btn.setVisible(True)

            # 다른 카테고리들은 내용이 있으면 유지, 없으면 숨김
            self.pose_detail.setVisible(bool(self.pose_detail.toPlainText().strip()) and self.pose_combo.currentText() != "유지")
            self.pose_ref_btn.setVisible(bool(self.pose_detail.toPlainText().strip()) and self.pose_combo.currentText() != "유지")
            self.framing_detail.setVisible(bool(self.framing_detail.toPlainText().strip()) and self.framing_combo.currentText() != "기존 구도 유지")
            self.framing_ref_btn.setVisible(bool(self.framing_detail.toPlainText().strip()) and self.framing_combo.currentText() != "기존 구도 유지")
            self.mood_detail.setVisible(bool(self.mood_detail.toPlainText().strip()) and self.mode_combo.currentText() != "유지")
            self.mood_ref_btn.setVisible(bool(self.mood_detail.toPlainText().strip()) and self.mode_combo.currentText() != "유지")

            # 각 앵글별 도움말 설정
            placeholders = {
                "좌측면": "예: 왼쪽에서 바라본 각도로 옆라인이 잘 보이도록...",
                "우측면": "예: 오른쪽에서 바라본 각도로 옆라인이 잘 보이도록...",
                "45도 각도": "예: 3/4 뷰 각도로 정면과 옆면이 적절히 섞인 각도로...",
                "후면": "예: 뒷모습이 강조되도록 등과 뒤태가 잘 보이는 각도로...",
                "하이 앵글": "예: 위에서 내려다보는 각도로 전체적인 실루엣이 보이도록...",
                "로우 앵글": "예: 아래에서 올려다보는 각도로 역동적이고 강렬한 느낌으로...",
                "디테일 앵글": "예: 특정 아이템이나 부위에 포커스를 맞춘 각도로..."
            }
            self.angle_detail.setPlaceholderText(placeholders.get(text, "촬영 각도에 대한 자세한 설명을 입력하세요..."))

    def on_mode_changed(self, text):
        """분위기 콤보박스 변경시 상세 입력창의 placeholder text 업데이트"""
        if text == "유지":
            self.mood_detail.setVisible(False)
            self.mood_ref_btn.setVisible(False)
        else:
            self.mood_detail.setVisible(True)
            self.mood_ref_btn.setVisible(True)

            # 다른 카테고리들은 내용이 있으면 유지, 없으면 숨김
            self.pose_detail.setVisible(bool(self.pose_detail.toPlainText().strip()) and self.pose_combo.currentText() != "유지")
            self.pose_ref_btn.setVisible(bool(self.pose_detail.toPlainText().strip()) and self.pose_combo.currentText() != "유지")
            self.framing_detail.setVisible(bool(self.framing_detail.toPlainText().strip()) and self.framing_combo.currentText() != "기존 구도 유지")
            self.framing_ref_btn.setVisible(bool(self.framing_detail.toPlainText().strip()) and self.framing_combo.currentText() != "기존 구도 유지")
            self.angle_detail.setVisible(bool(self.angle_detail.toPlainText().strip()) and self.angle_combo.currentText() != "정면")
            self.angle_ref_btn.setVisible(bool(self.angle_detail.toPlainText().strip()) and self.angle_combo.currentText() != "정면")

            placeholders = {
                "심플/베이직": "예: 흰색 배경에 그림자 없는 깔끔한 조명",
                "모던/미니멀": "예: 직선적인 구도와 차가운 색감의 배경",
                "세련/럭셔리": "예: 고급스러운 소품과 은은한 조명 활용",
                "캐주얼/데일리": "예: 카페나 길거리 등 일상적인 배경",
                "스포티/액티브": "예: 역동적인 구도와 야외 배경",
                "러블리/페미닌": "예: 파스텔톤 색감과 부드러운 자연광",
                "시크/도시적": "예: 야경이나 도시의 건축물을 배경으로",
                "빈티지/레트로": "예: 필름 카메라 느낌의 색감과 소품",
                "자연스러움/라이프스타일": "예: 여행지나 집과 같은 자연스러운 공간",
                "시즌감 (봄/여름/가을/겨울)": "예: 계절에 맞는 야외 배경과 색감",
                "직접입력": "원하는 분위기를 직접 입력하세요."
            }
            self.mood_detail.setPlaceholderText(placeholders.get(text, "전체적인 분위기와 컨셉을 입력하세요."))

    def update_all_visibility(self):
        """초기화 시 또는 필요시 모든 카테고리의 visibility 업데이트"""
        # 포즈
        if self.pose_combo.currentText() != "유지" and self.pose_detail.toPlainText().strip():
            self.pose_detail.setVisible(True)
            self.pose_ref_btn.setVisible(True)
        else:
            self.pose_detail.setVisible(self.pose_combo.currentText() != "유지")
            self.pose_ref_btn.setVisible(self.pose_combo.currentText() != "유지")

        # 구도
        if self.framing_combo.currentText() != "기존 구도 유지" and self.framing_detail.toPlainText().strip():
            self.framing_detail.setVisible(True)
            self.framing_ref_btn.setVisible(True)
        else:
            self.framing_detail.setVisible(self.framing_combo.currentText() != "기존 구도 유지")
            self.framing_ref_btn.setVisible(self.framing_combo.currentText() != "기존 구도 유지")

        # 촬영 방향
        if self.angle_combo.currentText() != "정면" and self.angle_detail.toPlainText().strip():
            self.angle_detail.setVisible(True)
            self.angle_ref_btn.setVisible(True)
        else:
            self.angle_detail.setVisible(self.angle_combo.currentText() != "정면")
            self.angle_ref_btn.setVisible(self.angle_combo.currentText() != "정면")

        # 분위기
        if self.mode_combo.currentText() != "유지" and self.mood_detail.toPlainText().strip():
            self.mood_detail.setVisible(True)
            self.mood_ref_btn.setVisible(True)
        else:
            self.mood_detail.setVisible(self.mode_combo.currentText() != "유지")
            self.mood_ref_btn.setVisible(self.mode_combo.currentText() != "유지")

    def upload_reference_image(self, category):
        """카테고리별 레퍼런스 이미지 업로드"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            f"{category} 레퍼런스 이미지 선택",
            "",
            "Image files (*.png *.jpg *.jpeg)"
        )

        if file_path:
            # 카테고리별로 이미지 경로 저장
            if category == 'pose':
                self.pose_reference = file_path
                self.pose_ref_btn.setText(f"포즈 레퍼런스: {os.path.basename(file_path)}")
            elif category == 'framing':
                self.framing_reference = file_path
                self.framing_ref_btn.setText(f"구도 레퍼런스: {os.path.basename(file_path)}")
            elif category == 'angle':
                self.angle_reference = file_path
                self.angle_ref_btn.setText(f"방향 레퍼런스: {os.path.basename(file_path)}")
            elif category == 'mood':
                self.mood_reference = file_path
                self.mood_ref_btn.setText(f"분위기 레퍼런스: {os.path.basename(file_path)}")

            # 레퍼런스 이미지 그리드 업데이트
            self.update_image_grid(self.image_grid_widget)

    def load_image(self, image_path):
        self.original_image_path = image_path
        pixmap = QPixmap(image_path)
        if not pixmap.isNull():
            self.image_viewer.set_photo(pixmap)
            # 원본 이미지 로드 시에는 등록하기 버튼 숨김 (업데이트된 이미지가 아니므로)
            self.register_button.setVisible(False)

    # yhkim1
    def _show_image_popup(self, image_bytes: bytes, title: str = "Image Popup"):
        """
        생성된 이미지 확인을 위한 임시 팝업창 함수
        """
        try:
            dialog = ImagePopup(image_bytes, self)
            dialog.setWindowTitle(title)
            result = dialog.exec_()

            # 확인 버튼(QDialog.Accepted)을 눌렀을 때만 이미지 업데이트
            if result == QDialog.Accepted:
                # 재생성된 이미지를 현재 편집기의 이미지 뷰어에 적용
                self.image_viewer.set_photo(dialog.pixmap)
                # 이미지가 업데이트되었으므로 등록하기 버튼 표시
                self.register_button.setVisible(True)
                return True
            return False
        except Exception as e:
            QMessageBox.critical(self, "Popup Error", f"이미지 팝업을 띄우는 중 오류 발생: {e}")
            return False

    def _read_image_as_bytes(self, image_path: str) -> bytes:
        """
        이미지 파일을 바이트 타입으로 읽어 반환합니다.
        """
        try:
            with open(image_path, 'rb') as f:
                image_bytes = f.read()
            return image_bytes
        except FileNotFoundError:
            print(f"오류: 파일을 찾을 수 없습니다 - {image_path}")
            return None
        except Exception as e:
            print(f"오류가 발생했습니다: {e}")
            return None

    def _save_bytes_as_png(self, image_bytes: bytes, output_path: str):
        """
        바이트 데이터를 PNG 파일로 저장합니다.

        Args:
          image_bytes (bytes): LLM으로부터 받은 이미지의 바이트 데이터
          output_path (str): 저장할 파일의 경로 (예: 'generated_image.png')
        """
        try:
            with open(output_path, 'wb') as f:
                f.write(image_bytes)
            print(f"이미지를 성공적으로 저장했습니다: {output_path}")
        except Exception as e:
            print(f"오류가 발생했습니다: {e}")


    def start_image_regeneration(self):
        if not self.original_image_path:
            QMessageBox.warning(self, "이미지 없음", "편집할 이미지를 먼저 로드해주세요.")
            return

        print("Collecting editor data...")
        edit_data = self.collect_editor_data()
        print(f"edit_data:\n{edit_data}")
        # edit_data = {
        #    "action":{
        #        "option":"앉은 포즈",
        #        "description":"",
        #    },
        #    "framing":{
        #        "option":"클로즈업",
        #        "description":"",
        #        "reference":""
        #    },
        #    "angle":{
        #        "option":"로우 앵글",
        #        "description":"",
        #        "reference": ""
        #    },
        #    "mood":{
        #        "option":"캐주얼/데일리",
        #        "description":"",
        #    },
        #    "reference":[
        #       "C:/Users/USER/PycharmProjects/GenCommerce/resource/test/reference_test_2.jpg",
        #       "C:/Users/USER/PycharmProjects/GenCommerce/resource/test/05_숏바지.png",
        #       "C:/Users/USER/PycharmProjects/GenCommerce/resource/test/01_부츠.png",
        #       "C:/Users/USER/PycharmProjects/GenCommerce/resource/test/reference_test_1.png",
        #       "C:/Users/USER/PycharmProjects/GenCommerce/resource/test/mood_2.jpg"
        #    ],
        #    "original_image":"C:\\Users\\USER\\PycharmProjects\\GenCommerce\\output\\guest\\lookbook_demo\\recommend\\modelshot\\model_shot_20250918_134009.png",
        #    "mask_image":"b""'\\x89PNG\r\...\\x00\\x00"}


        original_image = self._read_image_as_bytes(edit_data["original_image"])
        mask_image = edit_data['mask_image']
        reference_images = [
            self._read_image_as_bytes(path)
            for path in edit_data['reference']
        ]
        reference_images = [img for img in reference_images if img is not None]

        try:
            generated_image = self.vision_editor.regenerate_image(
                source_image=original_image,
                mask_image=mask_image,
                reference_images=reference_images,
                annotation=False
            )
            self._save_bytes_as_png(generated_image, "./generated_image_temp.png")

            # 기존
            # generated_image_shot = self.vision_editor.regenerate_image_shot(
            #     source_image=generated_image,
            #     regen_data=edit_data,
            #     reference_images=reference_images
            # )
            # yhkim1 - 구조 변경 가정
            # edit_data = {
            #     "action": {
            #         "option": "앉은 포즈",
            #         "description": "",
            #         "reference": "C:/Users/USER/PycharmProjects/GenCommerce/resource/test/reference_test_1.png"
            #     },
            #     "framing": {
            #         "option": "클로즈업",
            #         "description": "",
            #         "reference": ""
            #     },
            #     "angle": {
            #         "option": "로우 앵글",
            #         "description": "",
            #         "reference": ""
            #     },
            #     "mood": {
            #         "option": "캐주얼/데일리",
            #         "description": "",
            #         "reference": "C:/Users/USER/PycharmProjects/GenCommerce/resource/test/mood_2.jpg"
            #     },
            #     "reference": [
            #         "C:/Users/USER/PycharmProjects/GenCommerce/resource/test/reference_test_2.jpg",
            #         "C:/Users/USER/PycharmProjects/GenCommerce/resource/test/05_숏바지.png",
            #         "C:/Users/USER/PycharmProjects/GenCommerce/resource/test/01_부츠.png"
            #     ],
            #     "original_image": "C:\\Users\\USER\\PycharmProjects\\GenCommerce\\output\\guest\\lookbook_demo\\recommend\\modelshot\\model_shot_20250918_134009.png",
            #     "mask_image": "b""'\\x89PNG\r\...\\x00\\x00"}

            # edit_data에서 사용할 옵션값만 추출
            keys_to_extract = ['action', 'framing', 'angle', 'mood']
            extracted_edit_data = {key: edit_data[key] for key in keys_to_extract}

            generated_image_shot = self.vision_editor.regenerate_image_shot(
                source_image=generated_image,
                regen_data=extracted_edit_data
            )

            if generated_image_shot:
                print("Image regenerated successfully.")
                # yhkim1 - 이미지 확인용으로 만든 임시 팝업창
                image_applied = self._show_image_popup(generated_image_shot, "재생성된 이미지")
                if image_applied:
                    print("재생성된 이미지가 편집기에 적용되었습니다.")
                else:
                    print("사용자가 이미지 적용을 취소했습니다.")
                # PathManager를 사용하여 temp 디렉토리 생성
                from datetime import datetime
                from admin.path_manager import PathManager

                path_manager = PathManager()
                temp_dir = path_manager.get_recommend_temp_dir("modelshot")

                if temp_dir:
                    # 현재 시간으로 파일명 생성
                    current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
                    temp_file_path = f"{temp_dir}/generate_image_{current_time}.png"
                    self._save_bytes_as_png(generated_image_shot, temp_file_path)
                else:
                    # 폴백: 로컬 temp 디렉토리 사용
                    import os
                    temp_dir = "./temp"
                    if not os.path.exists(temp_dir):
                        os.makedirs(temp_dir)
                    current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
                    temp_file_path = f"{temp_dir}/generate_image_{current_time}.png"
                    self._save_bytes_as_png(generated_image_shot, temp_file_path)
            else:
                print("실패", "이미지 재생성에 실패했습니다. (결과 없음)")

        except Exception as e:
            print(f"An error occurred during regeneration: {e}")

    def register_image(self):
        """현재 편집기의 이미지를 상품 등록 폼에 등록하는 함수"""
        if not self.original_image_path:
            QMessageBox.warning(self, "이미지 없음", "등록할 이미지가 없습니다.")
            return

        try:
            # 현재 편집기의 이미지를 파일로 저장
            current_pixmap = self.image_viewer._photo.pixmap()
            if current_pixmap.isNull():
                QMessageBox.warning(self, "이미지 없음", "등록할 이미지가 없습니다.")
                return

            # 임시 파일로 저장 (상품 등록 폼에서 사용할 수 있도록)
            import tempfile
            import os
            temp_dir = tempfile.gettempdir()
            temp_filename = f"edited_image_{os.getpid()}_{id(self)}.png"
            temp_file_path = os.path.join(temp_dir, temp_filename)

            # 이미지 저장
            current_pixmap.save(temp_file_path)

            # 부모 위젯이 ProductForm인지 확인하고 이미지 추가
            parent_widget = self.parent()
            while parent_widget:
                if hasattr(parent_widget, 'image_grid_widget') and hasattr(parent_widget, 'add_image_from_result'):
                    # ProductForm을 찾았을 때
                    parent_widget.add_image_from_result(temp_file_path)
                    msg = QMessageBox()
                    msg.setIcon(QMessageBox.Information)
                    msg.setWindowTitle("등록 완료")
                    msg.setText("이미지가 상품 등록 폼에 추가되었습니다.")
                    msg.adjustSize()
                    msg.exec_()
                    return
                parent_widget = parent_widget.parent()

            # ProductForm을 찾지 못한 경우 일반 파일 저장
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "이미지 등록",
                "edited_image.png",
                "Image files (*.png *.jpg *.jpeg)"
            )

            if file_path:
                current_pixmap.save(file_path)
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Information)
                msg.setWindowTitle("등록 완료")
                msg.setText(f"이미지가 파일로 저장되었습니다.\n경로: {file_path}")
                msg.adjustSize()
                msg.exec_()

        except Exception as e:
            QMessageBox.critical(self, "등록 실패", f"이미지 등록 중 오류가 발생했습니다: {str(e)}")

    def handle_regeneration_result(self, new_image_path, error_message):
        self.apply_button.setEnabled(True)
        self.apply_button.setText("적용하기")

        if error_message:
            QMessageBox.critical(self, "이미지 재생성 오류", f"이미지 재생성 중 오류 발생: {error_message}")
        elif new_image_path:
            pixmap = QPixmap(new_image_path)
            if not pixmap.isNull():
                self.image_viewer.set_photo(pixmap)
                QMessageBox.information(self, "완료", "이미지 재생성이 완료되었습니다.")
            else:
                QMessageBox.warning(self, "이미지 로드 실패", f"생성된 이미지를 로드할 수 없습니다: {new_image_path}")
        else:
            QMessageBox.warning(self, "이미지 재생성", "이미지 재생성 결과가 없습니다.")

    def collect_editor_data(self):
        # 각 상세 설명 필드에서 텍스트 수집
        pose_desc = self.pose_detail.toPlainText() if self.pose_detail.isVisible() else ''
        framing_desc = self.framing_detail.toPlainText() if self.framing_detail.isVisible() else ''
        angle_desc = self.angle_detail.toPlainText() if self.angle_detail.isVisible() else ''
        mood_desc = self.mood_detail.toPlainText() if self.mood_detail.isVisible() else ''

        buffer = QBuffer()
        buffer.open(QIODevice.WriteOnly)
        self.image_viewer.mask_image.save(buffer, "PNG")
        mask_image_bytes = buffer.data().data()
        buffer.close()

        # 카테고리별 레퍼런스 이미지 수집
        reference_data = {
            'item': [path for path in getattr(self.image_grid_widget, 'image_paths', [])],  # 기존 아이템 레퍼런스 (최대 5개)
            'pose': self.pose_reference if self.pose_reference else None,  # 포즈 레퍼런스 (최대 1개)
            'framing': self.framing_reference if self.framing_reference else None,  # 구도 레퍼런스 (최대 1개)
            'angle': self.angle_reference if self.angle_reference else None,  # 방향 레퍼런스 (최대 1개)
            'mood': self.mood_reference if self.mood_reference else None  # 분위기 레퍼런스 (최대 1개)
        }

        edit_data = {
            'action': {
                'option': self.pose_combo.currentText(),
                'description': pose_desc,
                'reference': reference_data['pose'] if reference_data['pose'] else ""
            },
            'framing': {
                'option': self.framing_combo.currentText(),
                'description': framing_desc,
                'reference': reference_data['framing'] if reference_data['framing'] else ""
            },
            'angle': {
                'option': self.angle_combo.currentText(),
                'description': angle_desc,
                'reference': reference_data['angle'] if reference_data['angle'] else ""
            },
            'mood': {
                'option': self.mode_combo.currentText(),
                'description': mood_desc,
                'reference': reference_data['mood'] if reference_data['mood'] else ""
            },
            'reference': reference_data['item'],  # 아이템 레퍼런스만 (최대 5개)
            'original_image': self.original_image_path,
            'mask_image': mask_image_bytes
        }

        return edit_data




class ImageRegenerationThread(QThread):

    """이미지 재생성 스레드"""
    regeneration_completed = pyqtSignal(int, object, str)

    def __init__(self, regen_data=None, source_image=None, mask_image=None):
        super().__init__()
        self.regen_data = regen_data
        self.source_image = source_image
        self.mask_image = mask_image
        self.temp_folder = "../temp"

        # Gemini 초기화
        try:
            from common.gemini import Gemini
            self.gemini = Gemini()
        except ImportError as e:
            print(f"error:{e}")

    def run(self):
        """이미지 재생성 실행"""
        try:
            new_image_path = self.regenerate()
            self.regeneration_completed.emit(new_image_path, "")

        except Exception as e:
            self.regeneration_completed.emit(None, str(e))
        finally:
            import gc
            gc.collect()

    def start_regeneration_thread(self, options):
        """재생성 스레드 시작"""
        # 재생성 스레드 생성 및 시작
        self.regeneration_thread = ImageRegenerationThread(options)
        self.regeneration_thread.finished.connect(self.on_regeneration_finished)
        self.regeneration_thread.progress.connect(self.on_regeneration_progress)
        self.regeneration_thread.start()

    def on_regeneration_finished(self, result):
        """재생성 완료 시 호출"""
        self.apply_button.setEnabled(True)
        self.apply_button.setText("적용하기")

        if result and 'error' not in result:
            # 성공적으로 재생성된 경우
            new_image_path = result.get('generated_image_path')
            if new_image_path:
                # 새로운 이미지로 뷰어 업데이트
                self.image_viewer.load_image(new_image_path)
                QMessageBox.information(self, '완료', '이미지가 성공적으로 재생성되었습니다.')
            else:
                QMessageBox.warning(self, '결과 없음', '재생성된 이미지를 찾을 수 없습니다.')
        else:
            # 오류 발생한 경우
            error_msg = result.get('error', '알 수 없는 오류가 발생했습니다.') if result else '재생성에 실패했습니다.'
            QMessageBox.critical(self, '재생성 실패', error_msg)

class VisionEditor():
    def __init__(self):
        # 설정 파서로부터 입력 디렉토리 및 프로젝트명 등 받아오기
        self.args = parser()

        # Gemini models
        self.gemini = GeminiEditor()
        self.model = "gemini-2.0-flash"  # gemini-2.5-flash
        self.model_nb = "gemini-2.5-flash-image-preview"
        self.prompt = EDITOR()

    def _read_image_as_bytes(self, image_path: str) -> bytes:
        """
        이미지 파일을 바이트 타입으로 읽어 반환합니다.
        """
        try:
            with open(image_path, 'rb') as f:
                image_bytes = f.read()
            return image_bytes
        except FileNotFoundError:
            print(f"오류: 파일을 찾을 수 없습니다 - {image_path}")
            return None
        except Exception as e:
            print(f"오류가 발생했습니다: {e}")
            return None

    def _save_bytes_as_png(self, image_bytes: bytes, output_path: str):
        """
        바이트 데이터를 PNG 파일로 저장합니다.

        Args:
          image_bytes (bytes): LLM으로부터 받은 이미지의 바이트 데이터
          output_path (str): 저장할 파일의 경로 (예: 'generated_image.png')
        """
        try:
            with open(output_path, 'wb') as f:
                f.write(image_bytes)
            print(f"이미지를 성공적으로 저장했습니다: {output_path}")
        except Exception as e:
            print(f"오류가 발생했습니다: {e}")


    # --- [Main] 메타데이터 추출 ---
    # 기존 버전
    def regenerate_image(self, source_image: bytes, mask_image: bytes, reference_images: list,
                          annotation: bool) -> bytes:
        """
        편집 기능을 통해 이미지 의상 재생성하는 함수
        """
        try:
            print("bytes 데이터를 PIL Image 객체로 변환합니다...")
            pil_source_image = Image.open(BytesIO(source_image))
            pil_mask_image = Image.open(BytesIO(mask_image))

            contents = [
                pil_source_image,
                pil_mask_image
            ]

            print("레퍼런스 이미지를 체크합니다...")
            print(f"발견된 레퍼런스 이미지 {len(reference_images)}개")
            if reference_images and isinstance(reference_images, list):
                # PIL 이미지 객체들을 저장할 리스트를 생성합니다.
                pil_reference_images = []
                # 리스트에 있는 각 이미지 바이트에 대해 반복 작업을 수행합니다.
                for ref_image_bytes in reference_images:
                    pil_img = Image.open(BytesIO(ref_image_bytes))
                    pil_reference_images.append(pil_img)

                # contents 리스트에 pil_reference_images 리스트의 모든 원소를 추가합니다.
                contents.extend(pil_reference_images)
        except Exception as e:
            print(f"이미지 바이트를 PIL 이미지로 변환하는 중 오류 발생: {e}")
            return None

        # 최종적으로 LLM에 전달한 contents
        prompt = self.prompt.model_shot_edit_prompt(annotation)
        contents.insert(1, prompt)

        # 3. 수정된 contents 리스트를 API에 전달합니다. (GeminiEditor의 메소드 호출 방식에 맞게 조정)
        generated_image = self.gemini.regenerate_image_editor(contents, self.model_nb)
        print(f"의상 변경 기법 프롬프트:\n{prompt}")

        if generated_image:
            print(type(generated_image))  # <class 'PIL.PngImagePlugin.PngImageFile'> 출력 확인
            # 3. 성공 시, PIL Image 객체를 bytes로 변환하여 반환합니다.
            buffer = BytesIO()
            generated_image.save(buffer, format="PNG")
            image_bytes = buffer.getvalue()
            return image_bytes

            # 4. 실패 시, None을 반환합니다.
        print("<class 'NoneType'>")  # 실패 시 NoneType 출력
        return None

    def regenerate_image(self, source_image: bytes, mask_image: bytes, reference_images: list,
                          annotation: bool) -> bytes:
        """
        편집 기능을 통해 이미지 의상 재생성하는 함수
        """
        try:
            print("bytes 데이터를 PIL Image 객체로 변환합니다...")
            pil_source_image = Image.open(BytesIO(source_image))
            pil_mask_image = Image.open(BytesIO(mask_image))

            contents = [
                pil_source_image,
                pil_mask_image
            ]

            print("레퍼런스 이미지를 체크합니다...")
            print(f"발견된 레퍼런스 이미지 {len(reference_images)}개")
            if reference_images and isinstance(reference_images, list):
                # PIL 이미지 객체들을 저장할 리스트를 생성합니다.
                pil_reference_images = []
                # 리스트에 있는 각 이미지 바이트에 대해 반복 작업을 수행합니다.
                for ref_image_bytes in reference_images:
                    pil_img = Image.open(BytesIO(ref_image_bytes))
                    pil_reference_images.append(pil_img)

                # contents 리스트에 pil_reference_images 리스트의 모든 원소를 추가합니다.
                contents.extend(pil_reference_images)
        except Exception as e:
            print(f"이미지 바이트를 PIL 이미지로 변환하는 중 오류 발생: {e}")
            return None

        # 최종적으로 LLM에 전달한 contents
        prompt = self.prompt.model_shot_edit_prompt(annotation)
        contents.insert(1, prompt)

        # 3. 수정된 contents 리스트를 API에 전달합니다. (GeminiEditor의 메소드 호출 방식에 맞게 조정)
        generated_image = self.gemini.regenerate_image_editor(contents, self.model_nb)
        print(f"의상 변경 기법 프롬프트:\n{prompt}")

        if generated_image:
            print(type(generated_image))  # <class 'PIL.PngImagePlugin.PngImageFile'> 출력 확인
            # 3. 성공 시, PIL Image 객체를 bytes로 변환하여 반환합니다.
            buffer = BytesIO()
            generated_image.save(buffer, format="PNG")
            image_bytes = buffer.getvalue()
            return image_bytes

            # 4. 실패 시, None을 반환합니다.
        print("<class 'NoneType'>")  # 실패 시 NoneType 출력
        return None


    # 기존
    # def regenerate_image_shot(self, source_image: bytes, regen_data: dict, reference_images: list) -> bytes:
    #     """
    #     촬영기법 반영하여 이미지 재생성하는 함수
    #     """
    #     try:
    #         print("bytes 데이터를 PIL Image 객체로 변환합니다...")
    #         pil_source_image = Image.open(BytesIO(source_image))
    #
    #         contents = [pil_source_image]
    #
    #         print("레퍼런스 이미지를 체크합니다...")
    #         print(f"발견된 레퍼런스 이미지 {len(reference_images)}개")
    #         if reference_images and isinstance(reference_images, list):
    #             # PIL 이미지 객체들을 저장할 리스트를 생성합니다.
    #             pil_reference_images = []
    #             # 리스트에 있는 각 이미지 바이트에 대해 반복 작업을 수행합니다.
    #             for ref_image_bytes in reference_images:
    #                 pil_img = Image.open(BytesIO(ref_image_bytes))
    #                 pil_reference_images.append(pil_img)
    #
    #             # contents 리스트에 pil_reference_images 리스트의 모든 원소를 추가합니다.
    #             contents.extend(pil_reference_images)
    #     except Exception as e:
    #         print(f"이미지 바이트를 PIL 이미지로 변환하는 중 오류 발생: {e}")
    #         return None
    #
    #     # 촬영 옵션 반영 프롬프트
    #     prompt = self.prompt.model_pose_edit_prompt(regen_data)
    #     print(f"촬영 기법 프롬프트:\n{prompt}")
    #
    #     # 최종적으로 LLM에 전달한 contents
    #     contents.insert(1, prompt)
    #
    #     # 3. 수정된 contents 리스트를 API에 전달합니다. (GeminiEditor의 메소드 호출 방식에 맞게 조정)
    #     generated_image = self.gemini.regenerate_image_editor(contents, self.model_nb)
    #
    #     if generated_image:
    #         print(type(generated_image))  # <class 'PIL.PngImagePlugin.PngImageFile'> 출력 확인
    #         # 3. 성공 시, PIL Image 객체를 bytes로 변환하여 반환합니다.
    #         buffer = BytesIO()
    #         generated_image.save(buffer, format="PNG")
    #         image_bytes = buffer.getvalue()
    #         return image_bytes
    #
    #         # 4. 실패 시, None을 반환합니다.
    #     print("<class 'NoneType'>")  # 실패 시 NoneType 출력
    #     return None
    # yhkim1 - 구조 변경 가정
    def _is_valid_image_path(self,path_string):
        """
        주어진 문자열이 비어있지 않고 유효한 이미지 파일 경로 형식인지 확인합니다.
        """
        if not path_string:
            return False
        # 문자열을 소문자로 변환하여 확장자를 검사합니다.

        # 유효한 이미지 파일 확장자 목록
        if path_string.lower().endswith(('.png', '.jpg', '.jpeg')):
            return True
        return False

    def regenerate_image_shot(self, source_image: bytes, regen_data: dict) -> bytes:
        """
        촬영기법 반영하여 이미지 재생성하는 함수
        """

        print("bytes 데이터를 PIL Image 객체로 변환합니다...")
        pil_source_image = Image.open(BytesIO(source_image))

        contents = [pil_source_image]
        image_num=1 # 원본 이미지

        # regen_data의 각 항목을 순회하며 reference 값이 비어있지 않은 경우 처리
        print("참고 이미지들을 PIL Image 객체로 변환하여 리스트에 추가합니다...")
        for category, data in regen_data.items():
            reference_path = data.get("reference")

            # reference_path가 존재하고, 빈 문자열이 아닌 경우
            if reference_path:
                try:
                    print(f"'{category}'의 참고 이미지 경로를 읽습니다: {reference_path}")
                    # 파일을 바이너리 읽기 모드로 열기
                    with open(reference_path, 'rb') as f:
                        image_bytes = f.read()

                    # 바이트 데이터를 PIL Image 객체로 변환
                    pil_reference_image = Image.open(BytesIO(image_bytes))

                    # contents 리스트에 추가
                    contents.append(pil_reference_image)
                    image_num += 1
                    regen_data[category]["image_num"] = image_num

                except FileNotFoundError:
                    print(f"경고: '{reference_path}' 경로에서 파일을 찾을 수 없습니다. 이 파일은 건너뜁니다.")
                except IOError:
                    print(f"경고: '{reference_path}' 파일은 유효한 이미지 파일이 아니거나 손상되었습니다. 이 파일은 건너뜁니다.")
                except Exception as e:
                    print(f"'{reference_path}' 파일을 처리하는 중 에러가 발생했습니다: {e}")

        print(f"총 {len(contents)}개의 이미지가 리스트에 준비되었습니다.")

        # 촬영 옵션 반영 프롬프트
        prompt = self.prompt.model_pose_edit_prompt(regen_data)
        print(f"촬영 기법 프롬프트:\n{prompt}")

        # 최종적으로 LLM에 전달한 contents
        contents.insert(1, prompt)

        # 3. 수정된 contents 리스트를 API에 전달합니다. (GeminiEditor의 메소드 호출 방식에 맞게 조정)
        generated_image = self.gemini.regenerate_image_editor(contents, self.model_nb)

        if generated_image:
            print(type(generated_image))  # <class 'PIL.PngImagePlugin.PngImageFile'> 출력 확인
            # 3. 성공 시, PIL Image 객체를 bytes로 변환하여 반환합니다.
            buffer = BytesIO()
            generated_image.save(buffer, format="PNG")
            image_bytes = buffer.getvalue()
            return image_bytes

            # 4. 실패 시, None을 반환합니다.
        print("<class 'NoneType'>")  # 실패 시 NoneType 출력
        return None


    # 로컬 테스트용
    @timefn
    def run(self):
        # yhkim1 테스트용 임시 데이터
        source_image = self._read_image_as_bytes("../resource/test/08_result.png")
        mask_image = self._read_image_as_bytes("../resource/test/mask_test_3.png")
        reference_image_1 = self._read_image_as_bytes("../resource/test/reference_test_1.png")
        reference_image_2 = self._read_image_as_bytes("../resource/test/reference_test_2.jpg")
        reference_images=[reference_image_2]
        annotation = False # False > 주석 없음
        regen_data = {
            "pose":"앉은 포즈",
            "projection": "45도 각도",
            "shot": "클로즈업",
            "mood": "러블리/페미닌"
        }
        # print('-----------모델 의상 변경-----------')
        # result_image_bytes = self.regenerate_image(source_image, mask_image, reference_images, annotation)
        # print(type(result_image_bytes))
        # result_image_path = "../resource/test/output.png"
        # self._save_bytes_as_png(result_image_bytes, result_image_path)

        print('-----------모델 포즈 변경-----------')
        result_image_bytes = self._read_image_as_bytes("../resource/test/output.png")
        reference_image_1 = self._read_image_as_bytes("../resource/test/pose_5.png")
        reference_image_2 = self._read_image_as_bytes("../resource/test/mood_2.jpg")
        reference_images = [reference_image_1, reference_image_2]
        result_image_pose_bytes = self.regenerate_image_shot(result_image_bytes, regen_data, reference_images)
        print(type(result_image_pose_bytes))
        result_image_pose_path = "../resource/test/output_pose.png"
        self._save_bytes_as_png(result_image_pose_bytes, result_image_pose_path)
        return


if __name__ == '__main__':
    import sys
    app = QApplication(sys.argv)
    editor = AiEditorWidget()
    editor.setWindowTitle("Copyright © 2025 ITCEN CLOIT All rights reserved.")

    test_image_path = "../resource/test/08_result.png" # Create a dummy image for testing
    if os.path.exists(test_image_path):
        editor.load_image(test_image_path)
    editor.show()
    sys.exit(app.exec_())
