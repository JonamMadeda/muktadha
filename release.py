"""Usage: python release.py <version>  e.g. python release.py 1.1.0"""
import os
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).parent
GH = "C:\\Program Files\\GitHub CLI\\gh.exe"


def bump_version(version):
    path = HERE / "muktadha.py"
    code = path.read_text(encoding="utf-8")
    code = re.sub(r'__version__\s*=\s*"[^"]+"', f'__version__ = "{version}"', code)
    path.write_text(code, encoding="utf-8")
    print(f"[release] Bumped __version__ to {version}")


def build_exe():
    subprocess.run([sys.executable, str(HERE / "build.py")], check=True)
    print("[release] Muktadha.exe built")


def build_installer():
    candidates = [
        Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "Inno Setup 6" / "ISCC.exe",
        Path("C:\\Program Files (x86)\\Inno Setup 6\\ISCC.exe"),
        Path("C:\\Program Files\\Inno Setup 6\\ISCC.exe"),
    ]
    iscc = next((p for p in candidates if p.exists()), None)
    if not iscc:
        print("[release] ERROR: Inno Setup (ISCC.exe) not found")
        sys.exit(1)
    subprocess.run([str(iscc), str(HERE / "installer.iss")], check=True)
    print("[release] Muktadha_Installer.exe built")


def git_commit_and_tag(version):
    subprocess.run(["git", "add", "-A"], cwd=HERE, check=True)
    subprocess.run(["git", "commit", "-m", f"Release v{version}"], cwd=HERE, check=True)
    subprocess.run(["git", "tag", f"v{version}"], cwd=HERE, check=True)
    subprocess.run(["git", "push"], cwd=HERE, check=True)
    subprocess.run(["git", "push", "--tags"], cwd=HERE, check=True)
    print(f"[release] Committed and pushed tag v{version}")


def create_release(version):
    exe = HERE / "dist" / "Muktadha.exe"
    inst = HERE / "Muktadha_Installer.exe"
    args = [GH, "release", "create", f"v{version}",
            "--title", f"Muktadha v{version}",
            "--notes", f"See https://github.com/JonamMadeda/muktadha/releases/tag/v{version}",
            str(inst)]
    subprocess.run(args, check=True)
    print(f"[release] GitHub release v{version} created with Muktadha_Installer.exe")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    version = sys.argv[1].lstrip("v")
    bump_version(version)
    build_exe()
    build_installer()
    git_commit_and_tag(version)
    create_release(version)
    print(f"\n[release] Done! v{version} is live at:")
    print(f"  https://github.com/JonamMadeda/muktadha/releases/tag/v{version}")


if __name__ == "__main__":
    main()
