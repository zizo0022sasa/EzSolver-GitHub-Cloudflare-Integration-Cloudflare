import asyncio
import json
import os
import platform
import random
import subprocess
import time
from typing import Optional
"""
MADE BY ISMOILOFF. GOOD LUCK HAVE FUN, THIS IS JUST PROJECT, USE IT ON UR OWN RISKS!

"""
import nodriver as uc

# Performance and resource-saving flags for Chrome
CHROME_ARGS = [
    "--disable-dev-shm-usage",
    "--disable-background-networking",
    "--disable-background-timer-throttling",
    "--disable-renderer-backgrounding",
    "--disable-breakpad",
    "--disable-component-update",
    "--disable-domain-reliability",
    "--disable-sync",
    "--disable-translate",
    "--mute-audio",
    "--disk-cache-size=33554432",  # Cap disk cache to 32MB
    "--js-flags=--max-old-space-size=256",  # Cap V8 heap to 256MB
]


def _find_chrome() -> str:
    """Return the Chrome executable path, checking common locations per OS."""
    if os.environ.get("CHROME_PATH"):
        return os.environ["CHROME_PATH"]

    if platform.system() == "Windows":
        candidates = [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
        ]
    else:
        candidates = [
            "/usr/bin/google-chrome-stable",
            "/usr/bin/google-chrome",
            "/usr/bin/chromium-browser",
            "/usr/bin/chromium",
        ]

    for path in candidates:
        if os.path.isfile(path):
            return path

    raise FileNotFoundError(
        "Chrome not found in default locations. "
        "Set the CHROME_PATH environment variable to your Chrome executable."
    )


def _get_profile_dir() -> str:
    """Return a persistent Chrome profile directory for the current OS."""
    if os.environ.get("TS_PROFILE_DIR"):
        return os.environ["TS_PROFILE_DIR"]
    if platform.system() == "Windows":
        base = os.environ.get("TEMP") or os.environ.get("TMP") or r"C:\Temp"
        return os.path.join(base, "ts_profile")
    return "/tmp/ts_profile"


def _is_root() -> bool:
    """Check if running as root on Linux."""
    return platform.system() == "Linux" and hasattr(os, "geteuid") and os.geteuid() == 0


