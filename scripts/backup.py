#!/usr/bin/env python3
"""
Database backup and restore utilities for SOC Platform
"""

import asyncio
import os
import sys
import json
import gzip
from datetime import datetime
from pathlib import Path
import subprocess
import argparse

# Add the backend directory to Python path
backend_dir = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

from app.core.config import settings
from app.core.database import init_database
import motor.motor_asyncio


async def backup_database(backup_dir: str, compress: bool = True):
    """Create a database backup"""
    print(f"Creating database backup...")

    # Create backup directory
    backup_path = Path(backup_dir)
    backup_path.mkdir(parents=True, exist_ok=True)

    # Generate backup filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = backup_path / f"soc_platform_backup_{timestamp}"

    try:
        # Extract MongoDB connection details
        import urllib.parse
        parsed = urllib.parse.urlparse(settings.MONGODB_URL)

        host = parsed.hostname
        port = parsed.port or 27017
        username = parsed.username
        password = parsed.password
        database = settings.MONGODB_DB_NAME

        # Build mongodump command
        cmd = [
            "mongodump",
            "--host", f"{host}:{port}",
            "--db", database,
            "--out", str(backup_file)
        ]

        if username and password:
            cmd.extend(["--username", username, "--password", password])
            cmd.extend(["--authenticationDatabase", "admin"])

        # Execute mongodump
        print(f"Running: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            print(f"Error creating backup: {result.stderr}")
            return None

        # Compress backup if requested
        if compress:
            print("Compressing backup...")
            compressed_file = f"{backup_file}.tar.gz"
            subprocess.run([
                "tar", "-czf", compressed_file,
                "-C", str(backup_path),
                f"soc_platform_backup_{timestamp}"
            ])

            # Remove uncompressed directory
            subprocess.run(["rm", "-rf", str(backup_file)])
            backup_file = compressed_file

        print(f"Backup created successfully: {backup_file}")
        return backup_file

    except Exception as e:
        print(f"Error during backup: {e}")
        return None


async def restore_database(backup_file: str):
    """Restore database from backup"""
    print(f"Restoring database from: {backup_file}")

    backup_path = Path(backup_file)
    if not backup_path.exists():
        print(f"Backup file not found: {backup_file}")
        return False

    try:
        # Extract MongoDB connection details
        import urllib.parse
        parsed = urllib.parse.urlparse(settings.MONGODB_URL)

        host = parsed.hostname
        port = parsed.port or 27017
        username = parsed.username
        password = parsed.password
        database = settings.MONGODB_DB_NAME

        # Handle compressed backups
        if backup_file.endswith('.tar.gz'):
            print("Extracting compressed backup...")
            temp_dir = backup_path.parent / "temp_restore"
            temp_dir.mkdir(exist_ok=True)

            subprocess.run([
                "tar", "-xzf", backup_file,
                "-C", str(temp_dir)
            ])

            # Find the extracted directory
            extracted_dirs = [d for d in temp_dir.iterdir() if d.is_dir()]
            if not extracted_dirs:
                print("No directories found in backup archive")
                return False

            backup_dir = extracted_dirs[0] / database
        else:
            backup_dir = backup_path / database

        if not backup_dir.exists():
            print(f"Database directory not found in backup: {backup_dir}")
            return False

        # Build mongorestore command
        cmd = [
            "mongorestore",
            "--host", f"{host}:{port}",
            "--db", database,
            "--drop",  # Drop existing collections
            str(backup_dir)
        ]

        if username and password:
            cmd.extend(["--username", username, "--password", password])
            cmd.extend(["--authenticationDatabase", "admin"])

        # Execute mongorestore
        print(f"Running: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            print(f"Error restoring backup: {result.stderr}")
            return False

        # Cleanup temporary files
        if backup_file.endswith('.tar.gz'):
            subprocess.run(["rm", "-rf", str(temp_dir)])

        print("Database restored successfully")
        return True

    except Exception as e:
        print(f"Error during restore: {e}")
        return False


async def list_backups(backup_dir: str):
    """List available backups"""
    backup_path = Path(backup_dir)

    if not backup_path.exists():
        print(f"Backup directory not found: {backup_dir}")
        return

    backups = []
    for file in backup_path.iterdir():
        if file.name.startswith('soc_platform_backup_'):
            stat = file.stat()
            size = stat.st_size
            modified = datetime.fromtimestamp(stat.st_mtime)

            backups.append({
                'file': str(file),
                'size': size,
                'modified': modified
            })

    if not backups:
        print("No backups found")
        return

    backups.sort(key=lambda x: x['modified'], reverse=True)

    print("Available backups:")
    print("-" * 80)
    print(f"{'File':<40} {'Size':<15} {'Modified':<25}")
    print("-" * 80)

    for backup in backups:
        size_str = format_file_size(backup['size'])
        modified_str = backup['modified'].strftime('%Y-%m-%d %H:%M:%S')
        file_name = Path(backup['file']).name
        print(f"{file_name:<40} {size_str:<15} {modified_str:<25}")


def format_file_size(size_bytes):
    """Format file size in human readable format"""
    if size_bytes == 0:
        return "0 B"

    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0

    return f"{size_bytes:.1f} PB"


async def cleanup_old_backups(backup_dir: str, keep_count: int = 5):
    """Remove old backups, keeping only the most recent ones"""
    backup_path = Path(backup_dir)

    if not backup_path.exists():
        print(f"Backup directory not found: {backup_dir}")
        return

    backups = []
    for file in backup_path.iterdir():
        if file.name.startswith('soc_platform_backup_'):
            backups.append(file)

    if len(backups) <= keep_count:
        print(f"Only {len(backups)} backups found, no cleanup needed")
        return

    # Sort by modification time (newest first)
    backups.sort(key=lambda x: x.stat().st_mtime, reverse=True)

    # Remove old backups
    removed_count = 0
    for backup in backups[keep_count:]:
        print(f"Removing old backup: {backup.name}")
        if backup.is_file():
            backup.unlink()
        elif backup.is_dir():
            subprocess.run(["rm", "-rf", str(backup)])
        removed_count += 1

    print(f"Cleaned up {removed_count} old backups, kept {keep_count} most recent")


async def main():
    parser = argparse.ArgumentParser(description="SOC Platform Database Backup/Restore Utility")
    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Backup command
    backup_parser = subparsers.add_parser('backup', help='Create database backup')
    backup_parser.add_argument('--dir', default='./backups', help='Backup directory')
    backup_parser.add_argument('--no-compress', action='store_true', help='Do not compress backup')

    # Restore command
    restore_parser = subparsers.add_parser('restore', help='Restore database from backup')
    restore_parser.add_argument('backup_file', help='Path to backup file')

    # List command
    list_parser = subparsers.add_parser('list', help='List available backups')
    list_parser.add_argument('--dir', default='./backups', help='Backup directory')

    # Cleanup command
    cleanup_parser = subparsers.add_parser('cleanup', help='Remove old backups')
    cleanup_parser.add_argument('--dir', default='./backups', help='Backup directory')
    cleanup_parser.add_argument('--keep', type=int, default=5, help='Number of backups to keep')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    try:
        if args.command == 'backup':
            backup_file = await backup_database(args.dir, not args.no_compress)
            if backup_file:
                print(f"Backup completed: {backup_file}")
            else:
                sys.exit(1)

        elif args.command == 'restore':
            success = await restore_database(args.backup_file)
            if not success:
                sys.exit(1)

        elif args.command == 'list':
            await list_backups(args.dir)

        elif args.command == 'cleanup':
            await cleanup_old_backups(args.dir, args.keep)

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())