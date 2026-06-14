import atexit
import copy
import json
import os
import subprocess
import sys
import webbrowser
from pathlib import Path

import psutil
import pystray
from PIL import Image, ImageDraw, ImageFont

if getattr(sys, "frozen", False):
    BASE_DIR = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming")) / "Muktadha"
else:
    BASE_DIR = Path(__file__).parent
CONFIG_PATH = BASE_DIR / "config.json"


def load_config():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_config(config):
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)


def launch_apps(apps):
    for app_path in apps:
        expanded = os.path.expandvars(app_path)
        if not os.path.isfile(expanded):
            print(f"[muktadha] App path not found, skipping: {expanded}")
            continue
        try:
            subprocess.Popen([expanded], shell=True)
        except Exception as e:
            print(f"[muktadha] Failed to launch {expanded}: {e}")


def open_urls(urls):
    for url in urls:
        try:
            webbrowser.open(url)
        except Exception as e:
            print(f"[muktadha] Failed to open URL {url}: {e}")


def close_processes(names):
    for proc in psutil.process_iter(["pid", "name"]):
        try:
            name = proc.info["name"]
            if name and any(n.lower() == name.lower() for n in names):
                proc.terminate()
                proc.wait(timeout=5)
        except (psutil.NoSuchProcess, psutil.TimeoutExpired):
            try:
                proc.kill()
            except Exception:
                pass
        except Exception:
            pass


def switch_mode(mode_key):
    config = load_config()
    mode = config["modes"].get(mode_key)
    if not mode:
        print(f"[muktadha] Unknown mode: {mode_key}")
        return

    print(f"[muktadha] Switching to {mode['displayName']}...")

    close_list = mode.get("closeOnSwitch", [])
    if close_list:
        print(f"[muktadha] Closing: {', '.join(close_list)}")
        close_processes(close_list)

    apps = mode.get("apps", [])
    if apps:
        print(f"[muktadha] Launching apps: {', '.join(os.path.basename(a) for a in apps)}")
        launch_apps(apps)

    urls = mode.get("urls", [])
    if urls:
        print(f"[muktadha] Opening URLs: {', '.join(urls)}")
        open_urls(urls)

    config["activeContext"] = mode_key
    save_config(config)
    print(f"[muktadha] Now active: {mode['displayName']}")


def build_icon():
    size = 64
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    draw.rounded_rectangle((2, 2, size - 2, size - 2), radius=12, fill=(99, 102, 241, 255))
    draw.rounded_rectangle((8, 8, size - 8, size - 8), radius=8, fill=(255, 255, 255, 30))

    try:
        font = ImageFont.truetype("segoeui.ttf", 36)
    except Exception:
        font = ImageFont.load_default()

    bbox = draw.textbbox((0, 0), "M", font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    x = (size - tw) / 2 - bbox[0]
    y = (size - th) / 2 - bbox[1]
    draw.text((x, y), "M", fill="white", font=font)

    return img


def build_menu(config):
    items = []
    active = config.get("activeContext")
    for key, mode in config["modes"].items():
        label = mode["displayName"]
        is_active = key == active
        display = f"> {label}" if is_active else f"   {label}"

        def make_callback(k):
            def cb(icon):
                switch_mode(k)
                icon.title = f"Muktadha - {config['modes'][k]['displayName']}"
                update_menu(icon)

            return cb

        items.append(pystray.MenuItem(display, make_callback(key)))

    items.append(pystray.Menu.SEPARATOR)
    items.append(pystray.MenuItem("Settings", open_settings))
    items.append(pystray.MenuItem("Open Config File", open_config_file))
    startup_label = "\u2713 Run at startup" if is_startup_enabled() else "   Run at startup"
    items.append(pystray.MenuItem(startup_label, toggle_startup))
    items.append(pystray.Menu.SEPARATOR)
    items.append(pystray.MenuItem("Exit Muktadha", exit_app))
    return pystray.Menu(*items)


def update_menu(icon):
    try:
        config = load_config()
        icon.menu = build_menu(config)
    except Exception:
        pass


def open_config_file(icon):
    try:
        os.startfile(CONFIG_PATH)
    except AttributeError:
        subprocess.Popen(["xdg-open", str(CONFIG_PATH)])
    except Exception as e:
        print(f"[muktadha] Failed to open config: {e}")


def is_startup_enabled():
    try:
        import winreg
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                             r"Software\Microsoft\Windows\CurrentVersion\Run",
                             0, winreg.KEY_READ)
        winreg.QueryValueEx(key, "Muktadha")
        winreg.CloseKey(key)
        return True
    except (FileNotFoundError, ImportError):
        return False


