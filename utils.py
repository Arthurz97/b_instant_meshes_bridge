import bpy
import os
import struct
import winreg

def select_only(context, obj):
    """Clears selection and makes the given object the only selected and active one."""
    for scene_obj in context.scene.objects:
        scene_obj.select_set(False)
    
    obj.select_set(True)
    context.view_layer.objects.active = obj

def get_bundled_executable_path():
    """Path of the Instant Meshes executable bundled with the add-on (bin/)."""
    return os.path.join(os.path.dirname(__file__), "bin", "Instant Meshes.exe")

def get_executable_path(prefs):
    """Resolves the executable: user preference first, bundled bin/ fallback, else None."""
    if prefs.executable_path:
        user_path = bpy.path.abspath(prefs.executable_path)
        if os.path.isfile(user_path):
            return user_path
    bundled_path = get_bundled_executable_path()
    if os.path.isfile(bundled_path):
        return bundled_path
    return None

def clear_last_visited_mru(exe_path):
    """Removes the ComDlg32 'last visited folder' registry entry for the given exe.

    The Instant Meshes save dialog (nanogui -> GetSaveFileNameW with
    lpstrInitialDir=NULL) honors this per-app history
    (HKCU\\...\\ComDlg32\\LastVisitedPidlMRU) instead of the process cwd while the
    recorded folder is usable. Without a usable entry, the documented fallback is
    the cwd itself (cwd contains files matching the dialog filter) — the temp folder.
    """
    try:
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Explorer\ComDlg32\LastVisitedPidlMRU"
        exe_name = os.path.basename(exe_path).lower()
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_READ | winreg.KEY_WRITE) as key:
            target = None
            index = 0
            while True:
                try:
                    name, val, _ = winreg.EnumValue(key, index)
                except OSError:
                    break
                index += 1
                if name == "MRUListEx":
                    continue
                # App name = UTF-16LE terminado em NUL. split(b"\x00\x00") cortaria
                # um byte cedo demais (o byte alto do último char encosta no
                # terminador), então varre char a char até o primeiro NUL.
                chars = []
                for i in range(0, len(val) - 1, 2):
                    code = val[i] | (val[i + 1] << 8)
                    if code == 0:
                        break
                    chars.append(chr(code))
                app = "".join(chars).lower()
                if app == exe_name:
                    target = name
            if target is None:
                return
            winreg.DeleteValue(key, target)
            mru, _ = winreg.QueryValueEx(key, "MRUListEx")
            entries = list(struct.unpack("<%di" % (len(mru) // 4), mru))
            entries = [e for e in entries if e != int(target)]
            winreg.SetValueEx(key, "MRUListEx", 0, winreg.REG_BINARY, struct.pack("<%di" % len(entries), *entries))
    except (OSError, struct.error):
        pass