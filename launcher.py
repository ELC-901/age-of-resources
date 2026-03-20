import os
import sys
import shutil
import tempfile
from io import BytesIO
from zipfile import ZipFile

import requests


REPO_OWNER = "ELC-901"
REPO_NAME = "age-of-resources"
BRANCH = "main"

RAW_VERSION_URL = (
    f"https://raw.githubusercontent.com/{REPO_OWNER}/{REPO_NAME}/{BRANCH}/version.txt"
)
ZIP_URL = (
    f"https://github.com/{REPO_OWNER}/{REPO_NAME}/archive/refs/heads/{BRANCH}.zip"
)

LOCAL_VERSION_FILE = "version.txt"


def get_local_version() -> str | None:
    if not os.path.exists(LOCAL_VERSION_FILE):
        return None
    try:
        with open(LOCAL_VERSION_FILE, "r", encoding="utf-8") as f:
            return f.read().strip()
    except OSError:
        return None


def get_remote_version(timeout: float = 10.0) -> str | None:
    try:
        resp = requests.get(RAW_VERSION_URL, timeout=timeout)
        if resp.status_code != 200:
            print(f"Не удалось получить удалённую версию (HTTP {resp.status_code}).")
            return None
        return resp.text.strip()
    except requests.RequestException as e:
        print(f"Ошибка запроса версии: {e}")
        return None


def download_latest_zip(timeout: float = 30.0) -> BytesIO | None:
    try:
        print("Скачиваю последнюю версию игры с GitHub...")
        resp = requests.get(ZIP_URL, timeout=timeout, stream=True)
        if resp.status_code != 200:
            print(f"Не удалось скачать архив (HTTP {resp.status_code}).")
            return None
        total = int(resp.headers.get("Content-Length", 0))
        downloaded = 0
        bar_width = 30
        last_percent = -1
        buf = BytesIO()
        for chunk in resp.iter_content(chunk_size=8192):
            if not chunk:
                continue
            buf.write(chunk)
            downloaded += len(chunk)
            if total > 0:
                progress = downloaded / total
                percent = int(progress * 100)
                if percent != last_percent:
                    last_percent = percent
                    filled = int(bar_width * progress)
                    bar = "█" * filled + "-" * (bar_width - filled)
                    print(f"\r[{bar}] {percent}%", end="", flush=True)
            else:
                kb = downloaded // 1024
                if kb % 128 == 0:
                    print(f"\rСкачано ~{kb} КБ", end="", flush=True)
        print()
        buf.seek(0)
        return buf
    except requests.RequestException as e:
        print(f"Ошибка скачивания архива: {e}")
        return None


def extract_and_update_repo(zip_data: BytesIO) -> bool:
    current_dir = os.path.abspath(os.path.dirname(__file__))
    launcher_name = os.path.basename(__file__)

    tmp_dir = tempfile.mkdtemp(prefix="age_of_resources_update_")
    try:
        with ZipFile(zip_data) as zf:
            members = zf.infolist()
            file_members = [m for m in members if not m.is_dir()]
            total_zip_files = len(file_members)
            extracted_files = 0
            bar_width = 30
            last_percent = -1

            print("Распаковываю архив...")
            for info in members:
                zf.extract(info, tmp_dir)
                if not info.is_dir() and total_zip_files > 0:
                    extracted_files += 1
                    progress = extracted_files / total_zip_files
                    percent = int(progress * 100)
                    if percent != last_percent:
                        last_percent = percent
                        filled = int(bar_width * progress)
                        bar = "█" * filled + "-" * (bar_width - filled)
                        print(f"\r[{bar}] {percent}%", end="", flush=True)
            if total_zip_files > 0:
                print()

            root_entries = [
                name
                for name in zf.namelist()
                if name.endswith("/") and name.count("/") == 1
            ]
            if root_entries:
                root_folder = root_entries[0].split("/", 1)[0]
            else:
                # запасной вариант — общий префикс
                root_folder = os.path.commonprefix(zf.namelist()).split("/", 1)[0]

        src_root = os.path.join(tmp_dir, root_folder)
        if not os.path.isdir(src_root):
            print("Не удалось определить корневую папку в архиве.")
            return False

        total_files = 0
        for root, dirs, files in os.walk(src_root):
            total_files += len(files)

        print("Обновляю файлы игры...")
        copied_files = 0
        bar_width = 30
        last_percent = -1

        for root, dirs, files in os.walk(src_root):
            rel_dir = os.path.relpath(root, src_root)
            if rel_dir == ".":
                rel_dir = ""

            dest_dir = os.path.join(current_dir, rel_dir)
            os.makedirs(dest_dir, exist_ok=True)

            for filename in files:
                if filename == launcher_name:
                    continue

                src_path = os.path.join(root, filename)
                dest_path = os.path.join(dest_dir, filename)

                shutil.copy2(src_path, dest_path)

                copied_files += 1
                if total_files > 0:
                    progress = copied_files / total_files
                    percent = int(progress * 100)
                    if percent != last_percent:
                        last_percent = percent
                        filled = int(bar_width * progress)
                        bar = "█" * filled + "-" * (bar_width - filled)
                        print(f"\r[{bar}] {percent}%", end="", flush=True)

        if total_files > 0:
            print()  

        print("Обновление файлов завершено.")
        return True
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


def update_if_needed() -> None:
    print("Проверяю обновления Age of Resources...")
    local_version = get_local_version()
    remote_version = get_remote_version()

    print(f"Локальная версия: {local_version or 'нет'}")
    print(f"Удалённая версия: {remote_version or 'неизвестно'}")

    if remote_version is None:
        print("Не удалось определить удалённую версию. Обновление пропущено.")
        return

    if local_version == remote_version:
        print("У тебя уже установлена последняя версия.")
        return

    print("Доступна новая версия. Начинаю обновление...")
    zip_data = download_latest_zip()
    if zip_data is None:
        print("Не удалось скачать обновление.")
        return

    if extract_and_update_repo(zip_data):
        try:
            with open(LOCAL_VERSION_FILE, "w", encoding="utf-8") as f:
                f.write(remote_version)
        except OSError as e:
            print(f"Не удалось обновить файл версии: {e}")
        print("Обновление завершено. Можно запускать игру.")
    else:
        print("Ошибка при распаковке и обновлении файлов.")


if __name__ == "__main__":
    update_if_needed()
    if getattr(sys, "frozen", False):
        os.chdir(os.path.dirname(sys.executable))
    else:
        os.chdir(os.path.dirname(os.path.abspath(__file__)))

    try:
        import main_game
        print("main_game loaded")
        main_game.run_game()
        print("run_game finished")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        input("enter to exit")