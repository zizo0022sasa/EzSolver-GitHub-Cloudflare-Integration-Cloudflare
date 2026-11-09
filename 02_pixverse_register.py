# -*- coding: utf-8 -*-
"""
PixVerse Standalone Direct Account Creator (Single-Session Zero-Lag)
===================================================================
Opens a lightweight Chrome window once, retrieves Token 1, sends OTP,
waits for OTP input while keeping the session alive, resets Turnstile for Token 2,
completes registration, and saves to accounts_pixverse.json.
"""

import os
import sys
import time
import json
import asyncio
import requests
from typing import Optional

BASE_API = "https://app-api.pixverse.ai/creative_platform"
SITE_KEY = "0x4AAAAAAATSS5Nb9KyiA05l"
SITE_URL = "https://app.pixverse.ai"

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Origin": "https://app.pixverse.ai",
    "Referer": "https://app.pixverse.ai/",
    "Content-Type": "application/json",
    "Accept": "application/json, text/plain, */*"
}

async def _extract_turnstile_token(page, site_key: str = SITE_KEY, timeout: int = 60) -> str:
    """استخراج أو إعادة استخراج التوكن عبر تصفير الويدجت في نفس الصفحة"""
    await page.evaluate("window._cf_extracted_token = null;", return_by_value=True)
    
    inject_script = f"""
    (() => {{
        window._cf_extracted_token = null;
        
        function renderTurnstile() {{
            let container = document.getElementById("cf-auto-container");
            if (!container) {{
                container = document.createElement("div");
                container.id = "cf-auto-container";
                container.style = "position: fixed; top: 120px; left: 50%; transform: translateX(-50%); z-index: 999999; background: #fff; padding: 15px; border-radius: 8px; box-shadow: 0 4px 15px rgba(0,0,0,0.4); text-align: center;";
                document.body.appendChild(container);
            }}
            if (window.turnstile) {{
                try {{
                    if (window._turnstile_widget_id !== undefined) {{
                        window.turnstile.reset(window._turnstile_widget_id);
                    }} else {{
                        window._turnstile_widget_id = window.turnstile.render("#cf-auto-container", {{
                            sitekey: "{site_key}",
                            callback: function(token) {{
                                window._cf_extracted_token = token;
                            }}
                        }});
                    }}
                }} catch(e) {{
                    try {{
                        window._turnstile_widget_id = window.turnstile.render("#cf-auto-container", {{
                            sitekey: "{site_key}",
                            callback: function(token) {{
                                window._cf_extracted_token = token;
                            }}
                        }});
                    }} catch(e2) {{}}
                }}
            }}
        }}
        
        if (!window.turnstile && !document.getElementById("cf-ts-tag")) {{
            const s = document.createElement("script");
            s.id = "cf-ts-tag";
            s.src = "https://challenges.cloudflare.com/turnstile/v0/api.js?onload=cfAutoLoaded";
            s.async = true;
            window.cfAutoLoaded = function() {{ renderTurnstile(); }};
            document.head.appendChild(s);
        }} else {{
            renderTurnstile();
        }}
    }})();
    """
    await page.evaluate(inject_script, return_by_value=True)
    
    start_t = time.time()
    while time.time() - start_t < timeout:
        token = await page.evaluate("window._cf_extracted_token", return_by_value=True)
        if isinstance(token, str) and len(token) > 20:
            print(f"[✓] تم استخراج التوكن بنجاح في {round(time.time() - start_t, 2)} ثانية!")
            return token
            
        dom_token = await page.evaluate("""
            (() => {
                const el = document.querySelector('[name="cf-turnstile-response"]');
                return el && el.value ? el.value : null;
            })()
        """, return_by_value=True)
        if isinstance(dom_token, str) and len(dom_token) > 20:
            print(f"[✓] تم التقاط التوكن بنجاح من النموذج في {round(time.time() - start_t, 2)} ثانية!")
            return dom_token
            
        await asyncio.sleep(0.5)
        
    raise TimeoutError(f"انتهت مهلة استخراج التوكن ({timeout} ثانية).")