def toggle_startup(icon):
    if is_startup_enabled():
        try:
            import winreg
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                                 r"Software\Microsoft\Windows\CurrentVersion\Run",
                                 0, winreg.KEY_SET_VALUE)
            winreg.DeleteValue(key, "Muktadha")
            winreg.CloseKey(key)
        except Exception:
            pass
    else:
        try:
            import winreg
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                                 r"Software\Microsoft\Windows\CurrentVersion\Run",
                                 0, winreg.KEY_SET_VALUE)
            exe = sys.executable if getattr(sys, "frozen", False) else str(Path(sys.executable).parent / "muktadha.py")
            winreg.SetValueEx(key, "Muktadha", 0, winreg.REG_SZ, exe)
            winreg.CloseKey(key)
        except Exception:
            pass
    update_menu(icon)


def open_settings(_icon=None):
    if getattr(sys, "frozen", False):
        subprocess.Popen([sys.executable, "--settings"])
    else:
        subprocess.Popen([sys.executable, str(Path(__file__).resolve()), "--settings"])


def run_settings_window():
    import tkinter as tk
    from tkinter import ttk, filedialog, simpledialog, messagebox

    if not CONFIG_PATH.exists():
        BASE_DIR.mkdir(parents=True, exist_ok=True)
        save_config({
            "activeContext": "mktWork_01",
            "modes": {
                "mktWork_01": {
                    "displayName": "Work Mode", "apps": [],
                    "urls": ["https://github.com", "https://jira.com"],
                    "closeOnSwitch": ["Steam.exe", "Spotify.exe"],
                },
                "mktChill_01": {
                    "displayName": "Chill Mode", "apps": [],
                    "urls": ["https://youtube.com"],
                    "closeOnSwitch": ["code.exe", "docker.exe"],
                },
            },
        })

    config = load_config()
    working = copy.deepcopy(config)
    modes = working["modes"]

    C = {
        "bg": "#f1f5f9",
        "surface": "#ffffff",
        "primary": "#6366f1",
        "primary_hover": "#4f46e5",
        "text": "#0f172a",
        "text_sec": "#64748b",
        "border": "#e2e8f0",
        "danger": "#ef4444",
        "danger_bg": "#fef2f2",
        "success": "#22c55e",
    }

    window = tk.Tk()
    window.title("Muktadha Settings")
    window.state("zoomed")
    window.configure(bg=C["bg"])
    window.protocol("WM_DELETE_WINDOW", window.destroy)

    # --- Header ---
    header = tk.Frame(window, bg=C["surface"])
    header.pack(fill=tk.X)
    tk.Frame(header, bg=C["primary"], height=3).pack(fill=tk.X)
    hc = tk.Frame(header, bg=C["surface"])
    hc.pack(fill=tk.X, padx=28, pady=18)
    tk.Label(hc, text="Muktadha Settings", font=("Segoe UI", 20, "bold"),
             bg=C["surface"], fg=C["text"]).pack(anchor=tk.W)
    tk.Label(hc, text="Configure your environment modes \u2014 apps, URLs, and close rules",
             font=("Segoe UI", 10), bg=C["surface"], fg=C["text_sec"]).pack(anchor=tk.W)

    # --- Notebook ---
    style = ttk.Style()
    for t in ("vista", "winnative", "clam"):
        if t in style.theme_names():
            style.theme_use(t)
            break
    style.configure("TNotebook", background=C["bg"])
    style.configure("TNotebook.Tab", padding=(16, 6), font=("Segoe UI", 10))

    notebook = ttk.Notebook(window)
    notebook.pack(fill=tk.BOTH, expand=True, padx=28, pady=(16, 0))

    # --- Helper: add item ---
    def add_item(lb, items, is_file, key):
        if is_file:
            path = filedialog.askopenfilename(
                title="Select Application",
                filetypes=[("Executables", "*.exe"), ("All Files", "*.*")],
            )
            if path:
                items.append(path)
                lb.insert(tk.END, path)
        else:
            prompt = ("Enter process name (e.g., chrome.exe)"
                      if key == "closeOnSwitch" else "Enter URL")
            result = simpledialog.askstring("Add Item", prompt)
            if result:
                result = result.strip()
                if result:
                    items.append(result)
                    lb.insert(tk.END, result)

    def remove_item(lb, items):
        sel = lb.curselection()
        if sel:
            idx = sel[0]
            items.pop(idx)
            lb.delete(idx)

    def browse_items(lb, items):
        paths = browse_apps_dialog(window)
        for p in paths:
            items.append(p)
            lb.insert(tk.END, p)

    # --- Build tabs ---
    for mode_key, mode_config in modes.items():
        tab = tk.Frame(notebook, bg=C["bg"])
        notebook.add(tab, text=mode_config["displayName"])

        canvas = tk.Canvas(tab, bg=C["bg"], highlightthickness=0)
        vsb = ttk.Scrollbar(tab, orient=tk.VERTICAL, command=canvas.yview)
        inner = tk.Frame(canvas, bg=C["bg"])

        def _on_inner_configure(e, c=canvas):
            c.configure(scrollregion=c.bbox("all"))
        inner.bind("<Configure>", _on_inner_configure)

        inner_id = canvas.create_window((0, 0), window=inner, anchor=tk.NW)

        def _on_canvas_configure(e, c=canvas, iid=inner_id):
            c.itemconfigure(iid, width=e.width)
            c.configure(scrollregion=c.bbox("all"))
        canvas.bind("<Configure>", _on_canvas_configure)

        canvas.configure(yscrollcommand=vsb.set)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)

        def on_enter(e, c=canvas):
            c.bind_all("<MouseWheel>", lambda ev, cn=c: cn.yview_scroll(
                int(-1 * (ev.delta / 120)), "units"))

        def on_leave(_):
            canvas.unbind_all("<MouseWheel>")

        canvas.bind("<Enter>", on_enter)
        canvas.bind("<Leave>", on_leave)

        sections = [
            ("Apps to Launch", "apps", True),
            ("URLs to Open", "urls", False),
            ("Close on Switch", "closeOnSwitch", False),
        ]

        for label, key, is_file in sections:
            card = tk.Frame(inner, bg=C["surface"],
                            highlightbackground=C["border"], highlightthickness=1)
            card.pack(fill=tk.BOTH, expand=True, padx=2, pady=(0, 14))

            tk.Frame(card, bg=C["primary"], height=3).pack(fill=tk.X)

            cc = tk.Frame(card, bg=C["surface"])
            cc.pack(fill=tk.BOTH, expand=True, padx=18, pady=(14, 6))

            # Title row
            tr = tk.Frame(cc, bg=C["surface"])
            tr.pack(fill=tk.X)
            tk.Label(tr, text=label, font=("Segoe UI", 12, "bold"),
                     bg=C["surface"], fg=C["text"]).pack(side=tk.LEFT)

            items = mode_config[key]

            # Listbox
            lf = tk.Frame(cc, bg=C["surface"])
            lf.pack(fill=tk.BOTH, expand=True, pady=(10, 8))

            sb = tk.Scrollbar(lf)
            lb = tk.Listbox(lf, yscrollcommand=sb.set, font=("Segoe UI", 10),
                            bg="#f8fafc", fg=C["text"],
                            relief="solid", borderwidth=1,
                            highlightcolor=C["border"], highlightbackground=C["border"],
                            activestyle="none",
                            selectbackground=C["primary"], selectforeground="white")
            sb.config(command=lb.yview)
            lb.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            sb.pack(side=tk.RIGHT, fill=tk.Y)

            for item in items:
                lb.insert(tk.END, item)

            # Add button (in title row)
            tk.Button(tr, text="+ Add", font=("Segoe UI", 9, "bold"),
                      bg=C["primary"], fg="white",
                      relief="flat", padx=14, pady=3, cursor="hand2",
                      activebackground=C["primary_hover"], activeforeground="white",
                      command=lambda lb=lb, items=items, f=is_file, k=key:
                          add_item(lb, items, f, k)).pack(side=tk.RIGHT)

            # Action row
            ar = tk.Frame(cc, bg=C["surface"])
            ar.pack(fill=tk.X)

            if key == "apps":
                tk.Button(ar, text="\u2b50 Browse Installed\u2026",
                          font=("Segoe UI", 9), bg=C["surface"], fg=C["primary"],
                          relief="flat", padx=10, pady=3, cursor="hand2",
                          activebackground="#eef2ff", activeforeground=C["primary_hover"],
                          command=lambda lb=lb, items=items: browse_items(lb, items)
                          ).pack(side=tk.LEFT)

            tk.Button(ar, text="\u2716 Remove Selected",
                      font=("Segoe UI", 9), bg=C["surface"], fg=C["danger"],
                      relief="flat", padx=10, pady=3, cursor="hand2",
                      activebackground=C["danger_bg"], activeforeground="#dc2626",
                      command=lambda lb=lb, items=items: remove_item(lb, items)
                      ).pack(side=tk.LEFT, padx=(8, 0))

    # --- Bottom bar ---
    bottom = tk.Frame(window, bg=C["surface"],
                      highlightbackground=C["border"], highlightthickness=1)
    bottom.pack(fill=tk.X, side=tk.BOTTOM)

    bc = tk.Frame(bottom, bg=C["surface"])
    bc.pack(fill=tk.X, padx=28, pady=14)

    def save():
        config.clear()
        config.update(working)
        save_config(config)
        messagebox.showinfo("Saved", "Settings saved successfully!")
        window.destroy()

    def cancel():
        if messagebox.askyesno("Discard?", "Discard all unsaved changes?"):
            window.destroy()

    tk.Button(bc, text="Cancel", font=("Segoe UI", 10),
              bg=C["surface"], fg=C["text"],
              relief="solid", borderwidth=1, padx=22, pady=7, cursor="hand2",
              activebackground="#f1f5f9", activeforeground=C["text"],
              command=cancel).pack(side=tk.RIGHT)

    tk.Button(bc, text="Save", font=("Segoe UI", 10, "bold"),
              bg=C["primary"], fg="white",
              relief="flat", padx=28, pady=7, cursor="hand2",
              activebackground=C["primary_hover"], activeforeground="white",
              command=save).pack(side=tk.RIGHT, padx=(10, 0))

    window.mainloop()


