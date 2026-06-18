import os
import sys
import subprocess


def install_and_import(package):
    try:
        __import__(package)
    except ImportError:
        print(f"Installiere {package}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])


def main():
    print("==================================================")
    print("  JDS Serv - Build Executables Script (.exe)")
    print("==================================================")
    print()

    # Install pyinstaller if not already present
    install_and_import("pyinstaller")
    install_and_import("requests")
    install_and_import("schedule")
    install_and_import("psutil")

    import PyInstaller.__main__

    # Base Directories
    base_dir = os.path.dirname(os.path.abspath(__file__))
    client_dir = os.path.join(base_dir, "jds_client")
    dist_dir = os.path.join(base_dir, "build_dist")

    os.makedirs(dist_dir, exist_ok=True)

    print("1. Baue JDS-Client-Installer.exe (GUI)...")
    # Build GUI Installer
    PyInstaller.__main__.run([
        os.path.join(client_dir, 'installer_gui.py'),
        '--name=JDS-Client-Installer',
        '--onefile',
        '--noconsole',  # No black terminal window
        f'--distpath={dist_dir}',
        '--clean',
    ])

    print("\n2. Baue JDS-Backup-Agent.exe (Hintergrund-Agent)...")
    PyInstaller.__main__.run([
        os.path.join(client_dir, 'main.py'),
        '--name=JDS-Backup-Agent',
        '--onefile',
        '--noconsole',
        f'--distpath={dist_dir}',
        '--clean',
    ])

    print("\n3. Baue JDS-Admin-Portal.exe (Admin-Verwaltung)...")
    PyInstaller.__main__.run([
        os.path.join(client_dir, 'admin_portal.py'),
        '--name=JDS-Admin-Portal',
        '--onefile',
        '--noconsole',
        f'--distpath={dist_dir}',
        '--clean',
    ])

    print()
    print("==================================================")
    print("  BUILD ERFOLGREICH ABGESCHLOSSEN!")
    print("==================================================")
    print(f"Die fertigen .exe Dateien liegen im Ordner: \n -> {dist_dir}")
    print()
    print("Dateien:")
    print("  - JDS-Client-Installer.exe  <-- Für Endnutzer (Doppelklick zum Einrichten)")
    print("  - JDS-Backup-Agent.exe      <-- Wird im Hintergrund ausgeführt")
    print("  - JDS-Admin-Portal.exe      <-- Für Admins (Metadaten, Clients verwalten)")
    print("==================================================")


if __name__ == "__main__":
    main()