def get_fast_turnstile_token(site_url: str = SITE_URL, site_key: str = SITE_KEY, timeout: int = 45) -> Optional[str]:
    """محاولة استخراج التوكن عبر خادم EzSolver المحلي في الخلفية فوراً"""
    try:
        r = requests.get("http://127.0.0.1:8191/health", timeout=1.5)
        if r.status_code == 200:
            print("[⚡] جاري استخراج التوكن عبر خادم EzSolver المحلي في الخلفية...")
            solve_res = requests.post(
                "http://127.0.0.1:8191/solve",
                json={"siteurl": site_url, "sitekey": site_key, "timeout": timeout},
                timeout=timeout + 15
            )
            if solve_res.status_code == 200:
                t = solve_res.json().get("token")
                if t:
                    print(f"[✓] تم استلام توكن صالح بنجاح من الخادم المحلي: {t[:35]}...")
                    return t
    except Exception:
        pass
    return None

import uuid

def get_browser_headers() -> dict:
    """توليد هيدرز متصفح حقيقي متطابقة تماماً مع طلبات المنصة لمنع كشف الأتمتة (500223)"""
    device_id = str(uuid.uuid4())
    trace_id = str(uuid.uuid4())
    anon_id = f"1a1bc{uuid.uuid4().hex[:10]}-{uuid.uuid4().hex[:14]}-26071f51-1638720"
    return {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "Origin": "https://app.pixverse.ai",
        "Referer": "https://app.pixverse.ai/",
        "Content-Type": "application/json",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.9",
        "x-device-id": device_id,
        "x-platform": "Web",
        "ai-trace-id": trace_id,
        "ai-anonymous-id": anon_id,
        "workspace-id": "0",
        "sec-ch-ua": '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-site"
    }

def request_verification_code(email: str, username: str, password: str, token: str) -> bool:
    """إرسال طلب كود التفعيل إلى بريد المستخدم"""
    url = f"{BASE_API}/account/getVerificationCode"
    payload = {
        "Username": username,
        "Mail": email,
        "Password": password,
        "Validate": token
    }
    r = requests.post(url, json=payload, headers=get_browser_headers(), timeout=20)
    data = r.json()
    err_code = data.get("ErrCode", 0)
    if err_code != 0:
        err_msg = data.get("ErrMsg", r.text)
        if err_code == 500214:
            raise RuntimeError(
                f"\n⚠️ منصة PixVerse رفضت دومين الإيميل ({email})!\n"
                f"السبب: المنصة تكتشف الإيميلات المؤقتة (Disposable Email Detection).\n"
                f"نص الرد من المنصة: {err_msg}\n"
                f"💡 الحل: استخدم إيميل دائم، أو إيميل dotGmail (@gmail.com)، أو دومينات مقبولة مثل (@rc.mailings.live)."
            )
        raise RuntimeError(f"فشل إرسال كود التفعيل (كود {err_code}): {err_msg}")
    print(f"[✓] تم إرسال كود التفعيل (OTP) بنجاح إلى البريد: {email}")
    return True

def complete_registration(email: str, username: str, password: str, code: str, token: str) -> dict:
    """إتمام تسجيل الحساب عبر كود الـ OTP والتوكن الثاني"""
    url = f"{BASE_API}/account/register"
    payload = {
        "Username": username,
        "Mail": email,
        "Password": password,
        "Code": code.strip(),
        "Validate": token
    }
    r = requests.post(url, json=payload, headers=get_browser_headers(), timeout=20)
    data = r.json()
    if data.get("ErrCode") != 0:
        raise RuntimeError(f"فشل إتمام التسجيل: {data.get('ErrMsg', r.text)}")
    result = data.get("Resp", {}).get("Result", {})
    print(f"[✓] تم التسجيل بنجاح في المنصة! معرف الحساب: {result.get('AccountId')}")
    return result

def save_account_entry(email: str, username: str, password: str, account_info: dict):
    """حفظ الحساب في ملفات الحسابات المعتمدة"""
    target_files = [
        os.path.join(os.path.dirname(__file__), "accounts_pixverse.json"),
        os.path.join(os.path.dirname(__file__), ".AAA_GGG_iii_VIBE_CODING_مجلد_المزودين", "pixverse.ai", "accounts_pixverse.json")
    ]
    
    new_entry = {
        "username": username,
        "email": email,
        "password": password,
        "account_id": account_info.get("AccountId"),
        "jwt_token": account_info.get("Token"),
        "active": True,
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S")
    }

    for fpath in target_files:
        if not os.path.exists(os.path.dirname(fpath)):
            continue
        accs = []
        if os.path.exists(fpath):
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    accs = json.load(f)
            except Exception:
                pass
        existing = False
        for a in accs:
            if a.get("email") == email:
                a.update(new_entry)
                existing = True
                break
        if not existing:
            accs.append(new_entry)
        with open(fpath, "w", encoding="utf-8") as f:
            json.dump(accs, f, indent=2, ensure_ascii=False)

    print("=" * 60)
    print("🎉 مبروك يا باشا! تم تفعيل الحساب وحفظه بنجاح، وجاهز للاستخدام الفوري.")
    print("=" * 60)

