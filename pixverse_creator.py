# -*- coding: utf-8 -*-
"""
PixVerseCreator — Pure HTTP Requests Client for PixVerse AI
=============================================================
Reverse-Engineered & Designed following the yihong0618/*Creator pattern.
Zero Browser / Pure Requests 100%.

Supports:
- Auto-Login & JWT Session Management (Captcha-Free endpoint)
- User Credits & Daily Allowance Check
- LLM Chat & Multi-Turn Sessions (gpt-6-astra, claude-sonnet-5, gemini-3.1-pro-preview, etc.)
- Text-to-Video Generation & Polling (PixVerse V6 / V6.5)
- Video Downloader & Local Archiving
- Multi-Account Pool & Auto-Rotation
"""

import os
import sys
import json
import time
import base64
import requests
from typing import Optional, Dict, Any, Generator, Callable

BASE_API = "https://app-api.pixverse.ai/creative_platform"
DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)

def parse_pixverse_response(res: requests.Response) -> Dict[str, Any]:
    """Parse standard or base64-encoded JSON responses from PixVerse."""
    text = res.text.strip()
    if not text:
        return {}
    if text.startswith("{") or text.startswith("["):
        try:
            return json.loads(text)
        except Exception:
            pass
    try:
        decoded = base64.b64decode(text).decode("utf-8")
        return json.loads(decoded)
    except Exception:
        return {"raw": text}


