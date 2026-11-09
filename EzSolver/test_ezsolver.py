# -*- coding: utf-8 -*-
"""
تجربة الاتصال بسيرفر EzSolver المحلي
"""
import requests
import json
import time

SOLVER_URL = "http://127.0.0.1:8191/solve"

def test_connection():
    print("📡 1. جاري فحص الاتصال بالسيرفر المحلي (http://127.0.0.1:8191)...")
    try:
        # فحص هيلث تشيك سريع
        res = requests.get("http://127.0.0.1:8191", timeout=3)
        print("✅ السيرفر مستجيب وشغال!")
    except Exception as e:
        print(f"❌ مش قادر يوصل للسيرفر: {e}")
        print("💡 شغل start_solver.bat الأول عشان السيرفر يشتغل في الخلفية.")
        return

    print("\n🚀 2. جاري إرسال طلب استخراج توكن لـ PixVerse...")
    payload = {
        "siteurl": "https://app.pixverse.ai",
        "sitekey": "0x4AAAAAAATSS5Nb9KyiA05l",
        "timeout": 45
    }
    
    start_time = time.time()
    try:
        res = requests.post(SOLVER_URL, json=payload, timeout=60)
        elapsed = round(time.time() - start_time, 2)
        
        if res.status_code == 200:
            data = res.json()
            token = data.get("token", "")
            print(f"🎉 تم استلام التوكن في {elapsed} ثانية!")
            print(f"🔑 Token (أول 50 حرف): {token[:50]}...")
        else:
            print(f"⚠️ استجابة بكود {res.status_code}: {res.text}")
    except Exception as e:
        print(f"❌ خطأ أثناء طلب التوكن: {e}")

if __name__ == "__main__":
    test_connection()