def register_flow_fast(email: str, password: str, username: str) -> bool:
    """مسار التسجيل فائق السرعة عبر خادم EzSolver المحلي المباشر"""
    print("=" * 60)
    print(f"🚀 بدء عملية إنشاء حساب PixVerse جديد للإيميل: {email}")
    print("=" * 60)

    # 1. استخراج التوكن الأول
    token_1 = get_fast_turnstile_token()
    if not token_1:
        return False

    # 2. إرسال كود التحقق
    request_verification_code(email, username, password, token_1)

    # 3. إدخال كود التحقق
    print("-" * 60)
    otp_code = input(">> ادخل كود التفعيل (OTP) المستلم على الإيميل: ").strip()
    print("-" * 60)

    # 4. استخراج التوكن الثاني فورياً
    token_2 = get_fast_turnstile_token()
    if not token_2:
        token_2 = token_1  # بديل لو التوكن الأول ما زال صالحاً

    # 5. إتمام التسجيل
    account_info = complete_registration(email, username, password, otp_code, token_2)
    save_account_entry(email, username, password, account_info)
    return True

async def register_flow_async(email: str, password: str = "Password2026!", username: Optional[str] = None):
    """جلسة تسجيل احتياطية تفتح متصفح تفاعلي لو الخادم المحلي غير متاح"""
    if not username:
        username = email.split("@")[0]

    # جرب أولاً المسار الفوري عبر الخادم المحلي
    try:
        if register_flow_fast(email, password, username):
            return
    except Exception as e:
        # لو الخطأ من رفض المنصة للإيميل (مثل دومين مؤقت)، أظهره فوراً دون فتح متصفح عبثاً
        if "500214" in str(e) or "disposable" in str(e).lower() or "permanent" in str(e).lower():
            raise e
        print(f"[*] تعذر إتمام المسار المباشر ({e})، جاري التبديل للمتصفح التفاعلي...")

    try:
        import nodriver as uc
    except ImportError:
        raise RuntimeError("مكتبة nodriver غير مثبتة! قم بتشغيل: pip install nodriver")

    print("\n[*] جاري فتح متصفح تفاعلي سريع (جلسة واحدة سلسة)...")
    browser = await uc.start(
        headless=False,
        browser_args=[
            "--window-size=550,650",
            "--no-first-run",
            "--no-default-browser-check"
        ]
    )

    try:
        page = await browser.get(SITE_URL)
        await asyncio.sleep(2)

        # 1. استخراج التوكن الأول
        print("[*] جاري استخراج توكن طلب كود التحقق (لو ظهر مربع تحقق اضغط عليه)...")
        token_1 = await _extract_turnstile_token(page)

        # 2. إرسال طلب OTP
        request_verification_code(email, username, password, token_1)

        # 3. إدخال الـ OTP من المستخدم دون إغلاق المتصفح
        print("-" * 60)
        otp_code = await asyncio.to_thread(input, ">> ادخل كود التفعيل (OTP) المستلم على الإيميل: ")
        otp_code = otp_code.strip()
        print("-" * 60)

        # 4. استخراج التوكن الثاني فورياً من نفس الصفحة المفتوحة
        print("[*] جاري استخراج توكن التفعيل النهائي من نفس الجلسة...")
        token_2 = await _extract_turnstile_token(page)

        # 5. إتمام التسجيل
        account_info = complete_registration(email, username, password, otp_code, token_2)
        save_account_entry(email, username, password, account_info)

    finally:
        try:
            browser.stop()
        except Exception:
            pass

def main():
    target_email = sys.argv[1] if len(sys.argv) > 1 else "hkga1official@rc.mailings.live"
    target_password = sys.argv[2] if len(sys.argv) > 2 else "Password2026!"
    try:
        asyncio.run(register_flow_async(target_email, target_password))
    except Exception as e:
        print(f"\n❌ حدث خطأ أثناء التسجيل: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