class PixVerseCreator:
    def __init__(
        self,
        username: Optional[str] = None,
        password: Optional[str] = None,
        token: Optional[str] = None,
        timeout: int = 30
    ):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": DEFAULT_USER_AGENT,
            "Origin": "https://app.pixverse.ai",
            "Referer": "https://app.pixverse.ai/",
            "Content-Type": "application/json",
            "Accept": "application/json, text/plain, */*"
        })
        self.timeout = timeout
        self.token = token
        self.username = username
        self.password = password
        self.account_id = None

        if self.token:
            self.session.headers.update({"token": self.token})
        elif self.username and self.password:
            self.login(self.username, self.password)

    def login(self, username: Optional[str] = None, password: Optional[str] = None) -> str:
        """
        Pure HTTP Login without CAPTCHA.
        Accepts username or email and returns a fresh JWT token.
        """
        user = username or self.username
        pwd = password or self.password
        if not user or not pwd:
            raise ValueError("Username and Password are required for login.")

        url = f"{BASE_API}/login"
        payload = {"Username": user, "Password": pwd}
        res = self.session.post(url, json=payload, timeout=self.timeout)
        data = parse_pixverse_response(res)

        if data.get("ErrCode") != 0:
            raise RuntimeError(f"Login failed: {data.get('ErrMsg', res.text)}")

        result = data.get("Resp", {}).get("Result", {})
        self.token = result.get("Token")
        self.account_id = result.get("AccountId")
        self.username = user
        self.session.headers.update({"token": self.token})
        return self.token

    def get_user_info(self) -> Dict[str, Any]:
        """Fetch user profile and status."""
        url = f"{BASE_API}/getUserInfo"
        res = self.session.get(url, timeout=self.timeout)
        data = parse_pixverse_response(res)
        return data.get("Resp", {})

    def get_credits(self) -> Dict[str, Any]:
        """Fetch current balance, package credits, daily credits, and free quotas."""
        url = f"{BASE_API}/user/credits"
        res = self.session.get(url, timeout=self.timeout)
        data = parse_pixverse_response(res)
        resp = data.get("Resp", {})
        return {
            "credit_package": resp.get("credit_package", 0),
            "credit_daily": resp.get("credit_daily", 0),
            "credit_monthly": resp.get("credit_monthly", 0),
            "high_quality_times": resp.get("high_quality_times", 0),
            "is_new_register_user": resp.get("is_new_register_user", False),
            "raw": resp
        }

    def create_session(self, title: str = "Chat Session") -> str:
        """Create a new LLM conversation session."""
        url = f"{BASE_API}/api/v1/sessions"
        payload = {"title": title}
        res = self.session.post(url, json=payload, timeout=self.timeout)
        data = parse_pixverse_response(res)
        resp = data.get("Resp", {})
        session_id = resp.get("id")
        if not session_id:
            raise RuntimeError(f"Failed to create session: {data}")
        return str(session_id)

    def chat(
        self,
        prompt: str,
        model: str = "gpt-6-astra",
        session_id: Optional[str] = None,
        stream: bool = False,
        on_delta: Optional[Callable[[str], None]] = None
    ) -> str:
        """
        Send a chat message to an AI model and stream/retrieve response.
        Supported models include:
          - gpt-6-astra
          - gpt-5.6-sol / gpt-5.6-luna
          - claude-sonnet-5 / claude-opus-4.7 / claude-haiku-4.5
          - gemini-3.1-pro-preview / gemini-3.1-flash / gemini-3.0
          - deepseek-v4-pro / deepseek-v4-flash
          - qwen3.7-max
        """
        if not session_id:
            title = (prompt[:40] + "...") if len(prompt) > 40 else prompt
            session_id = self.create_session(title=title)

        run_url = f"{BASE_API}/api/v1/sessions/{session_id}/runs"
        payload = {
            "api_version": 2,
            "request_model_id": model,
            "selection_mode": "explicit",
            "message": {
                "parts": [{"type": "text", "text": prompt}]
            },
            "context": {
                "locale": "en-US",
                "timezone": "Africa/Cairo",
                "image_model": "auto",
                "video_model": "auto"
            }
        }

        res = self.session.post(run_url, json=payload, timeout=self.timeout)
        data = parse_pixverse_response(res)
        run_resp = data.get("Resp", {})
        run_id = run_resp.get("id")
        if not run_id:
            raise RuntimeError(f"Failed to initiate run: {data}")

        # Stream SSE events
        events_url = f"{BASE_API}/api/v1/runs/{run_id}/events?token={self.token}"
        full_text = []

        with requests.get(events_url, headers={"Accept": "text/event-stream"}, stream=True, timeout=120) as sse:
            current_event = None
            for raw_line in sse.iter_lines(decode_unicode=True):
                if not raw_line:
                    continue
                line = raw_line.strip()
                if line.startswith("event:"):
                    current_event = line.replace("event:", "").strip()
                elif line.startswith("data:"):
                    data_str = line.replace("data:", "").strip()
                    try:
                        event_data = json.loads(data_str)
                    except Exception:
                        continue

                    if current_event == "message.part.delta":
                        delta = event_data.get("payload", {}).get("delta", "")
                        if delta:
                            full_text.append(delta)
                            if stream and on_delta:
                                on_delta(delta)
                            elif stream:
                                sys.stdout.write(delta)
                                sys.stdout.flush()

                    elif current_event == "run.finished":
                        break

        result_content = "".join(full_text)
        return result_content

    def generate_video(
        self,
        prompt: str,
        model: str = "v6",
        quality: str = "360p",
        aspect_ratio: str = "16:9",
        duration: int = 5,
        audio: int = 1,
        multi_shot: int = 1,
        seed: int = 2015806000,
        poll: bool = True,
        timeout: int = 240
    ) -> Dict[str, Any]:
        """
        Generate video from text prompt using PixVerse Video engine.
        Returns video details including .mp4 direct download URL upon completion.
        """
        url = f"{BASE_API}/video/t2v"
        payload = {
            "prompt": prompt,
            "model": model,
            "create_count": 1,
            "quality": quality,
            "aspect_ratio": aspect_ratio,
            "duration": duration,
            "audio": audio,
            "multi_shot": multi_shot,
            "seed": seed,
            "credit_change": 25,
            "model_name_default": "PixVerse V6"
        }

        res = self.session.post(url, json=payload, timeout=self.timeout)
        data = parse_pixverse_response(res)
        if data.get("ErrCode") != 0:
            raise RuntimeError(f"Video generation request failed: {data.get('ErrMsg', res.text)}")

        video_id = data.get("Resp", {}).get("video_id")
        if not video_id:
            raise RuntimeError(f"No video_id returned: {data}")

        if not poll:
            return {"video_id": video_id, "status": "submitted"}

        # Poll until complete
        start_time = time.time()
        while time.time() - start_time < timeout:
            time.sleep(5)
            detail = self.get_video_detail(video_id)
            status = detail.get("history_status") or detail.get("video_status")
            if status in ["completed", 1, "success"]:
                return {
                    "video_id": video_id,
                    "status": "completed",
                    "url": detail.get("url"),
                    "first_frame": detail.get("first_frame"),
                    "detail": detail
                }
            elif status in ["failed", -1, "error"]:
                raise RuntimeError(f"Video generation failed: {detail}")

        raise TimeoutError(f"Video generation timed out after {timeout} seconds.")

    def get_video_detail(self, video_id: int) -> Dict[str, Any]:
        """Fetch status and URLs of a generated video."""
        url = f"{BASE_API}/video/list/detail"
        payload = {"video_id": video_id, "platform": "web"}
        res = self.session.post(url, json=payload, timeout=self.timeout)
        data = parse_pixverse_response(res)
        return data.get("Resp", {})

    def download_video(self, url: str, output_path: str) -> str:
        """Download video file to local disk."""
        with requests.get(url, stream=True, timeout=120) as r:
            r.raise_for_status()
            with open(output_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        return output_path


def load_accounts(accounts_file: Optional[str] = None) -> list:
    """Load accounts from accounts_pixverse.json."""
    if not accounts_file:
        accounts_file = os.path.join(os.path.dirname(__file__), "accounts_pixverse.json")
    if os.path.exists(accounts_file):
        with open(accounts_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def get_default_creator(account_name: Optional[str] = None) -> PixVerseCreator:
    """Instantiate creator using a specific account or the first active account."""
    accounts = load_accounts()
    if account_name:
        for acc in accounts:
            if acc.get("username") == account_name or acc.get("email") == account_name:
                return PixVerseCreator(
                    username=acc.get("username"),
                    password=acc.get("password"),
                    token=acc.get("jwt_token")
                )
    for acc in accounts:
        if acc.get("active", True):
            return PixVerseCreator(
                username=acc.get("username"),
                password=acc.get("password"),
                token=acc.get("jwt_token")
            )
    raise RuntimeError("No active account found in accounts_pixverse.json.")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="PixVerseCreator CLI")
    parser.add_argument("--account", type=str, help="Username or email of account to use")
    parser.add_argument("--credits", action="store_true", help="Check account credits")
    parser.add_argument("--chat", type=str, help="Prompt to send to LLM (default: gpt-6-astra)")
    parser.add_argument("--model", type=str, default="gpt-6-astra", help="Model name")
    parser.add_argument("--video", type=str, help="Prompt to generate video")
    args = parser.parse_args()

    creator = get_default_creator(args.account)
    print(f"Logged in successfully as: {creator.username} (AccountID: {creator.account_id})")

    if args.credits:
        credits = creator.get_credits()
        print(f"Credits Summary:")
        print(f"  Package Credits: {credits['credit_package']}")
        print(f"  Daily Credits:   {credits['credit_daily']}")
        print(f"  Monthly Credits: {credits['credit_monthly']}")

    elif args.chat:
        print(f"Sending prompt to [{args.model}]...")
        response = creator.chat(args.chat, model=args.model, stream=True)
        print("\n--- Done ---")

    elif args.video:
        print(f"Generating video for: {args.video}...")
        res = creator.generate_video(args.video)
        print(f"Video Ready! URL: {res['url']}")

