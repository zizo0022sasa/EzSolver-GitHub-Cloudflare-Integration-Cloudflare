# -*- coding: utf-8 -*-
"""
منظومة الاختبارات الشاملة الموحدة لمزود PixVerse وسيرفر التحقق المحلي
Unified Test Suite for PixVerse & Local Turnstile Daemon
"""
import sys
import os
import time
import json
import requests
import subprocess
from typing import Dict, Any

DAEMON_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "EzSolver")
DAEMON_URL = "http://127.0.0.1:8191"
PIXVERSE_API = "https://app-api.pixverse.ai/creative_platform"
SITE_KEY = "0x4AAAAAAATSS5Nb9KyiA05l"
SITE_URL = "https://app.pixverse.ai"

results = []

def log_test(name: str, passed: bool, elapsed: float, details: str = ""):
    status_icon = "✅ ناجح (PASS)" if passed else "❌ فاشل (FAIL)"
    results.append({
        "name": name,
        "passed": passed,
        "elapsed": round(elapsed, 2),
        "details": details
    })
    print(f"[{status_icon}] {name} ({round(elapsed, 2)}s)")
    if details:
        print(f"   ℹ️ التفاصيل: {details}")

def test_1_dependencies():
    """1. فحص الاعتماديات والمكتبات ومسار كروم"""
    t0 = time.time()
    try:
        import nodriver
        import requests
        
        # فحص وجود كروم
        candidates = [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
        ]
        chrome_found = any(os.path.isfile(c) for c in candidates)
        if not chrome_found:
            raise FileNotFoundError("متصفح Google Chrome غير موجود في المسارات القياسية!")
            
        log_test(
            "1. فحص بيئة بايثون والاعتماديات ومسار Google Chrome",
            True,
            time.time() - t0,
            f"nodriver={nodriver.__version__}, Chrome مثبت وجاهز"
        )
        return True
    except Exception as e:
        log_test("1. فحص بيئة بايثون والاعتماديات ومسار Google Chrome", False, time.time() - t0, str(e))
        return False

def test_2_daemon_health():
    """2. فحص استجابة سيرفر التحقق المحلي (Healthcheck)"""
    t0 = time.time()
    try:
        res = requests.get(f"{DAEMON_URL}/health", timeout=3)
        if res.status_code == 200:
            data = res.json()
            if data.get("status") == "ok":
                log_test(
                    "2. فحص صحة واستجابة خادم EzSolver المحلي (/health)",
                    True,
                    time.time() - t0,
                    f"السيرفر متصل على البورت 8191 (نشط={data.get('active')}, في الانتظار={data.get('queued')})"
                )
                return True
        log_test("2. فحص صحة واستجابة خادم EzSolver المحلي (/health)", False, time.time() - t0, f"كود الاستجابة: {res.status_code}")
        return False
    except Exception as e:
        log_test(
            "2. فحص صحة واستجابة خادم EzSolver المحلي (/health)",
            False,
            time.time() - t0,
            f"السيرفر غير مستجيب على {DAEMON_URL}. تأكد من تشغيل start_solver.bat"
        )
        return False

def test_3_solve_token():
    """3. اختبار استخراج توكن حقيقي لـ PixVerse عبر الخادم المحلي"""
    t0 = time.time()
    payload = {
        "siteurl": SITE_URL,
        "sitekey": SITE_KEY,
        "timeout": 45
    }
    try:
        res = requests.post(f"{DAEMON_URL}/solve", json=payload, timeout=60)
        elapsed = time.time() - t0
        if res.status_code == 200:
            data = res.json()
            token = data.get("token", "")
            if len(token) > 30 and token.startswith("1."):
                log_test(
                    "3. استخراج توكن Turnstile أصلي لـ PixVerse عبر Daemon",
                    True,
                    elapsed,
                    f"تم استلام توكن صالح: {token[:45]}... (الطول: {len(token)} حرف)"
                )
                return token
        log_test("3. استخراج توكن Turnstile أصلي لـ PixVerse عبر Daemon", False, elapsed, f"الرد: {res.text}")
        return None
    except Exception as e:
        log_test("3. استخراج توكن Turnstile أصلي لـ PixVerse عبر Daemon", False, time.time() - t0, str(e))
        return None

def test_4_pixverse_api_reachability():
    """4. فحص اتصال خوادم PixVerse API الرسمية"""
    t0 = time.time()
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
        }
        res = requests.get(SITE_URL, headers=headers, timeout=10)
        log_test(
            "4. فحص الوصول إلى منصة PixVerse الأساسية (Network Reachability)",
            res.status_code == 200,
            time.time() - t0,
            f"استجابة المنصة HTTP {res.status_code}"
        )
        return res.status_code == 200
    except Exception as e:
        log_test("4. فحص الوصول إلى منصة PixVerse الأساسية (Network Reachability)", False, time.time() - t0, str(e))
        return False

def print_summary():
    print("\n" + "=" * 70)
    print("📊 الملخص التنفيذي لمنظومة الاختبارات الميدانية (Test Summary)")
    print("=" * 70)
    total = len(results)
    passed = sum(1 for r in results if r["passed"])
    failed = total - passed
    
    print(f"إجمالي الاختبارات: {total} | الناجحة: {passed} ✅ | الفاشلة: {failed} ❌")
    print("-" * 70)
    for i, r in enumerate(results, 1):
        mark = "✅ PASS" if r["passed"] else "❌ FAIL"
        print(f"{i}. [{mark}] {r['name']} ({r['elapsed']}s)")
    print("=" * 70)
    if failed == 0:
        print("🎉 كافة الاختبارات اجتازت بنجاح 100%! المنظومة جاهزة للإنتاج.")
    else:
        print("⚠️ يوجد اختبارات تحتاج مراجعة كما موضح أعلاه.")
    print("=" * 70 + "\n")

if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("🚀 بدء تنفيذ حزمة الاختبارات الشاملة لمزود PixVerse والخادم المحلي")
    print("=" * 70 + "\n")
    
    test_1_dependencies()
    test_4_pixverse_api_reachability()
    daemon_ok = test_2_daemon_health()
    if daemon_ok:
        test_3_solve_token()
    else:
        log_test("3. استخراج توكن Turnstile أصلي لـ PixVerse عبر Daemon", False, 0.0, "تم التخطي لعدم توفر السيرفر")
        
    print_summary()

