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
        resp = requests.get(ZIP_URL, timeout=timeout)
        if resp.status_code != 200:
            print(f"Не удалось скачать архив (HTTP {resp.status_code}).")
            return None
        return BytesIO(resp.content)
    except requests.RequestException as e:
        print(f"Ошибка скачивания архива: {e}")
        return None


def extract_and_update_repo(zip_data: BytesIO) -> bool:
    current_dir = os.path.abspath(os.path.dirname(__file__))
    launcher_name = os.path.basename(__file__)

    tmp_dir = tempfile.mkdtemp(prefix="age_of_resources_update_")
    try:
        with ZipFile(zip_data) as zf:
            zf.extractall(tmp_dir)

        root_entries = [
            name
            for name in zf.namelist()
            if name.endswith("/") and name.count("/") == 1
        ]
        if root_entries:
            root_folder = root_entries[0].split("/", 1)[0]
        else:
            
            root_folder = os.path.commonprefix(zf.namelist()).split("/", 1)[0]

        src_root = os.path.join(tmp_dir, root_folder)
        if not os.path.isdir(src_root):
            print("Не удалось определить корневую папку в архиве.")
            return False

        
        expected_files: set[str] = set()
        for root, dirs, files in os.walk(src_root):
            rel_dir = os.path.relpath(root, src_root)
            if rel_dir == ".":
                rel_dir = ""
            for filename in files:
                rel_path = os.path.normpath(os.path.join(rel_dir, filename))
                expected_files.add(rel_path)

        
        print("Удаляю устаревшие файлы...")
        for root, dirs, files in os.walk(current_dir):
            rel_dir = os.path.relpath(root, current_dir)
            if rel_dir == ".":
                rel_dir = ""
            for filename in files:
                if filename == launcher_name:
                    continue
                rel_path = os.path.normpath(os.path.join(rel_dir, filename))
                
                saves_root = os.path.normpath(os.path.join("assets", "saves"))
                textures_root = os.path.normpath(os.path.join("assets", "textures"))
                assets_root = os.path.normpath("assets")

                
                saves_root = os.path.normpath(os.path.join("assets", "saves"))
                if rel_path == saves_root or rel_path.startswith(saves_root + os.sep):
                    continue

                
                if rel_path.startswith(assets_root + os.sep) and not (
                    rel_path == textures_root
                    or rel_path.startswith(textures_root + os.sep)
                    or rel_path == saves_root
                    or rel_path.startswith(saves_root + os.sep)
                ):
                    continue

                if rel_path not in expected_files:
                    full_path = os.path.join(root, filename)
                    try:
                        os.remove(full_path)
                        print(f"Удалён файл: {rel_path}")
                    except OSError as e:
                        print(f"Не удалось удалить {rel_path}: {e}")

        print("Обновляю файлы игры...")
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
        print("Версия совпадает. Синхронизирую файлы с репозиторием...")
    else:
        print("Доступна новая версия. Начинаю обновление и синхронизацию файлов...")

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
        print("✅ main_game загружен")
        main_game.run_game()
        print("⚠️ run_game завершилась")
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    finally:
        input("👆 Нажми Enter, чтобы закрыть...")
