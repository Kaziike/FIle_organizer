#!/usr/bin/env python3
"""
File Organizer for Linux
Automatically scans configured source directories (e.g. ~/Downloads, ~/data)
and moves files based on rules in config.json.
Supports CLI & Interactive Management (Add/Edit/Delete source folders & categories).
"""

import os
import sys
import json
import time
import shutil
import logging
import argparse
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent.resolve()
DEFAULT_CONFIG_PATH = SCRIPT_DIR / "config.json"

# Temporary or incomplete download extensions to ignore
IGNORE_EXTENSIONS = {".crdownload", ".part", ".tmp", ".download", ".aria2"}

DEFAULT_CONFIG = {
    "source_dirs": [
        "~/Downloads",
        "~/data"
    ],
    "categories": {
        "Pictures": {
            "extensions": [".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg", ".bmp", ".ico", ".tiff", ".heic"],
            "target_dir": "~/Pictures"
        },
        "Documents": {
            "extensions": [".pdf", ".docx", ".doc", ".xlsx", ".xls", ".pptx", ".ppt", ".txt", ".csv", ".odt", ".rtf"],
            "target_dir": "~/Documents"
        },
        "Videos": {
            "extensions": [".mp4", ".mov", ".mkv", ".avi", ".flv", ".webm", ".wmv", ".m4v"],
            "target_dir": "~/Videos"
        },
        "AppApp": {
            "extensions": [".apk", ".deb", ".rpm", ".appimage", ".exe", ".msi"],
            "target_dir": "~/AppApp"
        },
        "Music": {
            "extensions": [".mp3", ".wav", ".flac", ".aac", ".ogg", ".m4a"],
            "target_dir": "~/Music"
        },
        "Archives": {
            "extensions": [".zip", ".tar.gz", ".tar", ".gz", ".rar", ".7z", ".bz2", ".xz"],
            "target_dir": "~/Documents/Archives"
        }
    }
}


def setup_logging(verbose: bool):
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="[%(asctime)s] %(levelname)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )


def load_config(config_path: Path) -> dict:
    """Load configuration from config.json. Normalizes schema if needed."""
    if not config_path.exists():
        logging.info(f"Config file not found. Creating default config at: {config_path}")
        save_config(DEFAULT_CONFIG, config_path)
        return DEFAULT_CONFIG

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Normalize schema if older format without source_dirs
        if "categories" not in data and isinstance(data, dict):
            data = {
                "source_dirs": ["~/Downloads"],
                "categories": data
            }

        if "source_dirs" not in data:
            data["source_dirs"] = ["~/Downloads"]

        logging.info(f"Loaded config from: {config_path}")
        return data
    except Exception as e:
        logging.error(f"Failed to read {config_path}: {e}. Using default config.")
        return DEFAULT_CONFIG


def save_config(config_data: dict, config_path: Path):
    """Save configuration to JSON file."""
    try:
        config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config_data, f, indent=4, ensure_ascii=False)
        logging.info(f"Configuration saved to: {config_path}")
    except Exception as e:
        logging.error(f"Failed to save config to {config_path}: {e}")


def clean_ext(ext: str) -> str:
    """Format extension to lowercase starting with dot."""
    ext = ext.strip().lower()
    return ext if ext.startswith(".") else f".{ext}"


def add_source_dir(config_data: dict, dir_path: str) -> bool:
    """Add a new source directory to monitor."""
    sources = config_data.setdefault("source_dirs", [])
    if dir_path not in sources:
        sources.append(dir_path)
        logging.info(f"Added source directory: '{dir_path}'")
        return True
    else:
        logging.warning(f"Source directory '{dir_path}' is already in the list.")
        return False


def delete_source_dir(config_data: dict, dir_path: str) -> bool:
    """Delete a source directory from monitoring list."""
    sources = config_data.get("source_dirs", [])
    if dir_path in sources:
        sources.remove(dir_path)
        logging.info(f"Deleted source directory: '{dir_path}'")
        return True
    else:
        logging.error(f"Source directory '{dir_path}' not found!")
        return False


def add_category(categories: dict, name: str, target_dir: str, extensions: list):
    """Add or update a category."""
    formatted_exts = [clean_ext(e) for e in extensions]
    categories[name] = {
        "extensions": list(dict.fromkeys(formatted_exts)),
        "target_dir": target_dir
    }
    logging.info(f"Added/Updated category [{name}] -> Dir: '{target_dir}', Exts: {formatted_exts}")


