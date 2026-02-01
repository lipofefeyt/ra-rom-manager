import platform
from pathlib import Path

# Detect the OS
IS_ANDROID = "android" in platform.uname().version.lower() or hasattr(platform, "android_ver")

def get_rom_path():
    """Returns the default ROM path based on the device."""
    if IS_ANDROID:
        # Pydroid standard path
        return Path("/storage/emulated/0/RetroArch/roms")
    else:
        # Windows standard path (adjust to your PC)
        return Path("H:/Disk/Games/Roms/GBA")

def get_save_path():
    if IS_ANDROID:
        return Path("/storage/emulated/0/RetroArch/saves")
    return Path("C:/Games/RetroArch/saves")
