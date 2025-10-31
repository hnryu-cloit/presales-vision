# -*- coding: utf-8 -*-
import os
import json
import sqlite3
import csv
from datetime import datetime, timedelta
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QScrollArea, QLineEdit, QComboBox,
                             QMessageBox, QFileDialog, QDialog, QTextEdit,
                             QCheckBox, QSpinBox, QDateEdit, QTabWidget)
from PyQt5.QtCore import Qt, pyqtSignal, QObject, QTimer, QThread
from PyQt5.QtGui import QFont, QIcon

# 이 클래스는 authDialog.py에 정의된 UserManager와 호환되도록 설계되었습니다.
# HistoryManager를 생성할 때 UserManager 인스턴스를 주입해야 합니다.
# 예: user_manager = UserManager()
#      history_manager = HistoryManager(user_manager)

class HistoryManager(QObject):
    """히스토리 데이터 관리 클래스"""

    history_updated = pyqtSignal()

    def __init__(self, user_manager=None, path_manager=None):
        super().__init__()
        self.user_manager = user_manager
        self.path_manager = path_manager
        self.db_path = './data/history.db'
        self.max_entries = 1000  # 최대 저장 엔트리 수
        self.init_database()

    def init_database(self):
        """히스토리 데이터베이스를 초기화하고 필요한 테이블과 인덱스를 생성합니다."""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 히스토리 테이블 생성
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                action_type TEXT NOT NULL,
                action_description TEXT NOT NULL,
                status TEXT DEFAULT 'success',
                details TEXT,
                project_id TEXT,
                session_id TEXT,
                duration_ms INTEGER DEFAULT 0
            )
        ''')

        # 검색 성능 향상을 위한 인덱스 생성
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_timestamp ON history(user_id, timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_action_type ON history(action_type)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_status ON history(status)')

        conn.commit()
        conn.close()

    def add_entry(self, action_type, description, status='success', details=None, project_id=None, duration_ms=0):
        """새로운 히스토리 엔트리를 데이터베이스에 추가합니다."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        user_id = None
        if self.user_manager and self.user_manager.get_current_user():
            user_id = self.user_manager.get_current_user().get('id')

        # 세션 ID 생성 (오늘 날짜 기반)
        session_id = datetime.now().strftime('%Y%m%d')

        cursor.execute('''
            INSERT INTO history (user_id, action_type, action_description, status, details, project_id, session_id, duration_ms)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, action_type, description, status, json.dumps(details) if details else None, project_id, session_id, duration_ms))

        conn.commit()

        # 최대 엔트리 수 초과 시 가장 오래된 항목부터 삭제
        cursor.execute('SELECT COUNT(*) FROM history WHERE user_id = ? OR (user_id IS NULL AND ? IS NULL)', (user_id, user_id))
        count = cursor.fetchone()[0]

        if count > self.max_entries:
            cursor.execute('''
                DELETE FROM history 
                WHERE id IN (
                    SELECT id FROM history 
                    WHERE user_id = ? OR (user_id IS NULL AND ? IS NULL)
                    ORDER BY timestamp ASC 
                    LIMIT ?
                )
            ''', (user_id, user_id, count - self.max_entries))
            conn.commit()

        conn.close()
        
        # JSON 파일로도 저장 (새로운 기능)
        if self.path_manager:
            self.save_history_json(action_type, description, status, details, project_id, duration_ms)
        
        self.history_updated.emit()

    def get_entries(self, limit=100, action_type=None, status=None, start_date=None, end_date=None):
        """지정된 조건에 맞는 히스토리 엔트리를 조회합니다."""
        conn = sqlite3.connect(self.db_path)
        # 딕셔너리 형태로 결과를 받기 위해 row_factory 설정
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        user_id = None
        if self.user_manager and self.user_manager.get_current_user():
            user_id = self.user_manager.get_current_user().get('id')

        query = 'SELECT * FROM history WHERE (user_id = ? OR (user_id IS NULL AND ? IS NULL))'
        params = [user_id, user_id]

        if action_type:
            query += ' AND action_type = ?'
            params.append(action_type)

        if status:
            query += ' AND status = ?'
            params.append(status)

        if start_date:
            # start_date를 datetime 객체로 가정
            query += ' AND timestamp >= ?'
            params.append(start_date)

        if end_date:
            # end_date를 datetime 객체로 가정
            query += ' AND timestamp <= ?'
            params.append(end_date)

        query += ' ORDER BY timestamp DESC LIMIT ?'
        params.append(limit)

        cursor.execute(query, params)
        # row 객체를 딕셔너리로 변환
        entries = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return entries

    def get_statistics(self):
        """현재 사용자의 히스토리 통계 정보를 반환합니다."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        user_id = None
        if self.user_manager and self.user_manager.get_current_user():
            user_id = self.user_manager.get_current_user().get('id')

        # 오늘 활동 수
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        cursor.execute('''
            SELECT COUNT(*) FROM history 
            WHERE (user_id = ? OR (user_id IS NULL AND ? IS NULL)) AND timestamp >= ?
        ''', (user_id, user_id, today_start))
        today_count = cursor.fetchone()[0]

        # 총 활동 수
        cursor.execute('SELECT COUNT(*) FROM history WHERE user_id = ? OR (user_id IS NULL AND ? IS NULL)', (user_id, user_id))
        total_count = cursor.fetchone()[0]

        # 상태별 통계
        cursor.execute('''
            SELECT status, COUNT(*) FROM history 
            WHERE user_id = ? OR (user_id IS NULL AND ? IS NULL)
            GROUP BY status
        ''', (user_id, user_id))
        status_stats = dict(cursor.fetchall())

        # 액션 타입별 통계
        cursor.execute('''
            SELECT action_type, COUNT(*) FROM history 
            WHERE user_id = ? OR (user_id IS NULL AND ? IS NULL)
            GROUP BY action_type 
            ORDER BY COUNT(*) DESC 
            LIMIT 10
        ''', (user_id, user_id))
        action_stats = dict(cursor.fetchall())

        conn.close()

        return {
            'today_count': today_count,
            'total_count': total_count,
            'status_stats': status_stats,
            'action_stats': action_stats
        }

    def export_history(self, file_path, format='json'):
        """히스토리를 JSON 또는 CSV 파일로 내보냅니다."""
        try:
            entries = self.get_entries(limit=10000)  # 내보내기 시에는 더 많은 데이터를 가져옴

            if format.lower() == 'json':
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(entries, f, ensure_ascii=False, indent=2)

            elif format.lower() == 'csv':
                if not entries:
                    return True, "내보낼 히스토리가 없습니다."
                
                with open(file_path, 'w', newline='', encoding='utf-8-sig') as f:
                    writer = csv.DictWriter(f, fieldnames=entries[0].keys())
                    writer.writeheader()
                    writer.writerows(entries)

            return True, f"히스토리가 {file_path} (으)로 내보내졌습니다."

        except Exception as e:
            return False, f"내보내기 중 오류가 발생했습니다: {str(e)}"

    def clear_history(self, older_than_days=None):
        """지정된 기간보다 오래된 히스토리를 삭제하거나 전체 히스토리를 삭제합니다."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        user_id = None
        if self.user_manager and self.user_manager.get_current_user():
            user_id = self.user_manager.get_current_user().get('id')

        if older_than_days:
            cutoff_date = datetime.now() - timedelta(days=older_than_days)
            cursor.execute('''
                DELETE FROM history 
                WHERE (user_id = ? OR (user_id IS NULL AND ? IS NULL)) AND timestamp < ?
            ''', (user_id, user_id, cutoff_date))
        else:
            cursor.execute('DELETE FROM history WHERE user_id = ? OR (user_id IS NULL AND ? IS NULL)', (user_id, user_id))

        conn.commit()
        conn.close()
        self.history_updated.emit()

    def save_history_json(self, action_type, description, status='success', details=None, project_id=None, duration_ms=0):
        """히스토리를 JSON 파일로 저장"""
        if not self.path_manager or not self.path_manager.get_current_project_root():
            return None
            
        timestamp = datetime.now()
        step_id = int(timestamp.timestamp() * 1000)  # 밀리초 기반 step ID
        
        # JSON 데이터 구성
        history_data = {
            "step": step_id,
            "timestamp": timestamp.isoformat(),
            "function": action_type,
            "action": description,
            "status": status,
            "params": details or {},
            "inputs": details.get('inputs', []) if details else [],
            "output": details.get('output', '') if details else '',
            "project_id": project_id,
            "duration_ms": duration_ms,
            "user_id": self.path_manager.get_user_id() if hasattr(self.path_manager, 'get_user_id') else None
        }
        
        # 기능별 history 디렉토리에 저장
        history_dir = self.path_manager.get_project_history_dir(action_type)
        if not history_dir:
            return None
            
        # 파일명: {step}_{timestamp}.json
        filename = f"{step_id}_{timestamp.strftime('%Y%m%d_%H%M%S')}.json"
        file_path = os.path.join(history_dir, filename)
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(history_data, f, ensure_ascii=False, indent=2)
                
            # 최신 상태를 latest.json으로도 저장
            latest_path = os.path.join(history_dir, 'latest.json')
            with open(latest_path, 'w', encoding='utf-8') as f:
                json.dump(history_data, f, ensure_ascii=False, indent=2)
                
            return file_path
        except Exception as e:
            print(f"JSON 히스토리 저장 실패: {e}")
            return None
    
    def load_latest_history_json(self, function_name):
        """특정 기능의 최신 히스토리 JSON 로드"""
        if not self.path_manager:
            return None
            
        history_dir = self.path_manager.get_project_history_dir(function_name)
        if not history_dir:
            return None
            
        latest_path = os.path.join(history_dir, 'latest.json')
        
        try:
            if os.path.exists(latest_path):
                with open(latest_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"JSON 히스토리 로드 실패: {e}")
            
        return None
    
    def get_history_stack(self, function_name, limit=10):
        """특정 기능의 히스토리 스택 반환 (undo/redo용)"""
        if not self.path_manager:
            return []
            
        history_dir = self.path_manager.get_project_history_dir(function_name)
        if not history_dir or not os.path.exists(history_dir):
            return []
            
        try:
            # JSON 파일들을 시간순으로 정렬
            json_files = []
            for filename in os.listdir(history_dir):
                if filename.endswith('.json') and filename != 'latest.json':
                    file_path = os.path.join(history_dir, filename)
                    mtime = os.path.getmtime(file_path)
                    json_files.append((mtime, file_path))
                    
            # 최신순으로 정렬하고 limit 적용
            json_files.sort(reverse=True)
            json_files = json_files[:limit]
            
            # 파일 내용 로드
            history_stack = []
            for mtime, file_path in json_files:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        history_stack.append(data)
                except:
                    continue
                    
            return history_stack
        except Exception as e:
            print(f"히스토리 스택 로드 실패: {e}")
            return []
    
    def add_metadata_history(self, metadata_type, metadata_id, action, changes=None, status='success'):
        """메타데이터 변경 이력을 저장합니다."""
        if not self.path_manager:
            return None
            
        timestamp = datetime.now()
        step_id = int(timestamp.timestamp() * 1000)
        
        # 메타데이터 히스토리 데이터 구성
        metadata_history = {
            "step": step_id,
            "timestamp": timestamp.isoformat(),
            "metadata_type": metadata_type,
            "metadata_id": metadata_id,
            "action": action,
            "changes": changes or {},
            "status": status,
            "user_id": self.path_manager.get_user_id() if hasattr(self.path_manager, 'get_user_id') else None,
            "project_id": self.path_manager.get_current_project_root()
        }
        
        # 메타데이터 히스토리 디렉토리에 저장
        history_dir = self.path_manager.get_metadata_history_dir()
        if not history_dir:
            return None
            
        # 파일명: {step}_{metadata_type}_{metadata_id}.json
        filename = f"{step_id}_{metadata_type}_{metadata_id}.json"
        file_path = os.path.join(history_dir, filename)
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(metadata_history, f, ensure_ascii=False, indent=2)
                
            # 일반 히스토리에도 기록
            description = f"메타데이터 {action}: {metadata_type} [{metadata_id}]"
            self.add_entry('metadata', description, status, metadata_history)
                
            return file_path
        except Exception as e:
            print(f"메타데이터 히스토리 저장 실패: {e}")
            return None
    
    def get_metadata_history(self, metadata_type=None, metadata_id=None, limit=50):
        """메타데이터 히스토리를 조회합니다."""
        if not self.path_manager:
            return []
            
        history_dir = self.path_manager.get_metadata_history_dir()
        if not history_dir or not os.path.exists(history_dir):
            return []
            
        try:
            # JSON 파일들을 필터링하고 시간순으로 정렬
            json_files = []
            for filename in os.listdir(history_dir):
                if not filename.endswith('.json'):
                    continue
                    
                # 파일명 필터링 (metadata_type, metadata_id 기준)
                if metadata_type and metadata_type not in filename:
                    continue
                if metadata_id and metadata_id not in filename:
                    continue
                    
                file_path = os.path.join(history_dir, filename)
                mtime = os.path.getmtime(file_path)
                json_files.append((mtime, file_path))
                
            # 최신순으로 정렬하고 limit 적용
            json_files.sort(reverse=True)
            json_files = json_files[:limit]
            
            # 파일 내용 로드
            history_list = []
            for mtime, file_path in json_files:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        history_list.append(data)
                except:
                    continue
                    
            return history_list
        except Exception as e:
            print(f"메타데이터 히스토리 조회 실패: {e}")
            return []