def edit_category(categories: dict, name: str, new_target_dir: str = None, add_exts: list = None, remove_exts: list = None):
    """Edit category target directory or extensions."""
    if name not in categories:
        logging.error(f"Category [{name}] does not exist!")
        return False

    if new_target_dir:
        categories[name]["target_dir"] = new_target_dir
        logging.info(f"Updated target directory for [{name}] to '{new_target_dir}'")

    current_exts = categories[name].get("extensions", [])

    if add_exts:
        for e in add_exts:
            cleaned = clean_ext(e)
            if cleaned not in current_exts:
                current_exts.append(cleaned)
                logging.info(f"Added extension '{cleaned}' to category [{name}]")

    if remove_exts:
        for e in remove_exts:
            cleaned = clean_ext(e)
            if cleaned in current_exts:
                current_exts.remove(cleaned)
                logging.info(f"Removed extension '{cleaned}' from category [{name}]")

    categories[name]["extensions"] = current_exts
    return True


def delete_category(categories: dict, name: str) -> bool:
    """Delete a category."""
    if name in categories:
        del categories[name]
        logging.info(f"Deleted category [{name}]")
        return True
    else:
        logging.error(f"Category [{name}] not found!")
        return False


def get_unique_path(target_path: Path) -> Path:
    """Generate a unique path if file already exists."""
    if not target_path.exists():
        return target_path

    parent = target_path.parent
    stem = target_path.stem
    suffix = target_path.suffix

    counter = 1
    while True:
        new_path = parent / f"{stem}_{counter}{suffix}"
        if not new_path.exists():
            return new_path
        counter += 1


def organize_directory(source_dir: Path, categories: dict, dry_run: bool = False):
    """Scan source_dir and move matched files to target directories."""
    if not source_dir.exists():
        logging.warning(f"Source directory does not exist (skipping): {source_dir}")
        return

    moved_count = 0

    for item in source_dir.iterdir():
        if item.is_dir() or item.name.startswith("."):
            continue

        ext = item.suffix.lower()

        if ext in IGNORE_EXTENSIONS:
            logging.debug(f"Skipping temporary download file: {item.name}")
            continue

        target_dir = None

        for cat_name, info in categories.items():
            exts = [e.lower() for e in info.get("extensions", [])]
            if ext in exts:
                raw_target = info.get("target_dir")
                if raw_target:
                    target_dir = Path(raw_target).expanduser().resolve()
                break

        if target_dir:
            # Prevent moving file into its own source folder
            if target_dir == source_dir:
                continue

            if not dry_run:
                target_dir.mkdir(parents=True, exist_ok=True)

            destination = get_unique_path(target_dir / item.name)

            if dry_run:
                logging.info(f"[DRY-RUN] [{source_dir.name}] Would move: '{item.name}' -> '{destination}'")
            else:
                try:
                    shutil.move(str(item), str(destination))
                    logging.info(f"[{source_dir.name}] Moved: '{item.name}' -> '{destination}'")
                    moved_count += 1
                except Exception as e:
                    logging.error(f"Failed to move '{item.name}': {e}")

    if not dry_run and moved_count > 0:
        logging.info(f"Finished scan for '{source_dir}'. Total files moved: {moved_count}")


def organize_all(config_data: dict, override_source: str = None, dry_run: bool = False):
    """Organize all configured source directories."""
    categories = config_data.get("categories", {})

    if override_source:
        sources = [override_source]
    else:
        sources = config_data.get("source_dirs", ["~/Downloads"])

    for raw_src in sources:
        src_path = Path(raw_src).expanduser().resolve()
        organize_directory(src_path, categories, dry_run=dry_run)


def print_active_rules(config_data: dict, config_path: Path):
    sources = config_data.get("source_dirs", [])
    categories = config_data.get("categories", {})

    print(f"\n================ File Organizer Configuration ({config_path.name}) ================")
    print("📂 THƯ MỤC NGUỒN CẦN QUÉT (Source Directories):")
    for src in sources:
        full_p = Path(src).expanduser().resolve()
        exists_mark = " (Tồn tại)" if full_p.exists() else " (Chưa tạo)"
        print(f"   - {src}{exists_mark}")

    print("\n📁 DANH MỤC PHÂN LOẠI FILE (Categories):")
    for cat, info in categories.items():
        exts_str = ", ".join(info.get("extensions", []))
        target = info.get("target_dir")
        print(f"   [{cat}]:")
        print(f"      Target Dir: {target}")
        print(f"      Extensions: {exts_str}")
    print("=================================================================================\n")


