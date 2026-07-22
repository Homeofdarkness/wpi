from modules.run_main import run_app
from utils.logger_manager import clean_logs_directory, configure_logging


def main() -> None:
    configure_logging()
    clean_logs_directory()
    run_app()


if __name__ == "__main__":
    main()
