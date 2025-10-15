import os
from io import BytesIO
import base64
import io

from PIL import Image
import vertexai
from vertexai.vision_models import Image as VertexImage, ImageGenerationModel

from common.gemini import Gemini
from common import prompt
import tempfile

from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFileDialog, QGroupBox, QComboBox, QTextEdit,QGraphicsView, QLineEdit,
    QGraphicsScene, QGraphicsPixmapItem, QFrame,
    QSlider, QRadioButton, QButtonGroup, QFormLayout, QColorDialog, QAction, QMessageBox,
    QDialog, QScrollArea, QInputDialog, QGridLayout, QCheckBox
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


class FinalSaveDialog(QDialog):
    def __init__(self, history, parent=None):
        super().__init__(parent)
        self.setWindowTitle("최종 저장할 이미지 선택")
        self.setModal(True)
        self.setMinimumSize(600, 400)

        self.history = history
        self.checkboxes = []

        main_layout = QVBoxLayout(self)

        # Scroll Area for the grid
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        content_widget = QWidget()
        scroll_area.setWidget(content_widget)
        grid_layout = QGridLayout(content_widget)
        grid_layout.setSpacing(10)

        # Populate grid
        for i, item in enumerate(self.history):
            row, col = i // 3, i % 3

            container = QWidget()
            container_layout = QVBoxLayout(container)
            container.setContentsMargins(0,0,0,0)

            pixmap = item["pixmap"]
            image_path = item["image_path"]

            img_label = QLabel()
            img_label.setPixmap(pixmap.scaled(150, 150, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            img_label.setAlignment(Qt.AlignCenter)

            checkbox = QCheckBox(f"Step {i+1}")
            checkbox.setProperty("image_path", image_path) # Store path in property

            container_layout.addWidget(img_label)
            container_layout.addWidget(checkbox)
            self.checkboxes.append(checkbox)

            grid_layout.addWidget(container, row, col)

        main_layout.addWidget(scroll_area)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        cancel_button = QPushButton("취소")
        cancel_button.clicked.connect(self.reject)
        
        save_button = QPushButton("저장")
        save_button.setDefault(True)
        save_button.clicked.connect(self.on_save)
        
        button_layout.addWidget(cancel_button)
        button_layout.addWidget(save_button)
        
        main_layout.addLayout(button_layout)

    def on_save(self):
        self.selected_paths = []
        for checkbox in self.checkboxes:
            if checkbox.isChecked():
                self.selected_paths.append(checkbox.property("image_path"))
        
        if not self.selected_paths:
            QMessageBox.warning(self, "선택 없음", "저장할 이미지를 하나 이상 선택해주세요.")
            return

        self.accept()

    def get_selected_paths(self):
        return self.selected_paths



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
        color.setAlpha(204)
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

class HistoryThumbnail(QFrame):
    clicked = pyqtSignal(int)

    def __init__(self, index, pixmap, description, is_selected=False, parent=None):
        super().__init__(parent)
        self.index = index
        self.setFrameShape(QFrame.StyledPanel)
        self.setFixedSize(230, 70)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)

        # Image
        pixmap_label = QLabel()
        pixmap_label.setFixedSize(60, 60)
        pixmap_label.setPixmap(pixmap.scaled(60, 60, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        pixmap_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(pixmap_label)

        # Description
        desc_label = QLabel(f"<b>Step {index + 1}</b><br>{description}")
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label, 1)

        self.set_selected(is_selected)

    def set_selected(self, selected):
        if selected:
            self.setStyleSheet("background-color: #E0EAFB; border: 1px solid #A23B72;")
        else:
            self.setStyleSheet("background-color: white; border: 1px solid #CCCCCC;")

    def mousePressEvent(self, event):
        self.clicked.emit(self.index)


class AiEditorWidget(QWidget):
    back_requested = pyqtSignal()
    finalSaveCompleted = pyqtSignal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.reference_paths = []
        self.original_image_path = None
        self.vision_editor = VisionEditor()

        # Image History
        self.image_history = []
        self.history_index = -1




        self.init_ui()

    def segment_foreground(self):
        if not self.original_image_path:
            QMessageBox.warning(self, "이미지 없음", "편집할 이미지를 먼저 로드해주세요.")
            return

        try:
            self.segment_button.setEnabled(False)
            self.segment_button.setText("분리 중...")
            QApplication.processEvents() # Update UI

            # Get original image bytes
            original_pixmap = self.image_viewer._photo.pixmap()
            buffer = QBuffer()
            buffer.open(QIODevice.WriteOnly)
            original_pixmap.save(buffer, "PNG")
            image_bytes = buffer.data()

            # Call segmentation
            mask_bytes = self.vision_editor.segment_image(image_bytes)

            if mask_bytes:
                mask_image = QImage()
                mask_image.loadFromData(mask_bytes)

                # The generated mask is likely black and white. We need to make it transparent where it's black.
                processed_mask = QImage(mask_image.size(), QImage.Format_ARGB32)
                processed_mask.fill(Qt.transparent)
                painter = QPainter(processed_mask)
                for y in range(mask_image.height()):
                    for x in range(mask_image.width()):
                        pixel_color = QColor(mask_image.pixel(x, y))
                        if pixel_color.red() > 128: # If white
                            if self.mask_keep_radio.isChecked():
                                painter.setPen(self.image_viewer.drawing_color)
                                painter.drawPoint(x, y)
                        else: # if black
                            if self.mask_change_radio.isChecked():
                                painter.setPen(self.image_viewer.drawing_color)
                                painter.drawPoint(x, y)
                painter.end()

                # Combine with existing mask
                final_painter = QPainter(self.image_viewer.mask_image)
                final_painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
                final_painter.drawImage(0, 0, processed_mask)
                final_painter.end()

                self.image_viewer.viewport().update()
                QMessageBox.information(self, "완료", "전경/배경 분리가 완료되었습니다.")
            else:
                QMessageBox.warning(self, "오류", "전경/배경 분리에 실패했습니다.")

        except Exception as e:
            QMessageBox.critical(self, "오류", f"세그멘테이션 중 오류 발생: {e}")
        finally:
            self.segment_button.setEnabled(True)
            self.segment_button.setText("전경/배경 분리")



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

        self.upscale_btn = QPushButton("해상도 향상")
        tools_layout.addWidget(self.upscale_btn)
        self.upscale_btn.clicked.connect(self.upscale_image)




        # Undo/Redo buttons (moved inside tools_layout)
        undo_redo_layout = QHBoxLayout()
        self.undo_btn = QPushButton("실행 취소")
        self.undo_btn.setIcon(QIcon(os.path.join(os.path.dirname(os.path.abspath(__file__)),"resource/icon/backward.png")))
        self.undo_btn.setToolTip("실행 취소 (Ctrl+Z)")
        self.redo_btn = QPushButton("다시 실행")
        self.redo_btn.setIcon(QIcon(os.path.join(os.path.dirname(os.path.abspath(__file__)),"resource/icon/next.png")))
        self.redo_btn.setToolTip("다시 실행 (Ctrl+Y)")

        button_style = '''
            QPushButton {
                background-color: #FFFFFF;
                border: 1px solid #CCCCCC;
                border-radius: 4px;
                padding: 5px;res
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

        # 2.1 Subject Type
        # 피사체 유형 섹션 제거

        # 2.2 Segmentation & Masking
        seg_group = QGroupBox("영역 선택 및 마스크")
        seg_layout = QVBoxLayout(seg_group)

        self.segment_button = QPushButton("전경/배경 분리")
        self.segment_button.clicked.connect(self.segment_foreground)
        seg_layout.addWidget(self.segment_button)
        self.mask_keep_radio = QRadioButton("선택 영역 유지")
        self.mask_change_radio = QRadioButton("선택 영역 변경")
        self.mask_change_radio.setChecked(True)

        seg_layout.addWidget(self.mask_keep_radio)
        seg_layout.addWidget(self.mask_change_radio)
        ai_options_layout.addWidget(seg_group)

        # 2.2 Detailed Controls
        # 상세 옵션 UI가 제거되었습니다.
        
        # Add stretch to align bottom with reference image layout
        ai_options_layout.addStretch()

        # Add panels to left container
        left_main_layout.addWidget(tools_panel)

        # History Panel
        history_panel = QGroupBox("히스토리")
        history_panel_layout = QVBoxLayout(history_panel)
        self.history_scroll_area = QScrollArea()
        self.history_scroll_area.setWidgetResizable(True)
        self.history_scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.history_scroll_area.setMinimumHeight(300)
        self.history_widget = QWidget()
        self.history_layout = QVBoxLayout(self.history_widget)
        self.history_layout.setContentsMargins(0,0,0,0)
        self.history_layout.setSpacing(3)
        self.history_layout.addStretch()
        self.history_scroll_area.setWidget(self.history_widget)
        history_panel_layout.addWidget(self.history_scroll_area)
        left_main_layout.addWidget(history_panel)
        left_main_layout.addWidget(ai_options_panel)

        # --- Center/Right Panel ---
        center_container = QWidget()
        center_layout = QVBoxLayout(center_container)
        center_layout.setContentsMargins(0, 0, 0, 0)

        # 1. Image Viewer
        image_viewer_group = QGroupBox("이미지 편집")
        image_viewer_layout = QVBoxLayout(image_viewer_group)

        # Layout for title and final save button
        title_layout = QHBoxLayout()
        title_label = QLabel("이미지 편집") # Re-add a label for the title
        title_layout.addWidget(title_label, 1)
        self.final_save_btn = QPushButton("최종 저장")
        self.final_save_btn.clicked.connect(self.open_final_save_dialog)
        self.final_save_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745; 
                color: white; 
                padding: 5px 10px; 
                font-weight: bold;
                border-radius: 5px;
                border: none;
            }
            QPushButton:hover { background-color: #218838; }
            QPushButton:pressed { background-color: #1e7e34; }
        """)
        title_layout.addWidget(self.final_save_btn)
        image_viewer_layout.addLayout(title_layout)


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
        bottom_layout.setContentsMargins(5, 5, 5, 5)
        bottom_layout.setSpacing(10)

        self.user_prompt_input = QLineEdit()
        self.user_prompt_input.setPlaceholderText("사용자 프롬프트를 입력하세요...")
        self.user_prompt_input.setMinimumHeight(40)
        bottom_layout.addWidget(self.user_prompt_input, 1)

        self.apply_button = QPushButton("적용하기")
        self.apply_button.setMinimumHeight(40)
        self.apply_button.setMinimumWidth(100)
        self.apply_button.setIcon(QIcon(os.path.join(os.path.dirname(os.path.abspath(__file__)), "resource/icon/ai-editor.png")))

        self.apply_button.setStyleSheet("""
            QPushButton {
                background-color: #A23B72; 
                color: white; 
                padding: 10px 20px; 
                font-weight: bold;
                border-radius: 5px;
                border: none;
            }
            QPushButton:hover {
                background-color: #8A2F5F;
            }
            QPushButton:pressed {
                background-color: #6D2349;
            }
        """)
        self.apply_button.clicked.connect(self.start_image_regeneration)

        bottom_layout.addWidget(self.apply_button)

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
        card.setFixedSize(96, 116)  # 태그 공간을 위해 높이 증가
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
        img_label.setFixedSize(90, 90)  # 태그 공간을 위해 높이 조정
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
        add_card.setFixedSize(96, 96)
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
        # 아이템 레퍼런스 이미지 확인 및 삭제
        if image_path in grid_widget.image_paths:
            grid_widget.image_paths.remove(image_path)

        self.update_image_grid(grid_widget)

    def update_image_grid(self, grid_widget):
        layout = grid_widget.layout()
        max_images = getattr(grid_widget, 'max_images', 5)

        # Clear all items from the layout
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        # Add category reference images with tags first
        # 카테고리 레퍼런스 기능 제거

        # Add item reference images (no tags)
        for image_path in grid_widget.image_paths:
            card = self.create_image_card(image_path, grid_widget)
            layout.addWidget(card)

        # Add the add button if not at max capacity for item references
        if len(grid_widget.image_paths) < max_images:
            add_btn = self.create_add_button(grid_widget)
            layout.addWidget(add_btn)

        layout.addStretch()

    def new_from_text(self):
        text, ok = QInputDialog.getText(self, '텍스트로 새로 만들기', '생성할 이미지에 대한 프롬프트를 입력하세요:')
        if ok and text:
            try:
                self.text_to_image_btn.setEnabled(False)
                self.text_to_image_btn.setText("생성 중...")
                QApplication.processEvents() # Update UI

                # Call text_to_image
                image_bytes = self.vision_editor.text_to_image(text)

                if image_bytes:
                    # Save to a temporary file and load it
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as f:
                        f.write(image_bytes)
                        self.load_image(f.name)
                    QMessageBox.information(self, "완료", "이미지 생성이 완료되었습니다.")
                else:
                    QMessageBox.warning(self, "오류", "이미지 생성에 실패했습니다.")

            except Exception as e:
                QMessageBox.critical(self, "오류", f"이미지 생성 중 오류 발생: {e}")
            finally:
                self.text_to_image_btn.setEnabled(True)
                self.text_to_image_btn.setText("텍스트로 새로 만들기")



    def upscale_image(self):
        if not self.original_image_path:
            QMessageBox.warning(self, "이미지 없음", "편집할 이미지를 먼저 로드해주세요.")
            return

        try:
            self.upscale_btn.setEnabled(False)
            self.upscale_btn.setText("업스케일 중...")
            QApplication.processEvents() # Update UI

            # Get original image bytes
            original_pixmap = self.image_viewer._photo.pixmap()
            buffer = QBuffer()
            buffer.open(QIODevice.WriteOnly)
            original_pixmap.save(buffer, "PNG")
            image_bytes = buffer.data()

            # Call upscale
            upscaled_bytes = self.vision_editor.upscale_image(image_bytes)

            if upscaled_bytes:
                image_applied = self._show_image_popup(upscaled_bytes, "업스케일된 이미지")
                if image_applied:
                    print("업스케일된 이미지가 편집기에 적용되었습니다.")
                else:
                    print("사용자가 이미지 적용을 취소했습니다.")
            else:
                QMessageBox.warning(self, "오류", "이미지 업스케일에 실패했습니다.")

        except Exception as e:
            QMessageBox.critical(self, "오류", f"업스케일 중 오류 발생: {e}")
        finally:
            self.upscale_btn.setEnabled(True)
            self.upscale_btn.setText("업스케일")

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



    def load_image(self, image_path):
        self.original_image_path = image_path
        pixmap = QPixmap(image_path)
        if not pixmap.isNull():
            # This is a new image, so it starts a new history
            self.image_history = []
            self.history_index = -1
            self.image_viewer.set_photo(pixmap) # set_photo must be called before add_to_history
            self.add_to_history(pixmap, "원본 이미지 로드")

    # yhkim1
    def _show_image_popup(self, image_bytes: bytes, title: str = "Image Popup", save_path: str = None):
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
                # save_path가 제공된 경우 파일 경로와 함께 히스토리에 추가
                self.add_to_history(dialog.pixmap, title, image_path=save_path)
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

        # 버튼 비활성화 및 로딩 표시
        self.apply_button.setEnabled(False)
        self.apply_button.setText("생성 중...")
        QApplication.processEvents()  # UI 업데이트

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
                user_prompt=edit_data.get('user_prompt', ''),
                annotation=False
            )

            if not generated_image:
                QMessageBox.warning(self, "오류", "첫 번째 이미지 생성에 실패했습니다.")
                return

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
            keys_to_extract = ['action', 'framing', 'angle', 'mood', 'user_prompt']
            extracted_edit_data = {key: edit_data.get(key) for key in keys_to_extract}
            extracted_edit_data = {k: v for k, v in extracted_edit_data.items() if v is not None}

            generated_image_shot = self.vision_editor.regenerate_image_shot(
                source_image=generated_image,
                regen_data=extracted_edit_data
            )

            if not generated_image_shot:
                QMessageBox.warning(self, "오류", "최종 이미지 생성에 실패했습니다.")
                return

            if generated_image_shot:
                print("Image regenerated successfully.")

                # 먼저 파일 경로 생성 (저장은 사용자가 확인을 눌렀을 때만)
                # 원본 이미지 경로를 기반으로 새 파일명 생성
                original_dir = os.path.dirname(self.original_image_path)
                original_name = os.path.splitext(os.path.basename(self.original_image_path))[0]
                original_ext = os.path.splitext(self.original_image_path)[1]

                # 기존 파일명에서 숫자 접미사와 히스토리 접미사 제거 (예: _changed_1, _history_0 -> _changed)
                import re
                base_name = re.sub(r'(_\d+|_history_\d+)$', '', original_name)

                # 같은 디렉토리에서 다음 번호 찾기
                counter = 1
                while True:
                    new_file_path = os.path.join(original_dir, f"{base_name}_{counter}{original_ext}")
                    if not os.path.exists(new_file_path):
                        break
                    counter += 1

                # 팝업으로 이미지 확인 및 저장 경로 전달
                image_applied = self._show_image_popup(generated_image_shot, "재생성된 이미지", save_path=new_file_path)

                if image_applied:
                    # 확인을 눌렀을 때만 파일 저장
                    self._save_bytes_as_png(generated_image_shot, new_file_path)
                    print(f"이미지 저장됨: {new_file_path}")
                    print("재생성된 이미지가 편집기에 적용되었습니다.")

                    # 현재 작업 중인 이미지 경로 업데이트
                    self.original_image_path = new_file_path

                    # 입력창 초기화
                    self.user_prompt_input.clear()
                else:
                    print("사용자가 이미지 적용을 취소했습니다.")
            else:
                print("실패", "이미지 재생성에 실패했습니다. (결과 없음)")

        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"An error occurred during regeneration: {e}")
            print(f"Traceback:\n{error_details}")
            QMessageBox.critical(self, "오류", f"이미지 재생성 중 오류가 발생했습니다:\n{str(e)}")
        finally:
            # 버튼 다시 활성화
            self.apply_button.setEnabled(True)
            self.apply_button.setText("적용하기")



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
        # ... (existing code to collect pose_desc, etc.)

        user_prompt = self.user_prompt_input.text()
        mask_image_bytes = self.get_mask_bytes()
        reference_data = self.get_reference_data()

        edit_data = {
            'user_prompt': user_prompt,
            'mask_image': mask_image_bytes,
            'original_image': self.original_image_path,
            'reference': reference_data['item']
        }



        return edit_data

    def get_mask_bytes(self):
        buffer = QBuffer()
        buffer.open(QIODevice.WriteOnly)
        self.image_viewer.mask_image.save(buffer, "PNG")
        mask_image_bytes = buffer.data().data()
        buffer.close()
        return mask_image_bytes

    def get_reference_data(self):
        return {
            'item': [path for path in getattr(self.image_grid_widget, 'image_paths', [])]
        }

    def add_to_history(self, pixmap, description="", image_path=None):
        # If we are not at the end of the history (i.e., we did an undo), truncate the future
        if self.history_index < len(self.image_history) - 1:
            self.image_history = self.image_history[:self.history_index + 1]

        # 이미지 파일 경로가 제공되지 않으면 히스토리용 임시 파일로 저장
        if not image_path:
            # 원본 이미지 디렉토리에 히스토리 파일 저장
            if self.original_image_path:
                original_dir = os.path.dirname(self.original_image_path)
                original_name = os.path.splitext(os.path.basename(self.original_image_path))[0]
                original_ext = os.path.splitext(self.original_image_path)[1]

                # 히스토리 인덱스를 파일명에 포함
                history_num = len(self.image_history)
                image_path = os.path.join(original_dir, f"{original_name}_history_{history_num}{original_ext}")

                # Pixmap을 파일로 저장
                pixmap.save(image_path)

        # Add new state
        self.image_history.append({
            "pixmap": pixmap.copy(),
            "description": description,
            "image_path": image_path
        })
        self.history_index = len(self.image_history) - 1

        # 현재 작업 중인 이미지 경로 업데이트
        if image_path:
            self.original_image_path = image_path

        # Update UI
        self.update_history_panel()
        self.update_history_buttons(False, False)

    def update_history_panel(self):
        # Clear existing widgets
        while self.history_layout.count() > 1: # Keep the stretch
            child = self.history_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        for i, item in enumerate(self.image_history):
            is_selected = (i == self.history_index)
            thumbnail = HistoryThumbnail(i, item["pixmap"], item["description"], is_selected)
            thumbnail.clicked.connect(self.load_from_history)
            self.history_layout.insertWidget(self.history_layout.count() - 1, thumbnail)

        # Ensure the selected item is visible
        if self.history_index >= 0:
            QApplication.processEvents()
            last_added_widget = self.history_layout.itemAt(self.history_index).widget()
            if last_added_widget:
                self.history_scroll_area.ensureWidgetVisible(last_added_widget)

    def load_from_history(self, index):
        if 0 <= index < len(self.image_history):
            self.history_index = index
            item = self.image_history[index]
            self.image_viewer.set_photo(item["pixmap"]) # This resets mask history, which is fine

            # 현재 작업 중인 이미지 경로 업데이트
            if "image_path" in item and item["image_path"]:
                self.original_image_path = item["image_path"]

            self.update_history_panel()
            self.update_history_buttons(False, False)

    def open_final_save_dialog(self):
        if not self.image_history:
            QMessageBox.warning(self, "히스토리 없음", "저장할 히스토리가 없습니다.")
            return

        dialog = FinalSaveDialog(self.image_history, self)
        if dialog.exec_() == QDialog.Accepted:
            selected_paths = dialog.get_selected_paths()
            self.process_final_save(selected_paths)

    def process_final_save(self, selected_paths):
        if not selected_paths:
            return

        final_image_paths = []
        try:
            # Determine the base name from the very first image in the history
            if self.image_history:
                first_image_path = self.image_history[0]["image_path"]
                original_dir = os.path.dirname(first_image_path)
                original_name_ext = os.path.basename(first_image_path)
                original_name, original_ext = os.path.splitext(original_name_ext)
            else: # Fallback, should not happen if button is clicked
                QMessageBox.warning(self, "오류", "원본 이미지 정보를 찾을 수 없습니다.")
                return

            # Save selected files with _final_ suffix
            for i, path_to_copy in enumerate(selected_paths):
                final_name = f"{original_name}_final_{i+1}{original_ext}"
                final_path = os.path.join(original_dir, final_name)
                
                # Find the corresponding pixmap and save it
                for item in self.image_history:
                    if item["image_path"] == path_to_copy:
                        item["pixmap"].save(final_path)
                        final_image_paths.append(final_path)
                        break
            
            # Delete all _history_ files
            for item in self.image_history:
                history_path = item["image_path"]
                if "_history_" in history_path and os.path.exists(history_path):
                    try:
                        os.remove(history_path)
                        print(f"Removed history file: {history_path}")
                    except OSError as e:
                        print(f"Error removing file {history_path}: {e}")

            QMessageBox.information(self, "저장 완료", f"{len(final_image_paths)}개의 이미지가 최종 저장되었습니다.")
            self.finalSaveCompleted.emit(final_image_paths)

        except Exception as e:
            QMessageBox.critical(self, "저장 오류", f"최종 이미지를 저장하는 중 오류가 발생했습니다: {e}")
            print(f"Error during final save: {e}")

    def update_history_buttons(self, undo_enabled, redo_enabled):
        self.undo_btn.setEnabled(undo_enabled)
        self.redo_btn.setEnabled(redo_enabled)




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
        # Gemini models
        self.gemini = Gemini()
        self.model = "gemini-2.0-flash"  # gemini-2.5-flash
        self.model_nb = "gemini-2.5-flash-image-preview"
        self.prompt = prompt

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


    def text_to_image(self, prompt: str) -> bytes:
        """
        텍스트 프롬프트로부터 이미지를 생성합니다.
        """
        generated_image_data, _ = self.gemini.call_image_generator(prompt=prompt, image_files=[])

        if generated_image_data:
            return generated_image_data[0].data
        return None



    def upscale_image(self, source_image: bytes) -> bytes:
        """
        이미지를 업스케일하여 품질을 향상시킵니다.
        """
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as f_src:
            f_src.write(source_image)
            source_image_path = f_src.name

        try:
            p = "Upscale the given image to a higher resolution, enhancing its quality, clarity, and sharpness. The target resolution should be around 8 megapixels if possible."
            image_files = [source_image_path]
            
            generated_image_data, _ = self.gemini.call_image_generator(prompt=p, image_files=image_files)

            if generated_image_data:
                return generated_image_data[0].data
            return None
        finally:
            os.unlink(source_image_path)

    def segment_image(self, source_image: bytes) -> bytes:
        """
        이미지에서 전경을 분리하여 마스크 이미지를 생성합니다.
        """
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as f_src:
            f_src.write(source_image)
            source_image_path = f_src.name

        try:
            p = "Given the input image, create a segmentation mask of the main object. The mask should be a black and white image where the main object is white and the background is black."
            image_files = [source_image_path]
            
            generated_image_data, _ = self.gemini.call_image_generator(prompt=p, image_files=image_files)

            if generated_image_data:
                return generated_image_data[0].data
            return None
        finally:
            os.unlink(source_image_path)

    def regenerate_image(self, source_image: bytes, mask_image: bytes, reference_images: list, user_prompt: str,
                          annotation: bool) -> bytes:
        """
        편집 기능을 통해 이미지 의상 재생성하는 함수
        """
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as f_src:
                f_src.write(source_image)
                source_image_path = f_src.name
            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as f_mask:
                f_mask.write(mask_image)
                mask_image_path = f_mask.name

            reference_image_paths = []
            for ref_bytes in reference_images:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as f_ref:
                    f_ref.write(ref_bytes)
                    reference_image_paths.append(f_ref.name)

            p = self.prompt.REPLACE_OBJECT_IN_REFERENCE.format(object_to_replace='the selected area')
            if user_prompt:
                p += "\n\nUser prompt: " + user_prompt
            image_files = [source_image_path, mask_image_path] + reference_image_paths
            
            generated_image_data, _ = self.gemini.call_image_generator(prompt=p, image_files=image_files)

            if generated_image_data:
                return generated_image_data[0].data
            return None

        finally:
            os.unlink(source_image_path)
            os.unlink(mask_image_path)
            for p in reference_image_paths:
                os.unlink(p)




    def regenerate_image_shot(self, source_image: bytes, regen_data: dict) -> bytes:
        """
        촬영기법 반영하여 이미지 재생성하는 함수
        """
        instructions = []
        for category, data in regen_data.items():
            if category == 'user_prompt':
                continue
            if isinstance(data, dict) and data.get('option') and data.get('option') != '유지':
                instructions.append(f"{category}: {data['option']} ({data.get('description', '')})")
        
        user_prompt = regen_data.get('user_prompt', '')
        if user_prompt:
            instructions.append(f"User prompt: {user_prompt}")

        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as f_src:
            f_src.write(source_image)
            source_image_path = f_src.name

        reference_image_paths = []
        try:
            for category, data in regen_data.items():
                if category == 'user_prompt':
                    continue
                if isinstance(data, dict):
                    reference_path = data.get("reference")
                    if reference_path and os.path.exists(reference_path):
                        reference_image_paths.append(reference_path)

            p = self.prompt.CHANGE_ATTRIBUTES.format(instructions=", ".join(instructions))
            image_files = [source_image_path] + reference_image_paths

            generated_image_data, _ = self.gemini.call_image_generator(prompt=p, image_files=image_files)

            if generated_image_data:
                return generated_image_data[0].data
            return None
        finally:
            os.unlink(source_image_path)

