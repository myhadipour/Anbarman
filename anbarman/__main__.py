# -*- coding: utf-8 -*-
"""اجرای انبارمن: python -m anbarman"""
import sys
import traceback

def main():
    try:
        if sys.platform == "win32":
            try:
                import ctypes
                k = ctypes.windll.kernel32
                k.SetPriorityClass(k.GetCurrentProcess(), 0x00008000)
            except Exception:
                pass
        from .ui import App
        App().run()
    except Exception:
        err = traceback.format_exc()
        try:
            from .database import app_dir
            open(str(app_dir() / "error.log"), "w", encoding="utf-8").write(err)
        except Exception:
            pass
        try:
            import ctypes
            ctypes.windll.user32.MessageBoxW(0, "خطای برنامه:\n\n" + err[-900:], "انبارمن", 0x10)
        except Exception:
            print(err)

if __name__ == "__main__":
    main()