def _start_xvfb_if_needed(display: str = ":99") -> Optional[subprocess.Popen]:
    """On Linux headless servers, start a lightweight virtual display."""
    if platform.system() != "Linux":
        return None
    if os.environ.get("DISPLAY"):
        return None
    proc = subprocess.Popen(
        ["Xvfb", display, "-screen", "0", "1024x768x16"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    os.environ["DISPLAY"] = display
    time.sleep(0.5)
    return proc


async def start_browser(profile_dir: Optional[str] = None) -> uc.Browser:
    """Launch an optimized Chrome browser with minimal resource consumption."""
    return await uc.start(
        browser_executable_path=_find_chrome(),
        headless=False,
        user_data_dir=profile_dir or _get_profile_dir(),
        browser_args=CHROME_ARGS,
        sandbox=not _is_root(),
    )


async def solve_on_page(page: uc.Tab, sitekey: str, siteurl: str, timeout: int = 45) -> str:
    """Solve Cloudflare Turnstile on a given page/tab."""
    await page.get(siteurl)
    await asyncio.sleep(1.5)

    # Inject Turnstile widget cleanly without window.stop() disrupting scripts
    inject_script = f"""
    (() => {{
        window._cf_extracted_token = null;
        window._cf_extracted_error = null;

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
                            sitekey: "{sitekey}",
                            callback: function(token) {{
                                window._cf_extracted_token = token;
                            }},
                            "error-callback": function(code) {{
                                window._cf_extracted_error = code;
                            }}
                        }});
                    }}
                }} catch(e) {{
                    try {{
                        window._turnstile_widget_id = window.turnstile.render("#cf-auto-container", {{
                            sitekey: "{sitekey}",
                            callback: function(token) {{
                                window._cf_extracted_token = token;
                            }},
                            "error-callback": function(code) {{
                                window._cf_extracted_error = code;
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
            s.onerror = (e) => {{ window._cf_extracted_error = "SCRIPT_LOAD_ERROR"; }};
            window.cfAutoLoaded = function() {{ renderTurnstile(); }};
            document.head.appendChild(s);
        }} else {{
            renderTurnstile();
        }}
    }})();
    """
    await page.evaluate(inject_script)

    async def get_state() -> dict:
        raw = await page.evaluate("""
            JSON.stringify((() => {
                if (window._cf_extracted_error) return {error: window._cf_extracted_error};
                if (window._cf_extracted_token) return {token: window._cf_extracted_token};
                const inp = document.querySelector('[name="cf-turnstile-response"]');
                if (inp && inp.value) return {token: inp.value};
                return {};
            })())
        """)
        return json.loads(raw) if raw and raw != 'null' else {}

    async def get_cf_iframe_rect() -> Optional[dict]:
        raw = await page.evaluate("""
            JSON.stringify((() => {
                let f = document.querySelector('#cf-auto-container iframe');
                if (!f) {
                    for (const el of document.querySelectorAll('iframe')) {
                        const src = el.src || el.getAttribute('src') || '';
                        if (src.includes('challenges.cloudflare.com')) { f = el; break; }
                    }
                }
                if (f) {
                    const r = f.getBoundingClientRect();
                    if (r.width > 20 && r.height > 20) return {x: r.x, y: r.y, w: r.width, h: r.height};
                }
                return null;
            })())
        """)
        if raw and raw != 'null':
            return json.loads(raw)
        return None

    async def do_click(rect: Optional[dict]):
        if rect:
            cx = rect["x"] + 30 + random.uniform(-3, 3)
            cy = rect["y"] + rect["h"] / 2 + random.uniform(-3, 3)
            print(f"[solver] clicking Cloudflare iframe at ({cx:.0f}, {cy:.0f})")
        else:
            cx = 250 + random.uniform(-5, 5)
            cy = 150 + random.uniform(-5, 5)
            print(f"[solver] clicking fallback position ({cx:.0f}, {cy:.0f})")
        await page.mouse_move(cx - 50, cy - 20)
        await asyncio.sleep(random.uniform(0.1, 0.2))
        await page.mouse_move(cx, cy)
        await asyncio.sleep(random.uniform(0.05, 0.1))
        await page.mouse_click(cx, cy)

    start_time = asyncio.get_event_loop().time()
    deadline = start_time + timeout
    click_count = 0
    last_click = 0.0

    while asyncio.get_event_loop().time() < deadline:
        st = await get_state()
        if st.get("error"):
            raise RuntimeError(f"Cloudflare Turnstile error {st['error']}")
        if st.get("token"):
            return st["token"]

        now = asyncio.get_event_loop().time()
        # If 4 seconds passed after page load and no token yet, attempt interaction if iframe exists
        if (now - start_time > 4) and (click_count == 0 or (now - last_click > 6)):
            if click_count < 3:
                rect = await get_cf_iframe_rect()
                if rect:
                    await do_click(rect)
                    last_click = asyncio.get_event_loop().time()
                    click_count += 1

        await asyncio.sleep(0.5)

    st = await get_state()
    if st.get("token"):
        return st["token"]
    raise TimeoutError(f"Turnstile token not obtained within {timeout}s")


async def _solve(sitekey: str, siteurl: str, timeout: int) -> str:
    browser = await start_browser()
    try:
        page = await browser.get("about:blank")
        return await solve_on_page(page, sitekey, siteurl, timeout)
    finally:
        browser.stop()


def solve(sitekey: str, siteurl: str, timeout: int = 45) -> str:
    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return asyncio.run(_solve(sitekey, siteurl, timeout))


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        print("Usage: python solver.py <sitekey> <siteurl> [timeout]")
        sys.exit(1)

    timeout = int(sys.argv[3]) if len(sys.argv) > 3 else 45
    xvfb = _start_xvfb_if_needed()
    try:
        token = solve(sys.argv[1], sys.argv[2], timeout=timeout)
        print(token)
    finally:
        if xvfb:
            xvfb.terminate()
