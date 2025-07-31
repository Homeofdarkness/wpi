from modules.run_main import RunMain
from utils.logger_manager import clean_logs_directory


if __name__ == "__main__":
    clean_logs_directory()
    runner = RunMain()
    runner.set_running_mode()
    runner.run()