class HistoryPanel(QWidget):
    """히스토리 데이터를 표시하고 필터링하는 UI 패널"""

    def __init__(self, history_manager):
        super().__init__()
        self.history_manager = history_manager
        self.init_ui()
        self.setup_connections()
        self.load_history()

    def init_ui(self):
        """UI 초기화"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)

        # 헤더
        header_widget = self.create_header_widget()
        layout.addWidget(header_widget)

        # 필터 영역
        filter_widget = self.create_filter_widget()
        layout.addWidget(filter_widget)

        # 히스토리 목록
        scroll = QScrollArea()
        self.history_widget = QWidget()
        self.history_layout = QVBoxLayout(self.history_widget)
        self.history_layout.setContentsMargins(5, 5, 5, 5)
        self.history_layout.addStretch() # 아이템이 위로 쌓이도록

        scroll.setWidget(self.history_widget)
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: 1px solid #ddd; border-radius: 4px; background-color: white; }")
        layout.addWidget(scroll)

        # 하단 버튼
        bottom_widget = self.create_bottom_buttons()
        layout.addWidget(bottom_widget)

    def create_header_widget(self):
        """패널의 헤더 위젯을 생성합니다."""
        header_widget = QWidget()
        header_layout = QHBoxLayout(header_widget)
        title = QLabel('📜 작업 히스토리')
        title.setFont(QFont("Noto Sans KR", 14, QFont.Bold))

        close_btn = QPushButton('✕')
        close_btn.setFixedSize(25, 25)
        close_btn.clicked.connect(self.hide)
        close_btn.setStyleSheet("QPushButton { background-color: #f44336; color: white; border: none; border-radius: 12px; font-weight: bold; } QPushButton:hover { background-color: #d32f2f; }")

        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(close_btn)
        header_widget.setStyleSheet("QWidget { background-color: #f8f9fa; border-radius: 4px; padding: 5px; }")
        return header_widget

    def create_filter_widget(self):
        """검색 및 필터링을 위한 위젯을 생성합니다."""
        filter_widget = QWidget()
        filter_layout = QVBoxLayout(filter_widget)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText('🔍 검색어 입력...')
        self.search_input.textChanged.connect(self.apply_filters)
        filter_layout.addWidget(self.search_input)

        combo_layout = QHBoxLayout()
        self.action_filter = QComboBox()
        self.action_filter.addItems(['전체 액션', '로그인', '프로젝트', '공간 분석', '가구 배치', '가구 추천', '저장', '오류'])
        self.action_filter.currentTextChanged.connect(self.apply_filters)
        combo_layout.addWidget(self.action_filter)

        self.status_filter = QComboBox()
        self.status_filter.addItems(['전체 상태', 'success', 'error', 'warning', 'info'])
        self.status_filter.currentTextChanged.connect(self.apply_filters)
        combo_layout.addWidget(self.status_filter)
        
        filter_layout.addLayout(combo_layout)
        filter_widget.setStyleSheet("QWidget { background-color: #f0f0f0; border-radius: 4px; padding: 8px; margin: 2px; } QLineEdit, QComboBox { padding: 5px; border: 1px solid #ccc; border-radius: 3px; background-color: white; }")
        return filter_widget

    def create_bottom_buttons(self):
        """패널 하단의 버튼들을 생성합니다."""
        bottom_widget = QWidget()
        bottom_layout = QHBoxLayout(bottom_widget)

        export_btn = QPushButton('내보내기')
        export_btn.clicked.connect(self.export_history)
        export_btn.setStyleSheet(self.get_button_style('#FF9800'))
        bottom_layout.addWidget(export_btn)

        settings_btn = QPushButton('설정')
        settings_btn.clicked.connect(self.show_settings)
        settings_btn.setStyleSheet(self.get_button_style('#757575'))
        bottom_layout.addWidget(settings_btn)

        refresh_btn = QPushButton('새로고침')
        refresh_btn.clicked.connect(self.load_history)
        refresh_btn.setStyleSheet(self.get_button_style('#4CAF50'))
        bottom_layout.addWidget(refresh_btn)
        
        return bottom_widget

    def setup_connections(self):
        """시그널과 슬롯을 연결합니다."""
        self.history_manager.history_updated.connect(self.load_history)

    def load_history(self):
        """데이터베이스에서 히스토리를 로드하여 화면에 표시합니다."""
        self.apply_filters()

    def apply_filters(self):
        """현재 필터 조건에 따라 히스토리를 다시 로드하고 표시합니다."""
        search_text = self.search_input.text().lower()
        action_text = self.action_filter.currentText()
        status_text = self.status_filter.currentText()

        action_type = None if action_text == '전체 액션' else action_text
        status = None if status_text == '전체 상태' else status_text

        entries = self.history_manager.get_entries(
            limit=200,
            action_type=action_type,
            status=status
        )

        if search_text:
            entries = [e for e in entries if search_text in e['action_description'].lower()]

        self.display_filtered_entries(entries)

    def display_filtered_entries(self, entries):
        """필터링된 엔트리 목록을 화면에 표시합니다."""
        # 기존 위젯들 제거
        for i in reversed(range(self.history_layout.count())):
            widget = self.history_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)

        # 날짜별 그룹화
        grouped_entries = {}
        for entry in entries:
            # timestamp가 문자열일 경우 datetime 객체로 변환
            if isinstance(entry['timestamp'], str):
                dt_obj = datetime.strptime(entry['timestamp'], '%Y-%m-%d %H:%M:%S')
            else:
                dt_obj = entry['timestamp']
            date_str = dt_obj.strftime('%Y-%m-%d')
            if date_str not in grouped_entries:
                grouped_entries[date_str] = []
            grouped_entries[date_str].append(entry)

        # 날짜 그룹별로 위젯 생성
        for date_str in sorted(grouped_entries.keys(), reverse=True):
            date_group = self.create_date_group(date_str)
            self.history_layout.addWidget(date_group)

            for entry in grouped_entries[date_str]:
                entry_widget = self.create_history_entry(entry)
                self.history_layout.addWidget(entry_widget)
        
        self.history_layout.addStretch()


    def create_date_group(self, date_str):
        """날짜 그룹 헤더 라벨을 생성합니다."""
        group = QLabel(f"📅 {date_str}")
        group.setStyleSheet("QLabel { font-weight: bold; color: #333; padding: 8px; background-color: #f0f0f0; border-radius: 3px; margin-top: 5px; }")
        return group

    def create_history_entry(self, entry):
        """개별 히스토리 엔트리를 위한 위젯을 생성합니다."""
        entry_widget = QWidget()
        entry_layout = QHBoxLayout(entry_widget)
        entry_layout.setContentsMargins(15, 5, 10, 5)

        # 시간, 아이콘, 설명, 소요시간 등
        time_str = datetime.strptime(entry['timestamp'], '%Y-%m-%d %H:%M:%S').strftime('%H:%M')
        time_label = QLabel(time_str)
        time_label.setFixedWidth(45)
        time_label.setStyleSheet("color: #888; font-size: 11px; font-family: monospace;")
        entry_layout.addWidget(time_label)

        status_icon = self.get_status_icon(entry['status'])
        status_label = QLabel(status_icon)
        status_label.setFixedWidth(20)
        entry_layout.addWidget(status_label)

        action_label = QLabel(entry['action_description'])
        action_label.setStyleSheet("font-size: 12px; color: #333;")
        action_label.setWordWrap(True)
        entry_layout.addWidget(action_label)

        if entry.get('duration_ms', 0) > 0:
            duration_label = QLabel(f"{entry['duration_ms']}ms")
            duration_label.setStyleSheet("color: #666; font-size: 10px;")
            duration_label.setFixedWidth(50)
            entry_layout.addWidget(duration_label)

        entry_layout.addStretch()
        
        bg_color = {"error": "#ffebee", "warning": "#fff3e0", "success": "#e8f5e9"}.get(entry['status'], "#ffffff")
        entry_widget.setStyleSheet(f"QWidget {{ border-bottom: 1px solid #f0f0f0; background-color: {bg_color}; border-radius: 2px; }} QWidget:hover {{ background-color: #f8f9fa; }}")
        
        return entry_widget

    def get_status_icon(self, status):
        """상태 문자열에 해당하는 아이콘을 반환합니다."""
        return {'success': '✅', 'error': '❌', 'warning': '⚠️', 'info': 'ℹ️'}.get(status, '•')

    def export_history(self):
        """히스토리 내보내기 대화상자를 엽니다."""
        file_path, file_filter = QFileDialog.getSaveFileName(self, '히스토리 내보내기', f'history_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}', 'JSON Files (*.json);;CSV Files (*.csv)')
        if file_path:
            format_type = 'json' if 'json' in file_filter else 'csv'
            success, message = self.history_manager.export_history(file_path, format_type)
            QMessageBox.information(self, '내보내기 완료' if success else '내보내기 실패', message)

    def show_settings(self):
        """설정 다이얼로그를 엽니다."""
        dialog = HistorySettingsDialog(self.history_manager, self)
        dialog.exec_()

    def get_button_style(self, color):
        """버튼에 적용할 스타일시트를 생성합니다."""
        return f"QPushButton {{ background-color: {color}; color: white; padding: 5px 10px; border: none; border-radius: 3px; font-weight: bold; font-size: 11px; }} QPushButton:hover {{ background-color: {color}dd; }}"


class HistorySettingsDialog(QDialog):
    """히스토리 설정을 위한 다이얼로그"""

    def __init__(self, history_manager, parent=None):
        super().__init__(parent)
        self.history_manager = history_manager
        self.init_ui()

    def init_ui(self):
        """UI 초기화"""
        self.setWindowTitle('히스토리 설정')
        self.setFixedSize(400, 300)
        self.setModal(True)
        layout = QVBoxLayout(self)

        tab_widget = QTabWidget()
        general_tab = self.create_general_tab()
        data_tab = self.create_data_tab()
        tab_widget.addTab(general_tab, '일반')
        tab_widget.addTab(data_tab, '데이터 관리')
        layout.addWidget(tab_widget)

        button_layout = self.create_dialog_buttons()
        layout.addLayout(button_layout)

    def create_general_tab(self):
        """'일반' 설정 탭을 생성합니다."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        max_entries_layout = QHBoxLayout()
        max_entries_layout.addWidget(QLabel('최대 저장 개수:'))
        self.max_entries_spin = QSpinBox()
        self.max_entries_spin.setRange(100, 10000)
        self.max_entries_spin.setValue(self.history_manager.max_entries)
        max_entries_layout.addWidget(self.max_entries_spin)
        layout.addLayout(max_entries_layout)

        self.auto_cleanup_check = QCheckBox('오래된 히스토리 자동 정리 (미구현)')
        self.auto_cleanup_check.setEnabled(False) # 아직 구현되지 않음
        layout.addWidget(self.auto_cleanup_check)
        
        layout.addStretch()
        return tab

    def create_data_tab(self):
        """'데이터 관리' 탭을 생성합니다."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        clear_old_btn = QPushButton('30일 이전 히스토리 삭제')
        clear_old_btn.clicked.connect(lambda: self.clear_history(30))
        clear_old_btn.setStyleSheet("QPushButton { background-color: #FF9800; color: white; padding: 8px; border: none; border-radius: 4px; font-weight: bold; }")
        layout.addWidget(clear_old_btn)

        clear_all_btn = QPushButton('모든 히스토리 삭제')
        clear_all_btn.clicked.connect(lambda: self.clear_history(None))
        clear_all_btn.setStyleSheet("QPushButton { background-color: #f44336; color: white; padding: 8px; border: none; border-radius: 4px; font-weight: bold; }")
        layout.addWidget(clear_all_btn)
        
        layout.addStretch()
        return tab

    def create_dialog_buttons(self):
        """다이얼로그 하단의 버튼들을 생성합니다."""
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        cancel_btn = QPushButton('취소')
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        save_btn = QPushButton('저장')
        save_btn.clicked.connect(self.save_settings)
        save_btn.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; padding: 8px 16px; border: none; border-radius: 4px; font-weight: bold; }")
        button_layout.addWidget(save_btn)
        
        return button_layout

    def save_settings(self):
        """설정을 저장합니다."""
        self.history_manager.max_entries = self.max_entries_spin.value()
        # 자동 정리 설정은 아직 저장 로직 없음
        QMessageBox.information(self, '저장 완료', '설정이 저장되었습니다.')
        self.accept()

    def clear_history(self, days):
        """히스토리 삭제를 확인하고 실행합니다."""
        msg = f"{days}일 이전의 히스토리를" if days else "모든 히스토리를"
        reply = QMessageBox.question(self, '히스토리 삭제', f"{msg} 삭제하시겠습니까?이 작업은 되돌릴 수 없습니다.",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.history_manager.clear_history(days)
            QMessageBox.information(self, '삭제 완료', '히스토리가 삭제되었습니다.')


def add_history_entry(history_manager, action_description: str, status: str = 'info', details: dict = None, duration_ms: int = 0):
    """
    상태와 내용에 따라 적절한 액션 타입을 결정하여 히스토리 엔트리를 추가하는 편의 함수.
    
    :param history_manager: HistoryManager 인스턴스
    :param action_description: 작업 내용
    :param status: 작업 상태 ('success', 'error', 'warning', 'info')
    :param details: 추가 정보 (JSON으로 직렬화 가능한 딕셔셔너리)
    :param duration_ms: 작업 소요 시간 (밀리초)
    """
    if not history_manager:
        return

    # 액션 설명에서 키워드를 찾아 액션 타입 자동 결정
    if '로그인' in action_description:
        action_type = 'login'
    elif '프로젝트' in action_description:
        action_type = 'project'
    elif '공간' in action_description or '분석' in action_description:
        action_type = 'space_analysis'
    elif '가구' in action_description and '배치' in action_description:
        action_type = 'furniture_placement'
    elif '가구' in action_description and '추천' in action_description:
        action_type = 'furniture_recommendation'
    elif '저장' in action_description:
        action_type = 'save'
    elif '내보내기' in action_description:
        action_type = 'export'
    elif '삭제' in action_description:
        action_type = 'delete'
    else:
        action_type = 'general'
    
    # 오류 상태일 경우 action_type을 'error'로 설정할 수도 있음
    if status == 'error':
        action_type = 'error'

    history_manager.add_entry(
        action_type=action_type,
        description=action_description,
        status=status,
        details=details,
        duration_ms=duration_ms
    )
