import glob
import logging
import shutil
from datetime import datetime, timedelta
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

    def _setup_logging_environment(self):
        project_root = self._get_project_root()
        log_dir = project_root / "logs"
        log_dir.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = log_dir / f"app_{timestamp}.log"

        logging.basicConfig(
            level=logging.DEBUG,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[
                logging.FileHandler(log_file, mode="w", encoding="utf-8"),
                logging.StreamHandler()
            ]
        )

        self.log_dir = log_dir

    @staticmethod
    def get_logger(name: str = None) -> logging.Logger:
        return logging.getLogger(name or __name__)

    @staticmethod
    def _close_all_handlers():
        root_logger = logging.getLogger()
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
            if hasattr(handler, 'close'):
                handler.close()

    def _close_current_log_file(self):
        if hasattr(self, 'file_handler'):
            self.file_handler.close()
            logging.getLogger().removeHandler(self.file_handler)

    def clean_old_logs(self, days_to_keep: int = 7) -> List[str]:

        if not hasattr(self, 'log_dir'):
            return []

        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        deleted_files = []

        log_pattern = str(self.log_dir / "app_*.log")
        for log_file in glob.glob(log_pattern):
            file_path = Path(log_file)

            if file_path.exists():
                file_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                if file_time < cutoff_date:
                    try:
                        file_path.unlink()
                        deleted_files.append(str(file_path))
                    except OSError as e:
                        logging.error(
                            f"Не удалось удалить файл {file_path}: {e}")

        return deleted_files

    def remove_logs_directory(self) -> bool:
        """Полностью удаляет папку логов"""
        if not hasattr(self, 'log_dir'):
            return False

        try:
            # Закрываем все обработчики
            self._close_all_handlers()

            # Удаляем папку целиком
            if self.log_dir.exists():
                shutil.rmtree(self.log_dir)
                print(f"Папка логов {self.log_dir} удалена")

            self._initialized = False

            return True

        except Exception as e:
            print(f"Ошибка при удалении папки логов: {e}")
            return False

    def get_log_files(self) -> List[Path]:
        if not hasattr(self, 'log_dir'):
            return []

        log_pattern = str(self.log_dir / "app_*.log")
        return [Path(log_file) for log_file in glob.glob(log_pattern)]

    def get_log_info(self) -> dict:
        if not hasattr(self, 'log_dir'):
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
                        f.stat().st_mtime).strftime(
                        '%Y-%m-%d %H:%M:%S') if f.exists() else 'N/A'
                }
                for f in log_files
            ]
        }


_logger_manager = Logger()


def get_logger(name: str = None) -> logging.Logger:
    """Получить logger с указанным именем"""
    return _logger_manager.get_logger(name)


def clean_old_logs(days_to_keep: int = 7) -> List[str]:
    """Удалить старые логи"""
    return _logger_manager.clean_old_logs(days_to_keep)


def clean_all_logs() -> bool:
    """Удалить все логи"""
    return _logger_manager.remove_logs_directory()


def get_log_info() -> dict:
    """Получить информацию о логах"""
    return _logger_manager.get_log_info()


# Пример использования
if __name__ == "__main__":
    # Создаем logger
    logger = get_logger("example")

    # Логируем сообщения
    logger.info("Приложение запущено")
    logger.debug("Отладочная информация")
    logger.warning("Предупреждение")
    logger.error("Ошибка")

    # Получаем информацию о логах
    print("Информация о логах:")
    log_info = get_log_info()
    print(f"Папка логов: {log_info['log_dir']}")
    print(f"Количество файлов: {log_info['total_files']}")
    print(f"Общий размер: {log_info['total_size_mb']} MB")

    # Удаляем старые логи (старше 7 дней)
    deleted = clean_old_logs(days_to_keep=7)
    print(f"Удалено старых логов: {len(deleted)}")

    # Для демонстрации - удаляем все логи (раскомментируйте при необходимости)
    # deleted_all = clean_all_logs()
    # print(f"Удалено всех логов: {len(deleted_all)}")