def get_installed_apps():
    script = r'''
$folders = @(
    "$env:ProgramData\Microsoft\Windows\Start Menu\Programs",
    [Environment]::GetFolderPath("Programs")
)
$results = @()
$shell = New-Object -ComObject WScript.Shell
foreach ($folder in $folders) {
    if (Test-Path $folder) {
        Get-ChildItem -Path $folder -Recurse -Filter *.lnk -ErrorAction SilentlyContinue | ForEach-Object {
            try {
                $sc = $shell.CreateShortcut($_.FullName)
                $target = $sc.TargetPath
                if ($target -and (Test-Path $target)) {
                    $results += @{ Name = $_.BaseName; Path = $target }
                }
            } catch {}
        }
    }
}
$results | ConvertTo-Json
'''
    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command", script],
            capture_output=True, text=True, timeout=30,
        )
        if result.returncode == 0 and result.stdout.strip():
            import json as _json
            data = _json.loads(result.stdout.strip())
            if isinstance(data, dict):
                data = [data]
            seen = set()
            apps = []
            for item in data:
                p = item.get("Path", "")
                if p and p.lower() not in seen:
                    seen.add(p.lower())
                    apps.append(item)
            apps.sort(key=lambda x: x.get("Name", "").lower())
            return apps
    except Exception as e:
        print(f"[muktadha] App scan failed: {e}")
    return []


