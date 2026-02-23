#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Census File Type Detector
Automatically detects real file type regardless of extension.
"""

import os
import zipfile

# ======================================================
# CONFIG
# ======================================================

PROJECT_DIR = './_emis_code/census-1994-2024/'
DATA_DIR = os.path.join(PROJECT_DIR, 'data')


# ======================================================
# DETECTION LOGIC
# ======================================================

def detect_file_type(filepath):
    """
    Detect actual file type by inspecting file signature and content.
    """

    try:
        with open(filepath, 'rb') as f:
            header = f.read(4096)

        header_str = header.decode(errors='ignore').lower()

        # ZIP-based formats (xlsx is zip)
        if header.startswith(b'PK'):
            try:
                with zipfile.ZipFile(filepath, 'r') as z:
                    namelist = z.namelist()
                    if any('xl/' in name for name in namelist):
                        return "XLSX (Office Open XML - zipped)"
                    else:
                        return "ZIP archive (not Excel)"
            except:
                return "Corrupted ZIP"

        # Old binary XLS (BIFF) signature
        if header.startswith(b'\xD0\xCF\x11\xE0'):
            return "XLS (Binary BIFF format)"

        # HTML disguised as XLS
        if "<html" in header_str:
            return "HTML table (often mislabeled as .xls)"

        # XML Excel 2003 format
        if "<?xml" in header_str and "<worksheet" in header_str:
            return "Excel 2003 XML format"

        if "<?xml" in header_str:
            return "Generic XML"

        # CSV detection
        if "," in header_str[:1000]:
            return "CSV or delimited text"

        return "Plain text / Unknown format"

    except Exception as e:
        return f"Error reading file: {e}"


# ======================================================
# SCAN DIRECTORY
# ======================================================

def scan_directory(directory):
    print("=" * 70)
    print("CENSUS FILE TYPE DETECTOR")
    print("=" * 70)

    if not os.path.exists(directory):
        print(f"Directory not found: {directory}")
        return

    files = os.listdir(directory)

    if not files:
        print("No files found.")
        return

    for filename in files:
        filepath = os.path.join(directory, filename)

        if os.path.isfile(filepath):
            size_mb = os.path.getsize(filepath) / (1024 * 1024)
            file_type = detect_file_type(filepath)

            print(f"\nFile: {filename}")
            print(f"Size: {size_mb:.2f} MB")
            print(f"Detected Type: {file_type}")

            # Optional: show preview
            try:
                with open(filepath, 'rb') as f:
                    preview = f.read(300).decode(errors='ignore')
                    print("Preview:")
                    print("-" * 40)
                    print(preview[:24])
                    print("-" * 40)
            except:
                pass


# ======================================================
# MAIN
# ======================================================

if __name__ == "__main__":
    scan_directory(DATA_DIR)