def interactive_menu(config_data: dict, config_path: Path):
    """Interactive CLI menu for managing source directories and categories."""
    categories = config_data.setdefault("categories", {})
    sources = config_data.setdefault("source_dirs", [])

    while True:
        print("\n==================================================")
        print("    🛠️ CẤU HÌNH HỆ THỐNG FILE ORGANIZER          ")
        print("==================================================")
        print(" [1] Quản lý Thư mục nguồn (Source Directories)")
        print(" [2] Quản lý Danh mục phân loại (File Categories)")
        print(" [3] Xem tổng quan toàn bộ cấu hình")
        print(" [4] Lưu & Thoát")
        print("==================================================")

        choice = input("Nhập lựa chọn của bạn (1-4): ").strip()

        if choice == "1":
            while True:
                print("\n--- 📂 QUẢN LÝ THƯ MỤC NGUỒN CẦN QUÉT ---")
                print(" Hiện tại đang quét các thư mục:")
                for idx, s in enumerate(sources, 1):
                    print(f"   {idx}. {s}")
                print(" 1. Thêm thư mục nguồn mới (ví dụ: ~/data, ~/Desktop)")
                print(" 2. Xóa thư mục nguồn")
                print(" 3. Quay lại menu chính")

                sub_choice = input("Lựa chọn (1-3): ").strip()
                if sub_choice == "1":
                    new_src = input("Nhập đường dẫn thư mục nguồn cần thêm: ").strip()
                    if new_src:
                        if add_source_dir(config_data, new_src):
                            save_config(config_data, config_path)
                            print(f"✅ Đã thêm thư mục nguồn: '{new_src}'")
                elif sub_choice == "2":
                    del_src = input("Nhập đường dẫn thư mục nguồn cần xóa (ví dụ: ~/data): ").strip()
                    if delete_source_dir(config_data, del_src):
                        save_config(config_data, config_path)
                        print(f"✅ Đã xóa thư mục nguồn: '{del_src}'")
                elif sub_choice == "3":
                    break

        elif choice == "2":
            while True:
                print("\n--- 📁 QUẢN LÝ DANH MỤC PHÂN LOẠI ---")
                print(" 1. Xem danh sách danh mục hiện tại")
                print(" 2. Thêm danh mục mới (Add)")
                print(" 3. Sửa danh mục (Edit)")
                print(" 4. Xóa danh mục (Delete)")
                print(" 5. Quay lại menu chính")

                sub_choice = input("Lựa chọn (1-5): ").strip()
                if sub_choice == "1":
                    print_active_rules(config_data, config_path)
                elif sub_choice == "2":
                    name = input("Tên danh mục mới (ví dụ: Ebooks, ISO): ").strip()
                    if not name:
                        continue
                    target_dir = input("Đường dẫn thư mục đích (ví dụ: ~/Books): ").strip()
                    exts_input = input("Các đuôi file (ví dụ: .epub, .mobi): ").strip()
                    exts = [e.strip() for e in exts_input.split(",") if e.strip()]
                    add_category(categories, name, target_dir, exts)
                    save_config(config_data, config_path)
                    print(f"✅ Đã thêm danh mục [{name}]!")
                elif sub_choice == "3":
                    name = input("Tên danh mục cần sửa: ").strip()
                    if name not in categories:
                        print(f"❌ Danh mục [{name}] không tồn tại!")
                        continue
                    new_dir = input("Thực mục đích mới (bỏ trống để giữ nguyên): ").strip()
                    add_exts_input = input("Thêm đuôi file (phân cách bằng dấu phẩy): ").strip()
                    rem_exts_input = input("Xóa đuôi file (phân cách bằng dấu phẩy): ").strip()

                    add_exts = [e.strip() for e in add_exts_input.split(",") if e.strip()] if add_exts_input else None
                    rem_exts = [e.strip() for e in rem_exts_input.split(",") if e.strip()] if rem_exts_input else None

                    edit_category(categories, name, new_target_dir=new_dir if new_dir else None, add_exts=add_exts, remove_exts=rem_exts)
                    save_config(config_data, config_path)
                    print(f"✅ Đã cập nhật danh mục [{name}]!")
                elif sub_choice == "4":
                    name = input("Tên danh mục cần xóa: ").strip()
                    if delete_category(categories, name):
                        save_config(config_data, config_path)
                        print(f"✅ Đã xóa danh mục [{name}]!")
                elif sub_choice == "5":
                    break

        elif choice == "3":
            print_active_rules(config_data, config_path)
        elif choice == "4":
            save_config(config_data, config_path)
            print("👋 Đã lưu cấu hình và thoát!")
            break


