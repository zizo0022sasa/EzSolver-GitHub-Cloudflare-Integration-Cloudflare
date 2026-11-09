#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🤖 Apinex Models Discovery & Live Lab (Root Copy)
المعايير: جلب وتصفية موديلات Free حصراً · فحص الكوتة اليومية · الثلاثية القياسية
"""
import sys
import json
import requests
from curl_cffi import requests as cffi

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

KEY = "sk-apx437446cf04aadc92e3ea8b52c40d6edfdb34494c9b73ea8"
BASE_URL = "https://apinex.bond"

headers = {
    'Authorization': f'Bearer {KEY}',
    'Content-Type': 'application/json',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
}

# 1. جلب قائمة النماذج العامة
print("📡 [1/3] جلب قائمة النماذج العامة من Apinex...")
try:
    response = requests.get(f'{BASE_URL}/api/public/models', headers=headers, timeout=15)
    all_models_data = response.json()
except Exception as e:
    print(f"Error fetching models: {e}")
    all_models_data = {"models": []}

free_models_list = []
all_models = all_models_data.get('models', [])

print(f"📊 إجمالي النماذج المتوفرة بالمنصة: {len(all_models)}")

# 2. تصفية باقة النماذج المجانية Free فقط
for mod in all_models:
    m_id = mod.get("id", "")
    m_provider = mod.get("provider", "")
    if m_provider.lower() == "free" or m_id.startswith("free/"):
        free_models_list.append({
            "id": mod.get("id"),
            "name": mod.get("name"),
            "contextWindow": mod.get("contextWindow"),
            "health": mod.get("health"),
            "provider": mod.get("provider")
        })

print(f"\n🎁 تم العثور على {len(free_models_list)} موديل مجاني (Free):")
for idx, m in enumerate(free_models_list, 1):
    print(f"  {idx}. {m['id']:30} | {m['name']:20} | Context: {m['contextWindow']:5} | Health: {m['health']}")

# 3. دوال الثلاثية المعيارية
def register(api_key=KEY):
    """التحقق من المفتاح ورصيد التوكن"""
    r = requests.get(f"{BASE_URL}/v1/subscription", headers={'Authorization': f'Bearer {api_key}'}, timeout=15)
    if r.status_code == 200:
        sub = r.json()
        return {
            "status": "active" if sub.get("allowed") else "limited",
            "token": api_key,
            "tokens_remaining": sub.get("tokens_remaining", 0),
            "token_limit": sub.get("token_limit", 0),
            "resets_at_utc": sub.get("resets_at_utc"),
        }
    return {"status": "error", "code": r.status_code}

def refresh(account_info):
    """تجديد فحص كوتة التوكن"""
    return register(account_info.get("token", KEY))

def ask(prompt, model="free/gemini-3.8-flash", stream=False):
    """إرسال طلب استنتاج للنموذج المجاني"""
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "stream": stream
    }
    r = requests.post(f"{BASE_URL}/v1/chat/completions", headers=headers, json=payload, timeout=30)
    if r.status_code == 200:
        return r.json()["choices"][0]["message"]["content"]
    return f"Error {r.status_code}: {r.text}"

if __name__ == "__main__":
    print("\n🔍 فحص حساب المفتاح والكوتة:")
    acc = register()
    print(f"الحالة: {acc.get('status')} | التوكنات المتبقية: {acc.get('tokens_remaining'):,} / {acc.get('token_limit'):,}")
    print(f"موعد التجديد القادم: {acc.get('resets_at_utc')}")
    
    print("\n💬 تجربة سريعة لدالة ask:")
    reply = ask("1+1=?", model="free/gemini-3.8-flash")
    print(f"رد الموديل: {reply}")