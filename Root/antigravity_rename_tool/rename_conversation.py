#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
====================================================================
🛠️ Antigravity IDE Conversation Renamer Tool
أداة تغيير وتعديل أسماء محادثات Antigravity IDE بكل سهولة
تعمل مباشرة بزر التشغيل Run (▶️) داخل المحرر بواجهة ملونة تفاعلية
مع التوثيق التلقائي في مجلد الأرشيف history_logs وسجل CHATS_LOG.md
====================================================================
"""

import os
import sys
import glob
import re
import base64
import sqlite3
import shutil
from datetime import datetime

# تفعيل الألوان في الـ Terminal على ويندوز
if sys.platform == 'win32':
    os.system('')
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
        sys.stdin.reconfigure(encoding='utf-8')
    except Exception:
        pass

# أكواد الألوان
GREEN = "\033[1;92m"
BLUE = "\033[1;94m"
CYAN = "\033[1;96m"
RED = "\033[1;91m"
YELLOW = "\033[1;93m"
BOLD = "\033[1m"
RESET = "\033[0m"

# المسارات الافتراضية لـ Antigravity IDE
GLOBAL_VSCDB = os.path.expandvars(r"%APPDATA%\Antigravity IDE\User\globalStorage\state.vscdb")
WORKSPACE_STORAGE_DIR = os.path.expandvars(r"%APPDATA%\Antigravity IDE\User\workspaceStorage")
CONVERSATIONS_DIR = os.path.expanduser(r"~/.gemini/antigravity-ide/conversations")

# مسار مجلد السجلات الحالي والنسخة الأخرى إن وُجدت
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
HISTORY_DIRS = [
    os.path.join(CURRENT_DIR, "history_logs"),
    r"d:\SMS\.hRhRhRhRhRhR\.AAA_GGG_iii_VIBE_CODING\🟢_syntx_ai\Root\antigravity_rename_tool\history_logs",
    r"c:\Users\pc\Downloads\02.07_Genspark_claude-opus-5-code\antigravity_rename_tool\history_logs"
]

def encode_varint(n):
    """ترميز الأطوال بنظام Protobuf Varint"""
    res = bytearray()
    while True:
        b = n & 0x7F
        n >>= 7
        if n:
            res.append(b | 0x80)
        else:
            res.append(b)
            break
    return bytes(res)

def decode_varint(b, offset=0):
    """فك ترميز Protobuf Varint"""
    res = 0
    shift = 0
    idx = offset
    while idx < len(b):
        byte = b[idx]
        idx += 1
        res |= (byte & 0x7F) << shift
        if not (byte & 0x80):
            break
        shift += 7
    return res, idx - offset

def sanitize_filename(name):
    """تنظيف الاسم ليكون صالحاً كاسم ملف على ويندوز"""
    clean = re.sub(r'[\\/*?:"<>|]', '_', name)
    clean = re.sub(r'\s+', ' ', clean)
    return clean.strip()[:60]

def parse_egypt_time(t_str):
    """تحويل نص التاريخ المصري إلى كائن datetime للمقارنة والترتيب"""
    try:
        clean = t_str.replace('\\|', '|').strip()
        return datetime.strptime(clean, "%d-%m-%Y | %I:%M %p")
    except Exception:
        return datetime.min

def update_history_log_for_dir(history_dir, cid, old_title, new_title):
    """تحديث الملف التفصيلي للمحادثة وسجل CHATS_LOG.md لمجلد محدد"""
    os.makedirs(history_dir, exist_ok=True)
    short_id = cid[:8]
    egypt_time_escaped = datetime.now().strftime("%d-%m-%Y \\| %I:%M %p")
    egypt_time_clean = datetime.now().strftime("%d-%m-%Y | %I:%M %p")

    # 1. البحث عن الملف الفردي الخاص بهذه المحادثة
    existing_file = None
    for f in os.listdir(history_dir):
        if f.endswith(f"__{short_id}.md"):
            existing_file = os.path.join(history_dir, f)
            break

    new_filename = f"{sanitize_filename(new_title)}__{short_id}.md"
    new_filepath = os.path.join(history_dir, new_filename)

    history_entries = []
    if existing_file and os.path.exists(existing_file):
        try:
            with open(existing_file, "r", encoding="utf-8") as fp:
                for line in fp:
                    parts = [p.strip() for p in re.split(r'(?<!\\)\|', line) if p.strip()]
                    if len(parts) >= 4 and parts[0] != "#" and parts[0].isdigit():
                        history_entries.append({
                            "idx": int(parts[0]),
                            "time": parts[1],
                            "old": parts[2],
                            "new": parts[3]
                        })
            if existing_file != new_filepath:
                try:
                    os.remove(existing_file)
                except Exception:
                    pass
        except Exception:
            pass

    next_idx = len(history_entries) + 1
    history_entries.append({
        "idx": next_idx,
        "time": egypt_time_escaped,
        "old": old_title or "-",
        "new": new_title
    })

    # كتابة الملف الفردي
    content = f"""# 💬 تفاصيل المحادثة: {new_title}