def main():
    parser = argparse.ArgumentParser(description="Automated File Organizer for Linux")
    parser.add_argument(
        "--source",
        type=str,
        default=None,
        help="Override source directory to organize (default: scan all source_dirs from config.json)"
    )
    parser.add_argument(
        "--config",
        type=str,
        default=str(DEFAULT_CONFIG_PATH),
        help=f"Path to JSON config file (default: {DEFAULT_CONFIG_PATH})"
    )
    parser.add_argument(
        "--list-rules",
        action="store_true",
        help="Display all configured source directories and category rules"
    )
    parser.add_argument(
        "-i", "--manage", "--interactive",
        action="store_true",
        help="Open interactive CLI menu to manage source directories & categories"
    )
    parser.add_argument(
        "--add-source",
        type=str,
        metavar="DIR",
        help="Add a source directory to scan: --add-source ~/data"
    )
    parser.add_argument(
        "--delete-source",
        type=str,
        metavar="DIR",
        help="Delete a source directory: --delete-source ~/data"
    )
    parser.add_argument(
        "--add-category",
        nargs="+",
        metavar="ARG",
        help="Add a category: --add-category Ebooks ~/Books .epub .mobi"
    )
    parser.add_argument(
        "--edit-category",
        type=str,
        metavar="NAME",
        help="Category to edit (combine with --target-dir, --add-ext, --remove-ext)"
    )
    parser.add_argument(
        "--target-dir",
        type=str,
        help="New target directory for --edit-category"
    )
    parser.add_argument(
        "--add-ext",
        nargs="+",
        help="Extensions to add when using --edit-category"
    )
    parser.add_argument(
        "--remove-ext",
        nargs="+",
        help="Extensions to remove when using --edit-category"
    )
    parser.add_argument(
        "--delete-category",
        type=str,
        metavar="NAME",
        help="Delete a category by name: --delete-category Archives"
    )
    parser.add_argument(
        "--watch",
        action="store_true",
        help="Run continuously in watch/daemon mode"
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=5,
        help="Check interval in seconds when using --watch (default: 5)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without moving files"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose debugging output"
    )

    args = parser.parse_args()
    setup_logging(args.verbose)

    config_path = Path(args.config).expanduser().resolve()
    config_data = load_config(config_path)

    # Interactive mode
    if args.manage:
        interactive_menu(config_data, config_path)
        return

    # CLI modifications
    config_modified = False

    if args.add_source:
        if add_source_dir(config_data, args.add_source):
            config_modified = True

    if args.delete_source:
        if delete_source_dir(config_data, args.delete_source):
            config_modified = True

    categories = config_data.setdefault("categories", {})

    if args.add_category:
        if len(args.add_category) < 3:
            print("Error: --add-category requires NAME TARGET_DIR EXT1 [EXT2 ...]")
            sys.exit(1)
        cat_name = args.add_category[0]
        target_dir = args.add_category[1]
        exts = args.add_category[2:]
        add_category(categories, cat_name, target_dir, exts)
        config_modified = True

    if args.edit_category:
        cat_name = args.edit_category
        if edit_category(categories, cat_name, new_target_dir=args.target_dir, add_exts=args.add_ext, remove_exts=args.remove_ext):
            config_modified = True

    if args.delete_category:
        if delete_category(categories, args.delete_category):
            config_modified = True

    if config_modified:
        save_config(config_data, config_path)
        print_active_rules(config_data, config_path)
        return

    if args.list_rules:
        print_active_rules(config_data, config_path)
        return

    if args.dry_run:
        logging.info("Running in DRY-RUN mode. No files will be moved.")

    if args.watch:
        logging.info(f"Starting watch mode (interval: {args.interval}s). Press Ctrl+C to stop.")
        try:
            while True:
                config_data = load_config(config_path)
                organize_all(config_data, override_source=args.source, dry_run=args.dry_run)
                time.sleep(args.interval)
        except KeyboardInterrupt:
            logging.info("Watch mode stopped by user.")
    else:
        organize_all(config_data, override_source=args.source, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