def browse_apps_dialog(parent):
    import tkinter as tk
    from tkinter import ttk

    apps = get_installed_apps()
    if not apps:
        from tkinter import messagebox
        messagebox.showinfo("No Apps Found", "No installed applications were detected.", parent=parent)
        return []

    dialog = tk.Toplevel(parent)
    dialog.title("Browse Installed Applications")
    dialog.geometry("640x500")
    dialog.minsize(420, 320)
    dialog.transient(parent)
    dialog.grab_set()

    search_var = tk.StringVar()
    search_entry = ttk.Entry(dialog, textvariable=search_var, font=("Segoe UI", 11))
    search_entry.pack(fill=tk.X, padx=10, pady=(10, 5))
    search_entry.focus_set()

    info_label = ttk.Label(dialog, text="Select one or more apps, then click Add Selected", foreground="#666")
    info_label.pack(fill=tk.X, padx=10)

    lf = ttk.Frame(dialog)
    lf.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

    sb = ttk.Scrollbar(lf, orient=tk.VERTICAL)
    lb = tk.Listbox(
        lf, yscrollcommand=sb.set, font=("Segoe UI", 10),
        activestyle="none", selectmode=tk.MULTIPLE,
    )
    sb.config(command=lb.yview)
    lb.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    sb.pack(side=tk.RIGHT, fill=tk.Y)

    result_paths = []

    def refresh(query=""):
        lb.delete(0, tk.END)
        q = query.lower()
        for app in apps:
            if q in app.get("Name", "").lower() or q in app.get("Path", "").lower():
                display = f"{app['Name']}  —  {app['Path']}"
                lb.insert(tk.END, display)

    def on_search(*_):
        refresh(search_var.get())

    search_var.trace_add("write", on_search)
    refresh()

    def on_select():
        sel = lb.curselection()
        if sel:
            q = search_var.get().lower()
            filtered = [a for a in apps if q in a.get("Name", "").lower() or q in a.get("Path", "").lower()]
            result_paths.clear()
            for idx in sel:
                if idx < len(filtered):
                    result_paths.append(filtered[idx]["Path"])
            dialog.destroy()

    def on_double_click(_=None):
        sel = lb.curselection()
        if sel:
            on_select()

    lb.bind("<Double-Button-1>", on_double_click)

    bf = ttk.Frame(dialog)
    bf.pack(fill=tk.X, padx=10, pady=(5, 10))

    count_label = ttk.Label(bf, text=f"{len(apps)} apps found  (Ctrl+click to select multiple)")
    count_label.pack(side=tk.LEFT)

    ttk.Button(bf, text="Add Selected", command=on_select).pack(side=tk.RIGHT, padx=(5, 0))
    ttk.Button(bf, text="Cancel", command=dialog.destroy).pack(side=tk.RIGHT)

    parent.wait_window(dialog)
    return result_paths


