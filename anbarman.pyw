# -*- coding: utf-8 -*-
"""انبارمن — دوبار کلیک برای اجرا (نسخه ماژولار)"""
import sys
import os
from pathlib import Path

# ریشه پکیج = کنار این فایل
ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from anbarman.__main__ import main
main()
