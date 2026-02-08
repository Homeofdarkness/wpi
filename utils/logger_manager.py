"""Logging utilities.

A common pain point in small projects is that logging configuration leaks into
unit tests (e.g. creating files, writing into the repo, asking for input).

This module provides a small logger manager with sane defaults and
**test-friendly** knobs.

Environment variables:
- WPI_LOG_LEVEL: DEBUG/INFO/WARNING/ERROR (default: DEBUG)
- WPI_LOG_TO_FILE: 1/0 (default: 1)
- WPI_LOG_DIR: custom log directory (default: <project>/logs)
"""

from __future__ import annotations

import glob
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Optional, List


class Logger:
    _instance: Optional['Logger'] = None
    _initialized = False

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(Logger, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self._setup_logging_environment()
            self._initialized = True

    def _get_project_root(self) -> Path:
        current_path = Path(__file__).resolve()

        for parent in [current_path.parent] + list(current_path.parents):
            if any((parent / marker).exists() for marker in [
                'requirements.txt', 'setup.py', 'pyproject.toml',
                '.git', 'main.py', 'app.py', 'manage.py'
            ]):
                return parent

        return current_path.parent

    def _setup_logging_environment(self) -> None:
        # Respect env overrides (especially for tests)
        level_name = os.environ.get('WPI_LOG_LEVEL', 'DEBUG').upper()
        level = getattr(logging, level_name, logging.DEBUG)

        log_to_file = os.environ.get('WPI_LOG_TO_FILE', '1').strip() not in {
            '0', 'false', 'no'}

        project_root = self._get_project_root()
        log_dir = Path(
            os.environ.get('WPI_LOG_DIR', str(project_root / 'logs')))

        handlers: List[logging.Handler] = []

        self.log_dir = None

        if log_to_file:
            try:
                log_dir.mkdir(parents=True, exist_ok=True)
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                log_file = log_dir / f"app_{timestamp}.log"
                handlers.insert(
                    0,
                    logging.FileHandler(
                        log_file,
                        mode='w',
                        encoding='utf-8'
                    )
                )
                self.log_dir = log_dir
            except Exception:
                # If file logging fails for any reason, fall back to console.
                self.log_dir = None

        logging.basicConfig(
            level=level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=handlers,
        )

    @staticmethod
    def get_logger(name: str = None) -> logging.Logger:
        return logging.getLogger(name or __name__)

    def get_log_files(self) -> List[Path]:
        if not getattr(self, 'log_dir', None):
            return []

        log_pattern = str(Path(self.log_dir) / 'app_*.log')
        return [Path(log_file) for log_file in glob.glob(log_pattern)]

    def get_log_info(self) -> dict:
        if not getattr(self, 'log_dir', None):
            return {}

        log_files = self.get_log_files()
        total_size = sum(f.stat().st_size for f in log_files if f.exists())

        return {
            'log_dir': str(self.log_dir),
            'total_files': len(log_files),
            'total_size_mb': round(total_size / (1024 * 1024), 2),
            'files': [
                {
                    'name': f.name,
                    'size_kb': round(f.stat().st_size / 1024,
                                     2) if f.exists() else 0,
                    'modified': datetime.fromtimestamp(
                        f.stat().st_mtime).strftime('%Y-%m-%d %H:%M:%S')
                    if f.exists() else 'N/A',
                }
                for f in log_files
            ],
        }


_logger_manager = Logger()


def get_logger(name: str = None) -> logging.Logger:
    """Получить logger с указанным именем"""
    return _logger_manager.get_logger(name)


def clean_logs_directory(
        logs_dir: str = 'logs',
        max_files: int = 10,
        keep_latest: int = 3,
        file_pattern: str = '*',
        dry_run: bool = False,
        assume_yes: bool = False,
):
    """Clean up logs directory.

    This is a convenience utility, not used by the engine.
    `assume_yes` exists to make it script-friendly.
    """

    logs_path = Path(logs_dir)

    if not logs_path.exists():
        print(f"Директория {logs_dir} не существует")
        return

    if not logs_path.is_dir():
        print(f"{logs_dir} не является директорией")
        return

    files = list(logs_path.glob(file_pattern))
    files = [f for f in files if f.is_file()]

    print(f"Найдено {len(files)} файлов в {logs_dir}")

    if len(files) <= max_files:
        print(
            f"Количество файлов ({len(files)}) "
            f"не превышает лимит ({max_files})."
            f"Очистка не требуется.")
        return

    # Сортируем файлы по времени модификации (от новых к старым)
    files.sort(key=lambda f: f.stat().st_mtime, reverse=True)

    files_to_keep = files[:keep_latest]
    files_to_delete = files[keep_latest:]

    print(f"\nБудет сохранено {len(files_to_keep)} файлов:")
    for file in files_to_keep:
        mtime = file.stat().st_mtime
        print(f"  ✓ {file.name} (изменен: {format_time(mtime)})")

    print(f"\nБудет удалено {len(files_to_delete)} файлов:")
    for file in files_to_delete:
        mtime = file.stat().st_mtime
        print(f"  ✗ {file.name} (изменен: {format_time(mtime)})")

    if dry_run:
        print("\n[DRY RUN] Файлы не были удалены")
        return

    if files_to_delete and not assume_yes:
        confirm = input(
            f"\nУдалить {len(files_to_delete)} файлов? "
            f"(y/N, да/Нет): ").strip().lower()
        if confirm not in ['y', 'yes', 'да']:
            print("Отменено")
            return

    deleted_count = 0
    for file in files_to_delete:
        try:
            file.unlink()
            print(f"Удален: {file.name}")
            deleted_count += 1
        except Exception as e:
            print(f"Ошибка при удалении {file.name}: {e}")

    print(
        f"\nГотово! Удалено {deleted_count} файлов, "
        f"осталось {len(files_to_keep)}")


def format_time(timestamp: float) -> str:
    """Форматирует timestamp в читаемый вид"""
    import datetime

    return datetime.datetime.fromtimestamp(timestamp).strftime(
        "%Y-%m-%d %H:%M:%S")
