#!/usr/bin/env python3
"""
Script to fix mutable defaults in SQLAlchemy models
Replaces default=list and default=dict with server_default
"""
import re
from pathlib import Path

def fix_model_file(file_path: Path):
    """Fix mutable defaults in a single model file"""
    content = file_path.read_text()
    original = content

    # Fix ARRAY(String) with default=list
    content = re.sub(
        r'Column\(ARRAY\(String\), default=list, nullable=False\)',
        r"Column(ARRAY(String), server_default='{}', nullable=False)",
        content
    )

    # Fix ARRAY(String) with default=list (nullable=True)
    content = re.sub(
        r'Column\(ARRAY\(String\), default=list, nullable=True\)',
        r"Column(ARRAY(String), server_default='{}', nullable=True)",
        content
    )

    # Fix JSON with default=dict
    content = re.sub(
        r'Column\(JSON, default=dict, nullable=False\)',
        r"Column(JSON, server_default='{}', nullable=False)",
        content
    )

    # Fix JSON with default=dict (nullable=True)
    content = re.sub(
        r'Column\(JSON, default=dict, nullable=True\)',
        r"Column(JSON, server_default='{}', nullable=True)",
        content
    )

    # Fix JSON with default=list
    content = re.sub(
        r'Column\(JSON, default=list, nullable=False\)',
        r"Column(JSON, server_default='[]', nullable=False)",
        content
    )

    if content != original:
        file_path.write_text(content)
        print(f"✅ Fixed: {file_path.name}")
        return True
    else:
        print(f"⏭️  No changes needed: {file_path.name}")
        return False

def main():
    """Fix all model files"""
    models_dir = Path(__file__).parent.parent / "app" / "api" / "models"

    if not models_dir.exists():
        print(f"❌ Models directory not found: {models_dir}")
        return

    print("Fixing mutable defaults in model files...\n")

    fixed_count = 0
    for model_file in models_dir.glob("*.py"):
        if model_file.name == "__init__.py":
            continue

        if fix_model_file(model_file):
            fixed_count += 1

    print(f"\n✅ Fixed {fixed_count} file(s)")

if __name__ == "__main__":
    main()