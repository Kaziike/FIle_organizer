#!/usr/bin/env python3
"""
File Organizer for Linux
Automatically scans ~/Downloads and moves files based on rules in config.json.
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

DEFAULT_CATEGORIES = {
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


def setup_logging(verbose: bool):
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="[%(asctime)s] %(levelname)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )


def load_config(config_path: Path) -> dict:
    """
    Load category configuration from config.json.
    Creates default config.json if not present.
    """
    if not config_path.exists():
        logging.info(f"Config file not found. Creating default config at: {config_path}")
        save_config(DEFAULT_CATEGORIES, config_path)
        return DEFAULT_CATEGORIES

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            categories = json.load(f)
            logging.info(f"Loaded config from: {config_path}")
            return categories
    except Exception as e:
        logging.error(f"Failed to read {config_path}: {e}. Using default categories.")
        return DEFAULT_CATEGORIES


def save_config(categories: dict, config_path: Path):
    """Save categories to JSON config file."""
    try:
        config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(categories, f, indent=4, ensure_ascii=False)
        logging.info(f"Configuration saved to: {config_path}")
    except Exception as e:
        logging.error(f"Failed to save config to {config_path}: {e}")


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
    """Scan source_dir and move matched files to their target directories."""
    if not source_dir.exists():
        logging.error(f"Source directory does not exist: {source_dir}")
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
            if not dry_run:
                target_dir.mkdir(parents=True, exist_ok=True)

            destination = get_unique_path(target_dir / item.name)

            if dry_run:
                logging.info(f"[DRY-RUN] Would move: '{item.name}' -> '{destination}'")
            else:
                try:
                    shutil.move(str(item), str(destination))
                    logging.info(f"Moved: '{item.name}' -> '{destination}'")
                    moved_count += 1
                except Exception as e:
                    logging.error(f"Failed to move '{item.name}': {e}")

    if not dry_run and moved_count > 0:
        logging.info(f"Finished scan. Total files moved: {moved_count}")


def print_active_rules(categories: dict, config_path: Path):
    print(f"\n================ Active File Organizer Rules ({config_path.name}) ================")
    for cat, info in categories.items():
        exts_str = ", ".join(info.get("extensions", []))
        target = info.get("target_dir")
        print(f" Category [{cat}]:")
        print(f"    Extensions: {exts_str}")
        print(f"    Target Dir: {target}")
    print("=================================================================================\n")


def main():
    parser = argparse.ArgumentParser(description="Automated File Organizer for Linux")
    parser.add_argument(
        "--source",
        type=str,
        default=str(Path.home() / "Downloads"),
        help="Source directory to organize (default: ~/Downloads)"
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
        help="Display all active file extension rules and target directories"
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
    categories = load_config(config_path)

    if args.list_rules:
        print_active_rules(categories, config_path)
        return

    source_dir = Path(args.source).expanduser().resolve()
    logging.info(f"Target directory: {source_dir}")

    if args.dry_run:
        logging.info("Running in DRY-RUN mode. No files will be moved.")

    if args.watch:
        logging.info(f"Starting watch mode (interval: {args.interval}s). Press Ctrl+C to stop.")
        try:
            while True:
                # Reload config every scan loop to pick up live edits to config.json without restarting service!
                categories = load_config(config_path)
                organize_directory(source_dir, categories, dry_run=args.dry_run)
                time.sleep(args.interval)
        except KeyboardInterrupt:
            logging.info("Watch mode stopped by user.")
    else:
        organize_directory(source_dir, categories, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