LOCK_PATH = os.path.join(os.environ.get("TEMP", "."), ".muktadha.lock")


def is_single_instance():
    try:
        fd = os.open(LOCK_PATH, os.O_CREAT | os.O_EXCL | os.O_RDWR)
        os.close(fd)
        return True
    except FileExistsError:
        return False
    except Exception:
        return True


def release_lock():
    try:
        os.unlink(LOCK_PATH)
    except Exception:
        pass


def exit_app(icon):
    release_lock()
    icon.stop()


def show_splash():
    import tkinter as tk
    from tkinter import ttk

    splash = tk.Tk()
    splash.title("")
    splash.overrideredirect(True)
    splash.configure(bg="#6366f1")
    splash.attributes("-topmost", True)

    w, h = 320, 180
    sw = splash.winfo_screenwidth()
    sh = splash.winfo_screenheight()
    splash.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")

    tk.Frame(splash, bg="#4f46e5", height=4).pack(fill=tk.X, side=tk.BOTTOM)

    body = tk.Frame(splash, bg="#6366f1")
    body.pack(fill=tk.BOTH, expand=True)

    tk.Label(body, text="M", font=("Segoe UI", 36, "bold"),
             bg="#6366f1", fg="white").pack(anchor=tk.CENTER, pady=(30, 0))

    tk.Label(body, text="Muktadha", font=("Segoe UI", 18, "bold"),
             bg="#6366f1", fg="white").pack(anchor=tk.CENTER)

    tk.Label(body, text="Environment Switcher", font=("Segoe UI", 9),
             bg="#6366f1", fg="#c7d2fe").pack(anchor=tk.CENTER)

    tk.Label(body, text="Starting system tray\u2026", font=("Segoe UI", 9),
             bg="#6366f1", fg="#a5b4fc").pack(anchor=tk.CENTER, pady=(12, 0))

    pb = ttk.Progressbar(body, mode="indeterminate", length=200)
    pb.pack(anchor=tk.CENTER, pady=(8, 0))
    pb.start(10)

    splash.after(3000, splash.destroy)
    splash.mainloop()