* **🆔 المعرّف الكامل (ID):** `{cid}`
* **🏷️ الاسم الحالي:** {new_title}
* **🕒 آخر تحديث:** `{egypt_time_clean}` (توقيت مصر 🇪🇬)

---

## 📜 سجل تغيير الأسماء (تاريخ وتوقيت مصر):

| # | التاريخ والوقت (مصر 🇪🇬) | قبل (الاسم القديم) | بعد (الاسم الجديد) |
|---|---|---|---|
"""
    for entry in history_entries:
        content += f"| {entry['idx']} | {entry['time']} | {entry['old']} | {entry['new']} |\n"

    content += """
---
> 💡 **ملاحظة:** يتم تحديث هذا الملف تلقائياً بواسطة أداة `rename_conversation.py`.
"""
    with open(new_filepath, "w", encoding="utf-8") as fp:
        fp.write(content.strip() + "\n")

    # 2. إعادة بناء وتحديث فهرس CHATS_LOG.md
    rebuild_chats_log(history_dir)

def rebuild_chats_log(history_dir):
    """إعادة بناء فهرس المحادثات الشامل CHATS_LOG.md وترتيبه من الأحدث للأقدم"""
    chats_log_path = os.path.join(history_dir, "CHATS_LOG.md")
    egypt_time = datetime.now().strftime("%d-%m-%Y | %I:%M %p")

    items = []
    for f in os.listdir(history_dir):
        if f == "CHATS_LOG.md" or not f.endswith(".md"):
            continue
        p = os.path.join(history_dir, f)
        try:
            with open(p, "r", encoding="utf-8") as fp:
                txt = fp.read()
                cid_m = re.search(r'([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})', txt)
                title_m = re.search(r'# 💬 تفاصيل المحادثة:\s*(.+)', txt) or re.search(r'\*\*🏷️ الاسم الحالي:\*\*\s*(.+)', txt)
                cid = cid_m.group(1).strip() if cid_m else "Unknown"
                title = title_m.group(1).strip() if title_m else f

                rows = []
                for line in txt.splitlines():
                    parts = [pt.strip() for pt in re.split(r'(?<!\\)\|', line) if pt.strip()]
                    if len(parts) >= 4 and parts[0] != "#" and parts[0].isdigit():
                        rows.append(parts)
                if rows:
                    last_row = rows[-1]
                    last_time = last_row[1].replace('\\|', '|')
                    last_old = last_row[2]
                else:
                    last_time = egypt_time
                    last_old = "-"

                items.append({
                    "title": title,
                    "old_title": last_old,
                    "cid": cid,
                    "filename": f,
                    "last_time": last_time
                })
        except Exception:
            pass

    # ترتيب المحادثات بدقة حسب التوقيت المصري تنازلياً
    items.sort(key=lambda x: parse_egypt_time(x["last_time"]), reverse=True)

    table_content = f"""# 📋 سجل المحادثات الشامل (CHATS_LOG)

> 🕒 **آخر تحديث:** `{egypt_time}` (توقيت مصر 🇪🇬)  
> 📁 **مجلد السجلات والأرشيف:** `history_logs/`

---

## 📊 جدول المحادثات المسجلة:

| # | اسم المحادثة (الحالي) | الاسم السابق (قبل) | المعرّف الكامل (ID) | ملف المحادثة التفصيلي | آخر تعديل (مصر 🇪🇬) |
|---|---|---|---|---|---|
"""
    for i, it in enumerate(items):
        clean_link = it['filename'].replace(' ', '%20')
        table_content += f"| {i+1:02d} | **{it['title']}** | {it['old_title']} | `{it['cid']}` | [فتح التفاصيل]({clean_link}) | {it['last_time']} |\n"

    table_content += """
---

