import subprocess
import sys


def install(packages):
    for package in packages:
        print(f"Installing {package}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])


if __name__ == "__main__":
    dependencies = [
        "flask",
        "sqlalchemy",
    ]
    install(dependencies)
    print("All dependencies installed.")