def main():
    if "--settings" in sys.argv:
        import traceback
        try:
            run_settings_window()
        except Exception:
            BASE_DIR.mkdir(parents=True, exist_ok=True)
            with open(BASE_DIR / "muktadha_debug.log", "w") as f:
                traceback.print_exc(file=f)
        return

    if not is_single_instance():
        return
    atexit.register(release_lock)

    if not CONFIG_PATH.exists():
        BASE_DIR.mkdir(parents=True, exist_ok=True)
        default = {
            "activeContext": "mktWork_01",
            "modes": {
                "mktWork_01": {
                    "displayName": "Work Mode",
                    "apps": [],
                    "urls": ["https://github.com", "https://jira.com"],
                    "closeOnSwitch": ["Steam.exe", "Spotify.exe"],
                },
                "mktChill_01": {
                    "displayName": "Chill Mode",
                    "apps": [],
                    "urls": ["https://youtube.com"],
                    "closeOnSwitch": ["code.exe", "docker.exe"],
                },
            },
        }
        save_config(default)

    if getattr(sys, "frozen", False):
        show_splash()

    config = load_config()
    current_mode = config.get("activeContext", "mktWork_01")
    mode_display = config["modes"].get(current_mode, {}).get("displayName", "Unknown")

    icon = pystray.Icon(
        "muktadha",
        build_icon(),
        title=f"Muktadha - {mode_display}",
        menu=build_menu(config),
    )

    icon.run()


if __name__ == "__main__":
    import traceback
    try:
        main()
    except Exception:
        try:
            (BASE_DIR if "BASE_DIR" in dir() else Path(os.environ.get("APPDATA", ".")) / "Muktadha").mkdir(parents=True, exist_ok=True)
            with open((BASE_DIR if "BASE_DIR" in dir() else Path(os.environ.get("APPDATA", ".")) / "Muktadha") / "muktadha_crash.log", "w") as f:
                traceback.print_exc(file=f)
        except Exception:
            pass