### 🔍 كيف تستخدم هذا السجل؟
1. **البحث السريع:** اضغط `Ctrl + F` واكتب أي كلمة (سواء الاسم القديم أو الجديد أو الـ ID).
2. **التفاصيل الكاملة:** اضغط على رابط `[فتح التفاصيل]` بجوار أي محادثة للانتقال لملفها الفردي ومتابعة سجل تغيراتها.
3. **تحديث السجل:** يتم التحديث تلقائياً بمجرد تشغيل أداة `rename_conversation.py`.
"""

    with open(chats_log_path, "w", encoding="utf-8") as fp:
        fp.write(table_content.strip() + "\n")

def update_history_logs_all(cid, old_title, new_title):
    """تحديث السجل في جميع مسارات العمل النشطة"""
    visited = set()
    for h_dir in HISTORY_DIRS:
        parent = os.path.dirname(h_dir)
        if os.path.exists(parent):
            norm = os.path.normpath(h_dir).lower()
            if norm not in visited:
                visited.add(norm)
                try:
                    update_history_log_for_dir(h_dir, cid, old_title, new_title)
                except Exception:
                    pass

def get_current_conversation_id():
    """معرفة الـ ID لأحدث محادثة نشطة"""
    if not os.path.exists(CONVERSATIONS_DIR):
        return None
    files = glob.glob(os.path.join(CONVERSATIONS_DIR, "*.db"))
    if not files:
        return None
    latest_file = max(files, key=os.path.getmtime)
    cid = os.path.splitext(os.path.basename(latest_file))[0]
    return cid

def extract_title_from_db(db_path):
    """استخراج العنوان بدقة متناهية من ملف SQLite الخاص بالمحادثة"""
    try:
        con = sqlite3.connect(db_path)
        cur = con.cursor()
        rows = cur.execute("SELECT rowid, step_payload FROM steps WHERE step_payload IS NOT NULL LIMIT 30").fetchall()
        for rowid, p in rows:
            if not p:
                continue
            m = re.search(rb'\xf2\x01(?:[\x80-\xff]*[\x00-\x7f])\x22([\x01-\x7f])([^\x00\x08\x10\x18]{2,120})\x48', p)
            if m:
                l = m.group(1)[0]
                cand = m.group(2)[:l]
                try:
                    s = cand.decode('utf-8').strip().splitlines()[0]
                    if len(s) >= 2:
                        con.close()
                        return s
                except Exception:
                    pass
        con.close()
    except Exception:
        pass
    return None

def load_all_conversations():
    """قراءة كل المحادثات المسجلة مع عناوينها من globalStorage و conversations DB"""
    convos = {}

    # 1. قراءة المحادثات من globalStorage (trajectorySummaries)
    if os.path.exists(GLOBAL_VSCDB):
        try:
            con = sqlite3.connect(GLOBAL_VSCDB)
            row = con.cursor().execute(
                "SELECT value FROM ItemTable WHERE key=?",
                ('antigravityUnifiedStateSync.trajectorySummaries',)
            ).fetchone()
            con.close()
            if row:
                data = base64.b64decode(row[0])
                uuid_re = re.compile(rb'([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})')
                matches = list(uuid_re.finditer(data))
                for i, m in enumerate(matches):
                    uid = m.group(1).decode('ascii')
                    start = m.end()
                    next_start = matches[i+1].start() if i+1 < len(matches) else start + 2000
                    chunk = data[start:next_start]
                    b64_matches = re.findall(rb'[A-Za-z0-9+/=]{20,}', chunk)
                    for b in b64_matches:
                        try:
                            dec = base64.b64decode(b)
                            if dec.startswith(b'\n'):
                                l = dec[1]
                                t = dec[2:2+l].decode('utf-8', errors='ignore').strip().splitlines()[0]
                                if len(t) >= 2:
                                    convos[uid] = {
                                        "id": uid,
                                        "title": t,
                                        "source": "globalStorage",
                                        "mtime": 0
                                    }
                                    break
                        except Exception:
                            pass
        except Exception:
            pass

    # 2. تحديث تواريخ التعديل وربط ملفات .db
    if os.path.exists(CONVERSATIONS_DIR):
        for uid in list(convos.keys()):
            f = os.path.join(CONVERSATIONS_DIR, f"{uid}.db")
            if os.path.exists(f):
                convos[uid]["mtime"] = os.path.getmtime(f)

        for f in glob.glob(os.path.join(CONVERSATIONS_DIR, "*.db")):
            uid = os.path.splitext(os.path.basename(f))[0]
            mtime = os.path.getmtime(f)
            if uid not in convos:
                title = extract_title_from_db(f)
                if title:
                    convos[uid] = {
                        "id": uid,
                        "title": title,
                        "source": "conversations_db",
                        "mtime": mtime
                    }
            else:
                convos[uid]["mtime"] = max(convos[uid]["mtime"], mtime)
                db_title = extract_title_from_db(f)
                if db_title:
                    convos[uid]["title"] = db_title

    sorted_convos = sorted(convos.values(), key=lambda x: x["mtime"], reverse=True)
    return sorted_convos

def rename_in_conversation_db(cid, old_title, new_title):
    """تعديل العنوان وضبط Varint Length داخل قاعدة بيانات المحادثة"""
    db_path = os.path.join(CONVERSATIONS_DIR, f"{cid}.db")
    if not os.path.exists(db_path):
        return False, f"ملف قاعدة البيانات غير موجود: {db_path}"

    try:
        shutil.copyfile(db_path, db_path + ".bak")

        con = sqlite3.connect(db_path)
        cur = con.cursor()

        old_bytes = old_title.encode('utf-8') if old_title else None
        new_bytes = new_title.encode('utf-8')
        new_proto = b'\x22' + encode_varint(len(new_bytes)) + new_bytes

        updated_count = 0
        rows = cur.execute("SELECT rowid, step_payload FROM steps WHERE step_payload IS NOT NULL").fetchall()

        for rowid, payload in rows:
            changed = False
            new_payload = payload

            if old_bytes and old_bytes in new_payload:
                old_proto = b'\x22' + encode_varint(len(old_bytes)) + old_bytes
                if old_proto in new_payload:
                    new_payload = new_payload.replace(old_proto, new_proto)
                    changed = True
                else:
                    new_payload = new_payload.replace(old_bytes, new_bytes)
                    changed = True
            elif rowid in (5, 6, 7):
                idx = new_payload.find(b'\x22')
                if idx != -1 and idx + 2 < len(new_payload):
                    l, var_len = decode_varint(new_payload, idx + 1)
                    if 2 <= l <= 150:
                        old_chunk = new_payload[idx : idx + 1 + var_len + l]
                        new_payload = new_payload.replace(old_chunk, new_proto)
                        changed = True

            if changed:
                # تصحيح طول field 30 بدقة
                f30_idx = new_payload.find(b'\xf2\x01')
                if f30_idx != -1 and f30_idx + 4 < len(new_payload):
                    content = new_payload[f30_idx+4:]
                    nlen = len(content)
                    b1 = (nlen & 0x7f) | 0x80
                    b2 = (nlen >> 7) & 0x7f
                    new_payload = new_payload[:f30_idx+2] + bytes([b1, b2]) + content

                cur.execute("UPDATE steps SET step_payload = ? WHERE rowid = ?", (new_payload, rowid))
                updated_count += 1

        meta_rows = cur.execute("SELECT rowid, metadata FROM steps WHERE metadata IS NOT NULL").fetchall()
        for rowid, meta in meta_rows:
            if old_bytes and old_bytes in meta:
                cur.execute("UPDATE steps SET metadata = ? WHERE rowid = ?", (meta.replace(old_bytes, new_bytes), rowid))

        con.commit()
        con.close()
        return True, f"تم التحديث في {updated_count} خطوة بنجاح داخل ملف المحادثة."
    except Exception as e:
        return False, f"خطأ أثناء تعديل ملف المحادثة: {e}"

def rename_in_global_storage(cid, new_title, old_title=None):
    """تعديل العنوان في globalStorage/state.vscdb وضبط أطوال البايتات بدقة"""
    if not os.path.exists(GLOBAL_VSCDB):
        return False, "ملف globalStorage/state.vscdb غير موجود."

    try:
        shutil.copyfile(GLOBAL_VSCDB, GLOBAL_VSCDB + ".bak_rename")

        con = sqlite3.connect(GLOBAL_VSCDB)
        cur = con.cursor()
        row = cur.execute(
            "SELECT value FROM ItemTable WHERE key='antigravityUnifiedStateSync.trajectorySummaries'"
        ).fetchone()

        if not row:
            con.close()
            return False, "مفتاح trajectorySummaries غير موجود."

        data = base64.b64decode(row[0])
        cid_bytes = cid.encode('ascii')
        idx = data.find(cid_bytes)

        if idx == -1:
            con.close()
            return True, "المحادثة غير متزامنة في globalStorage بعد (ستتزامن تلقائياً)."

        chunk_after = data[idx:idx+2500]
        matches = list(re.finditer(rb'[A-Za-z0-9+/=]{30,}', chunk_after))

        replaced = False
        new_data = data

        for m in matches:
            b64_bytes = m.group(0)
            try:
                dec = base64.b64decode(b64_bytes)
                if dec.startswith(b'\n'):
                    old_len, var_len = decode_varint(dec, 1)

                    new_title_bytes = new_title.encode('utf-8')
                    new_dec = b'\n' + encode_varint(len(new_title_bytes)) + new_title_bytes + dec[1 + var_len + old_len:]
                    new_b64 = base64.b64encode(new_dec)

                    abs_start = idx + m.start()
                    abs_end = idx + m.end()

                    diff = len(new_b64) - len(b64_bytes)
                    new_data = data[:abs_start] + new_b64 + data[abs_end:]

                    # ضبط طول الرسالة الأب إذا تغير الحجم
                    if diff != 0 and idx >= 4:
                        try:
                            p = idx - 2
                            p_start = p - 1
                            while p_start > 0 and (data[p_start] & 0x80):
                                p_start -= 1
                            curr_len, v_size = decode_varint(data, p_start)
                            updated_entry_len = curr_len + diff
                            new_var = encode_varint(updated_entry_len)
                            new_data = new_data[:p_start] + new_var + new_data[p:]
                        except Exception:
                            pass

                    replaced = True
                    break
            except Exception:
                pass

        if replaced:
            new_outer_b64 = base64.b64encode(new_data).decode('ascii')
            cur.execute("UPDATE ItemTable SET value=? WHERE key='antigravityUnifiedStateSync.trajectorySummaries'", (new_outer_b64,))
            con.commit()
            con.close()
            return True, "تم التحديث بنجاح في سجلات globalStorage!"
        else:
            con.close()
            return False, "لم يتم العثور على كتلة العنوان في globalStorage."
    except Exception as e:
        return False, f"خطأ في globalStorage: {e}"

def rename_in_workspaces(old_title, new_title, cid):
    """تحديث العنوان في سجلات workspaceStorage"""
    if not os.path.exists(WORKSPACE_STORAGE_DIR):
        return 0

    count = 0
    for ws_db in glob.glob(os.path.join(WORKSPACE_STORAGE_DIR, "*", "state.vscdb")):
        try:
            con = sqlite3.connect(ws_db)
            cur = con.cursor()
            rows = cur.execute("SELECT key, value FROM ItemTable").fetchall()
            updated = False
            for k, v in rows:
                if (old_title and old_title in v) or (cid and cid in v):
                    if old_title and old_title in v:
                        new_v = v.replace(old_title, new_title)
                        cur.execute("UPDATE ItemTable SET value=? WHERE key=?", (new_v, k))
                        updated = True
            if updated:
                con.commit()
                count += 1
            con.close()
        except Exception:
            pass
    return count

def perform_rename(cid, new_title, old_title=None):
    """تنفيذ التعديل الشامل وتوثيقه في الأرشيف وطباعة النتيجة باللون الأزرق"""
    if not old_title:
        db_path = os.path.join(CONVERSATIONS_DIR, f"{cid}.db")
        if os.path.exists(db_path):
            old_title = extract_title_from_db(db_path)

    rename_in_conversation_db(cid, old_title, new_title)
    rename_in_global_storage(cid, new_title, old_title)
    rename_in_workspaces(old_title, new_title, cid)

    # توثيق العملية فوراً في سجل الأرشيف history_logs و CHATS_LOG.md
    update_history_logs_all(cid, old_title, new_title)

    egypt_time_now = datetime.now().strftime("%d-%m-%Y | %I:%M %p")

    # النتيجة باللون الأزرق كما طلب المستخدم بالظبط
    print()
    print(f"{BLUE}══════════════════════════════════════════════════════════════{RESET}")
    print(f"{BLUE} 🎉 تم تغيير اسم المحادثة وتوثيقها بنجاح!{RESET}")
    print(f"{BLUE}    🏷️  الاسم الجديد: {BOLD}{new_title}{RESET}")
    print(f"{BLUE}    🆔 ID: {cid}{RESET}")
    print(f"{BLUE}    🕒 توقيت مصر: {egypt_time_now} 🇪🇬{RESET}")
    print(f"{BLUE}    📁 تم التوثيق في: history_logs/CHATS_LOG.md{RESET}")
    print(f"{BLUE}══════════════════════════════════════════════════════════════{RESET}")
    print(f"\n{YELLOW}💡 ملحوظة هامة جداً:{RESET}")
    print(f"   عشان يظهر الاسم الجديد فوراً في قائمة المحادثات:")
    print(f"   اقفل برنامج {BOLD}Antigravity IDE{RESET} بالكامل وافتحه تاني! 🚀\n")

def run_interactive_flow():
    """الواجهة التفاعلية السلسة الملونة عند الضغط على Run ▶️"""
    print(f"{CYAN}{'='*60}{RESET}")
    print(f"{BOLD}{CYAN}   🌟 أداة تغيير وتعديل أسماء محادثات Antigravity IDE 🌟{RESET}")
    print(f"{CYAN}{'='*60}{RESET}\n")

    print("جاري تحميل قائمة المحادثات...\n")
    convos = load_all_conversations()
    current_id = get_current_conversation_id()

    old_input = input(f"{BOLD}👉 اكتب اسم المحادثة القديم اللي عايز تغيره (قبل) [أو اضغط Enter لعرض المحادثات]: {RESET}").strip()

    target_cid = None
    target_old_title = None

    if not old_input:
        print(f"\n{CYAN}📋 أحدث المحادثات المتاحة:{RESET}")
        print("-" * 60)
        display_convos = convos[:15]
        for i, c in enumerate(display_convos):
            is_curr = f" {YELLOW}(الحالية ⭐){RESET}" if c["id"] == current_id else ""
            print(f" [{i+1:02d}] {c['title']}{is_curr}")
            print(f"      ID: {c['id']}")
        print("-" * 60)

        num = input(f"\n{BOLD}👉 اختر رقم المحادثة: {RESET}").strip()
        try:
            idx = int(num) - 1
            if 0 <= idx < len(display_convos):
                target_cid = display_convos[idx]["id"]
                target_old_title = display_convos[idx]["title"]
            else:
                print(f"{RED}❌ رقم غير صحيح!{RESET}")
                return
        except ValueError:
            print(f"{RED}❌ إدخال غير سليم!{RESET}")
            return
    else:
        matches = []
        for c in convos:
            if old_input.lower() in c["title"].lower() or old_input.lower() == c["id"].lower():
                matches.append(c)

        if len(matches) == 1:
            target_cid = matches[0]["id"]
            target_old_title = matches[0]["title"]
        elif len(matches) > 1:
            print(f"\n{YELLOW}🔍 تم العثور على أكثر من محادثة مطابقة:{RESET}")
            for i, m in enumerate(matches):
                print(f" [{i+1}] {m['title']} ({m['id']})")
            choice = input(f"\n{BOLD}👉 اختر رقم المحادثة المطلوبة: {RESET}").strip()
            try:
                c_idx = int(choice) - 1
                if 0 <= c_idx < len(matches):
                    target_cid = matches[c_idx]["id"]
                    target_old_title = matches[c_idx]["title"]
                else:
                    print(f"{RED}❌ رقم غير صحيح!{RESET}")
                    return
            except ValueError:
                print(f"{RED}❌ إدخال غير سليم!{RESET}")
                return
        else:
            print(f"\n{RED}❌ لم يتم العثور على محادثة تحتوي على: '{old_input}'!{RESET}")
            print(f"{YELLOW}إليك أحدث المحادثات المسجلة لديك:{RESET}")
            for i, c in enumerate(convos[:8]):
                print(f" - {c['title']}")
            return

    # طباعة اللون الأخضر عند العثور على المحادثة
    print()
    print(f"{GREEN}══════════════════════════════════════════════════════════════{RESET}")
    print(f"{GREEN} ✅ تمام! تم العثور على المحادثة بنجاح:{RESET}")
    print(f"{GREEN}    🏷️  الاسم الحالي (قبل): {BOLD}{target_old_title}{RESET}")
    print(f"{GREEN}    🆔 ID: {target_cid}{RESET}")
    print(f"{GREEN}══════════════════════════════════════════════════════════════{RESET}\n")

    # طلب الاسم الجديد
    new_input = input(f"{BOLD}{GREEN}✍️ ادخل الاسم الجديد اللي عايز تغيره (بعد): {RESET}").strip()
    if not new_input:
        print(f"\n{RED}❌ تم الإلغاء، لم تقم بإدخال اسم جديد.{RESET}")
        return

    # تنفيذ التعديل والتوثيق وإظهار اللون الأزرق
    perform_rename(target_cid, new_input, target_old_title)

if __name__ == "__main__":
    try:
        run_interactive_flow()
    except KeyboardInterrupt:
        print("\n\nتم الإلغاء بواسطة المستخدم.")
    input("\nاضغط Enter للخروج...")
