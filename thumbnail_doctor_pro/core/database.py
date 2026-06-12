"""
Database Manager for Thumbnail Doctor Pro Ultimate
Handles SQLite database operations with thread safety
"""
import sqlite3
from datetime import datetime
from typing import Optional, List, Dict, Any
from contextlib import contextmanager
import threading
import os

class DatabaseManager:
    _instance = None
    _lock = threading.Lock()
    
    def __init__(self, db_path: str = "thumbnail_doctor.db"):
        self.db_path = db_path
        self._local = threading.local()
        self._init_database()
    
    @classmethod
    def get_instance(cls, db_path: str = "thumbnail_doctor.db") -> 'DatabaseManager':
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls(db_path)
        return cls._instance
    
    def _get_connection(self) -> sqlite3.Connection:
        if not hasattr(self._local, 'connection') or self._local.connection is None:
            self._local.connection = sqlite3.connect(self.db_path, check_same_thread=False)
            self._local.connection.row_factory = sqlite3.Row
        return self._local.connection
    
    @contextmanager
    def get_cursor(self):
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            yield cursor
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
    
    def _init_database(self):
        with self.get_cursor() as cursor:
            cursor.executescript('''
                CREATE TABLE IF NOT EXISTS settings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    key TEXT UNIQUE NOT NULL,
                    value TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE TABLE IF NOT EXISTS projects (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    path TEXT,
                    project_type TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE TABLE IF NOT EXISTS analysis_reports (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id INTEGER,
                    report_type TEXT NOT NULL,
                    overall_score REAL,
                    architecture_score REAL,
                    security_score REAL,
                    performance_score REAL,
                    maintainability_score REAL,
                    documentation_score REAL,
                    code_quality_score REAL,
                    issues_json TEXT,
                    recommendations_json TEXT,
                    fixes_json TEXT,
                    screenshot_path TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (project_id) REFERENCES projects(id)
                );
                
                CREATE TABLE IF NOT EXISTS thumbnail_analysis (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    image_path TEXT NOT NULL,
                    color_score REAL,
                    font_score REAL,
                    composition_score REAL,
                    subject_score REAL,
                    ctr_score REAL,
                    overall_score REAL,
                    colors_json TEXT,
                    recommendations_json TEXT,
                    photoshop_fixes_json TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE TABLE IF NOT EXISTS api_keys (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    service_name TEXT UNIQUE NOT NULL,
                    encrypted_key TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE TABLE IF NOT EXISTS analysis_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    analysis_type TEXT NOT NULL,
                    target_path TEXT,
                    score REAL,
                    summary TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE INDEX IF NOT EXISTS idx_projects_type ON projects(project_type);
                CREATE INDEX IF NOT EXISTS idx_reports_project ON analysis_reports(project_id);
                CREATE INDEX IF NOT EXISTS idx_reports_type ON analysis_reports(report_type);
                CREATE INDEX IF NOT EXISTS idx_history_type ON analysis_history(analysis_type);
            ''')
    
    def save_setting(self, key: str, value: str):
        with self.get_cursor() as cursor:
            cursor.execute('''
                INSERT OR REPLACE INTO settings (key, value, updated_at)
                VALUES (?, ?, ?)
            ''', (key, value, datetime.now()))
    
    def get_setting(self, key: str, default: Optional[str] = None) -> Optional[str]:
        with self.get_cursor() as cursor:
            cursor.execute('SELECT value FROM settings WHERE key = ?', (key,))
            row = cursor.fetchone()
            return row['value'] if row else default
    
    def save_project(self, name: str, path: Optional[str], project_type: str) -> int:
        with self.get_cursor() as cursor:
            cursor.execute('''
                INSERT INTO projects (name, path, project_type)
                VALUES (?, ?, ?)
            ''', (name, path, project_type))
            return cursor.lastrowid
    
    def get_project(self, project_id: int) -> Optional[Dict]:
        with self.get_cursor() as cursor:
            cursor.execute('SELECT * FROM projects WHERE id = ?', (project_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_all_projects(self) -> List[Dict]:
        with self.get_cursor() as cursor:
            cursor.execute('SELECT * FROM projects ORDER BY created_at DESC')
            return [dict(row) for row in cursor.fetchall()]
    
    def save_analysis_report(self, project_id: Optional[int], report_type: str, 
                            scores: Dict[str, float], issues: List[Dict],
                            recommendations: List[Dict], fixes: List[Dict],
                            screenshot_path: Optional[str] = None) -> int:
        import json
        with self.get_cursor() as cursor:
            cursor.execute('''
                INSERT INTO analysis_reports 
                (project_id, report_type, overall_score, architecture_score,
                 security_score, performance_score, maintainability_score,
                 documentation_score, code_quality_score,
                 issues_json, recommendations_json, fixes_json, screenshot_path)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                project_id, report_type,
                scores.get('overall', 0),
                scores.get('architecture', 0),
                scores.get('security', 0),
                scores.get('performance', 0),
                scores.get('maintainability', 0),
                scores.get('documentation', 0),
                scores.get('code_quality', 0),
                json.dumps(issues),
                json.dumps(recommendations),
                json.dumps(fixes),
                screenshot_path
            ))
            return cursor.lastrowid
    
    def save_thumbnail_analysis(self, image_path: str, scores: Dict[str, float],
                               colors: Dict, recommendations: List[Dict],
                               photoshop_fixes: List[Dict]) -> int:
        import json
        with self.get_cursor() as cursor:
            cursor.execute('''
                INSERT INTO thumbnail_analysis
                (image_path, color_score, font_score, composition_score,
                 subject_score, ctr_score, overall_score,
                 colors_json, recommendations_json, photoshop_fixes_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                image_path,
                scores.get('color', 0),
                scores.get('font', 0),
                scores.get('composition', 0),
                scores.get('subject', 0),
                scores.get('ctr', 0),
                scores.get('overall', 0),
                json.dumps(colors),
                json.dumps(recommendations),
                json.dumps(photoshop_fixes)
            ))
            return cursor.lastrowid
    
    def save_api_key(self, service_name: str, encrypted_key: str):
        with self.get_cursor() as cursor:
            cursor.execute('''
                INSERT OR REPLACE INTO api_keys (service_name, encrypted_key, updated_at)
                VALUES (?, ?, ?)
            ''', (service_name, encrypted_key, datetime.now()))
    
    def get_api_key(self, service_name: str) -> Optional[str]:
        with self.get_cursor() as cursor:
            cursor.execute('SELECT encrypted_key FROM api_keys WHERE service_name = ?', 
                          (service_name,))
            row = cursor.fetchone()
            return row['encrypted_key'] if row else None
    
    def save_history(self, analysis_type: str, target_path: Optional[str],
                    score: float, summary: str) -> int:
        with self.get_cursor() as cursor:
            cursor.execute('''
                INSERT INTO analysis_history (analysis_type, target_path, score, summary)
                VALUES (?, ?, ?, ?)
            ''', (analysis_type, target_path, score, summary))
            return cursor.lastrowid
    
    def get_history(self, limit: int = 50) -> List[Dict]:
        with self.get_cursor() as cursor:
            cursor.execute('''
                SELECT * FROM analysis_history 
                ORDER BY created_at DESC 
                LIMIT ?
            ''', (limit,))
            return [dict(row) for row in cursor.fetchall()]
    
    def close(self):
        if hasattr(self._local, 'connection') and self._local.connection:
            self._local.connection.close()
            self._local.connection = None
