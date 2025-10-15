#!/usr/bin/env python3
"""
OCR Verification Script
Checks if Tesseract OCR and libmagic are properly installed
"""

import sys
import subprocess


def check_command(command, name):
    """Check if a command is available"""
    try:
        result = subprocess.run(
            [command, "--version"], capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            version = result.stdout.split("\n")[0]
            print(f"✓ {name} installed: {version}")
            return True
        else:
            print(f"✗ {name} not found")
            return False
    except FileNotFoundError:
        print(f"✗ {name} not found")
        return False
    except Exception as e:
        print(f"✗ {name} check failed: {e}")
        return False


def check_python_package(package_name, import_name=None):
    """Check if a Python package is available"""
    import_name = import_name or package_name
    try:
        __import__(import_name)
        print(f"✓ Python package '{package_name}' installed")
        return True
    except ImportError:
        print(f"✗ Python package '{package_name}' not found")
        return False


def check_tesseract_data():
    """Check if Tesseract has language data"""
    try:
        result = subprocess.run(
            ["tesseract", "--list-langs"], capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            langs = result.stdout.strip().split("\n")[1:]  # Skip header
            print(f"✓ Tesseract languages available: {', '.join(langs)}")
            return len(langs) > 0
        else:
            print("✗ No Tesseract language data found")
            return False
    except Exception as e:
        print(f"✗ Failed to check Tesseract languages: {e}")
        return False


def check_libmagic():
    """Check if libmagic is available"""
    try:
        import magic

        # Try to create a Magic instance
        _ = magic.Magic(mime=True)
        print("✓ libmagic (python-magic) working")
        return True
    except Exception as e:
        print(f"✗ libmagic check failed: {e}")
        return False


def main():
    print("=" * 60)
    print("OCR & File Type Detection Verification")
    print("=" * 60)
    print()

    all_checks = []

    # Check system dependencies
    print("System Dependencies:")
    all_checks.append(check_command("tesseract", "Tesseract OCR"))
    all_checks.append(check_tesseract_data())
    print()

    # Check Python packages
    print("Python Packages:")
    all_checks.append(check_python_package("pytesseract"))
    all_checks.append(check_python_package("python-magic", "magic"))
    all_checks.append(check_python_package("PIL", "PIL"))
    all_checks.append(check_python_package("PyMuPDF", "fitz"))
    print()

    # Check libmagic functionality
    print("File Type Detection:")
    all_checks.append(check_libmagic())
    print()

    # Summary
    print("=" * 60)
    if all(all_checks):
        print("✓ All checks passed! OCR is ready to use.")
        print("=" * 60)
        return 0
    else:
        print("✗ Some checks failed. Please install missing dependencies.")
        print()
        print("Installation instructions:")
        print("  Docker: Ensure Dockerfile includes:")
        print("    - tesseract-ocr")
        print("    - tesseract-ocr-eng")
        print("    - libmagic1")
        print()
        print("  Ubuntu/Debian:")
        print("    sudo apt-get install tesseract-ocr tesseract-ocr-eng libmagic1")
        print()
        print("  macOS:")
        print("    brew install tesseract libmagic")
        print("=" * 60)
        return 1


if __name__ == "__main__":
    sys.exit(main())
