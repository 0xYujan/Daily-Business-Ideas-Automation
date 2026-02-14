#!/usr/bin/env python3
"""
Daily Business Ideas — Reply Checker (Phase 2)
Checks Gmail for replies to the preview email.
When user replies with idea titles, sends back full detailed breakdowns.
Runs every 5 minutes via cron.
"""

import json
import imaplib
import email as email_lib
import smtplib
import sys
import logging
import re
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from pathlib import Path

# ─── Constants ───────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent
CONFIG_FILE = BASE_DIR / "config.json"
PENDING_FILE = BASE_DIR / "pending_details.json"
PROCESSED_FILE = BASE_DIR / "processed_replies.json"
LOG_FILE = BASE_DIR / "automation.log"

# ─── Logging ─────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger("reply_checker")


def load_json(fp: Path):
    if not fp.exists():
        return {}
    with open(fp, "r", encoding="utf-8-sig") as f:
        return json.load(f)


def save_json(fp: Path, data):
    with open(fp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


# ─── IMAP: Check for replies ────────────────────────────────────────────────
def get_reply_emails(config):
    """Connect via IMAP and find unread replies to our digest emails."""
    replies = []

    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com", 993)
        mail.login(config["sender_email"], config["sender_password"])
        mail.select("INBOX")

        # Search for unread emails from self (replies go back to sender)
        _, msg_nums = mail.search(None, '(UNSEEN SUBJECT "Re: " FROM "{}")'.format(config["sender_email"]))

        if not msg_nums[0]:
            # Also check for replies from the recipient (in case sender != recipient)
            _, msg_nums = mail.search(None, '(UNSEEN SUBJECT "Re: " FROM "{}")'.format(config["recipient_email"]))

        if not msg_nums[0]:
            # Broader search: any unread reply to our subject pattern
            _, msg_nums = mail.search(None, '(UNSEEN SUBJECT "Re: " SUBJECT "Startup Ideas")')

        if msg_nums[0]:
            for num in msg_nums[0].split():
                _, msg_data = mail.fetch(num, "(RFC822)")
                raw = msg_data[0][1]
                msg = email_lib.message_from_bytes(raw)

                subject = msg.get("Subject", "")
                from_addr = msg.get("From", "")
                msg_id = msg.get("Message-ID", "")

                # Extract body text
                body = ""
                if msg.is_multipart():
                    for part in msg.walk():
                        ct = part.get_content_type()
                        if ct == "text/plain":
                            payload = part.get_payload(decode=True)
                            if payload:
                                body = payload.decode("utf-8", errors="ignore")
                                break
                        elif ct == "text/html" and not body:
                            payload = part.get_payload(decode=True)
                            if payload:
                                # Strip HTML tags for simple parsing
                                html_text = payload.decode("utf-8", errors="ignore")
                                body = re.sub(r"<[^>]+>", " ", html_text)
                else:
                    payload = msg.get_payload(decode=True)
                    if payload:
                        body = payload.decode("utf-8", errors="ignore")

                # Clean up the reply body (remove quoted original message)
                # Most email clients add "On <date> <sender> wrote:" before the quote
                clean_body = body
                for pattern in [
                    r"On .+wrote:",
                    r"----+ ?Original Message ?----+",
                    r"From: .+",
                    r"> ",
                ]:
                    parts = re.split(pattern, clean_body, maxsplit=1)
                    if len(parts) > 1:
                        clean_body = parts[0]

                clean_body = clean_body.strip()

                if clean_body:
                    replies.append({
                        "msg_id": msg_id,
                        "subject": subject,
                        "from": from_addr,
                        "body": clean_body,
                        "num": num,
                    })
                    log.info(f"📨 Found reply: \"{clean_body[:100]}...\"")

                # Mark as read
                mail.store(num, "+FLAGS", "\\Seen")

        mail.logout()

    except Exception as e:
        log.error(f"❌ IMAP error: {e}")

    return replies


# ─── Match idea titles from reply body ───────────────────────────────────────
def match_ideas(reply_body: str, pending_ideas: dict) -> list:
    """Fuzzy match idea names mentioned in the reply against pending ideas."""
    matched = []
    reply_lower = reply_body.lower().strip()

    # Check if user wants ALL ideas
    if reply_lower in ("all", "send all", "all ideas", "everything", "yes", "send me all"):
        return list(pending_ideas.values())

    for name, idea in pending_ideas.items():
        name_lower = name.lower()

        # Exact or partial match
        if name_lower in reply_lower:
            matched.append(idea)
            continue

        # Check individual significant words (skip common words)
        skip_words = {"nepal", "ai", "the", "for", "and", "pro", "app", "my", "a", "an"}
        words = [w for w in name_lower.split() if w not in skip_words and len(w) > 2]
        if words and all(w in reply_lower for w in words):
            matched.append(idea)
            continue

        # Check if user typed the idea number (e.g., "1, 3, 5" or "idea 2")
        numbers = re.findall(r"\b(\d)\b", reply_lower)
        idea_index = list(pending_ideas.keys()).index(name) + 1
        if str(idea_index) in numbers:
            matched.append(idea)

    return matched


# ─── Build detailed HTML for matched ideas ───────────────────────────────────
def build_detail_html(ideas: list, date_str: str) -> str:
    ideas_html = ""
    for idx, idea in enumerate(ideas, 1):
        is_hr = idea.get("is_high_risk", False)
        border_color = "#e94560" if is_hr else "#2d2d4a"
        label = "🔥 HIGH-RISK HIGH-REWARD" if is_hr else f"💡 Idea #{idx}"
        cost_color = {"Low": "#22c55e", "Medium": "#f59e0b", "High": "#ef4444"}.get(idea.get("startup_cost", ""), "#64748b")

        action_rows = ""
        for step in idea.get("action_plan", []):
            action_rows += f'<tr><td style="padding:4px 8px;font-size:12px;color:#cbd5e1;border-bottom:1px solid #2d2d4a;">{step}</td></tr>'

        hr_box = ""
        if is_hr:
            hr_box = f"""
            <table width="100%" style="margin-top:16px;" cellpadding="0" cellspacing="8">
            <tr>
              <td width="50%" style="background:#1a0a0a;border-radius:8px;padding:12px;vertical-align:top;">
                <p style="margin:0 0 4px;font-size:11px;font-weight:bold;color:#ef4444;">⚠ WHY HIGH RISK</p>
                <p style="margin:0;font-size:13px;color:#fca5a5;line-height:1.5;">{idea.get('high_risk_reason', '')}</p>
              </td>
              <td width="50%" style="background:#0a1a0a;border-radius:8px;padding:12px;vertical-align:top;">
                <p style="margin:0 0 4px;font-size:11px;font-weight:bold;color:#22c55e;">💎 WHY HIGH REWARD</p>
                <p style="margin:0;font-size:13px;color:#86efac;line-height:1.5;">{idea.get('high_risk_reward', '')}</p>
              </td>
            </tr>
            </table>"""

        ideas_html += f"""
        <table width="100%" cellpadding="0" cellspacing="0" style="margin:20px 0;background:#1e1e32;border-radius:12px;border:1px solid {border_color};">
        <tr><td style="padding:24px;">
          <p style="margin:0;font-size:12px;font-weight:bold;color:{'#f59e0b' if is_hr else '#64748b'};text-transform:uppercase;letter-spacing:2px;">{label}</p>
          <h2 style="margin:6px 0 0;font-size:22px;color:#e2e8f0;">{idea['business_name']}</h2>
          <span style="background:#2d2d4a;color:#a78bfa;padding:3px 10px;border-radius:20px;font-size:11px;">{idea['category']}</span>

          <p style="margin:16px 0 4px;font-size:11px;font-weight:bold;color:#e94560;text-transform:uppercase;letter-spacing:1px;">🔹 What It Does</p>
          <p style="margin:0;font-size:14px;color:#cbd5e1;line-height:1.6;">{idea['what_it_does']}</p>

          <p style="margin:16px 0 4px;font-size:11px;font-weight:bold;color:#e94560;text-transform:uppercase;letter-spacing:1px;">🔹 Where It Is Working</p>
          <p style="margin:0;font-size:14px;color:#cbd5e1;">{idea['where_working']}</p>

          <p style="margin:16px 0 4px;font-size:11px;font-weight:bold;color:#e94560;text-transform:uppercase;letter-spacing:1px;">🔹 Why It Is Growing</p>
          <p style="margin:0;font-size:14px;color:#cbd5e1;line-height:1.6;">{idea['why_growing']}</p>

          <p style="margin:16px 0 4px;font-size:11px;font-weight:bold;color:#e94560;text-transform:uppercase;letter-spacing:1px;">🔹 How To Adapt For Nepal</p>
          <p style="margin:0;font-size:14px;color:#cbd5e1;line-height:1.6;">{idea['nepal_adaptation']}</p>

          {hr_box}

          <table width="100%" style="margin-top:16px;" cellpadding="0" cellspacing="0">
          <tr>
            <td width="50%">
              <p style="margin:0 0 4px;font-size:11px;font-weight:bold;color:#e94560;text-transform:uppercase;">🔹 Startup Cost</p>
              <p style="margin:0;"><span style="background:{cost_color}22;color:{cost_color};padding:3px 10px;border-radius:8px;font-size:13px;font-weight:bold;">{idea['startup_cost']}</span>
              <span style="color:#64748b;font-size:12px;margin-left:6px;">{idea.get('cost_estimate','')}</span></p>
            </td>
            <td width="50%">
              <p style="margin:0 0 4px;font-size:11px;font-weight:bold;color:#e94560;text-transform:uppercase;">🔹 Monetization</p>
              <p style="margin:0;font-size:13px;color:#cbd5e1;">{idea['monetization']}</p>
            </td>
          </tr>
          </table>

          <p style="margin:16px 0 8px;font-size:11px;font-weight:bold;color:#e94560;text-transform:uppercase;letter-spacing:1px;">🔹 30-Day Action Plan</p>
          <table width="100%" style="background:#15152a;border-radius:8px;" cellpadding="0" cellspacing="0">
          {action_rows}
          </table>
        </td></tr>
        </table>"""

    html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"></head>
<body style="margin:0;padding:0;background:#0f0f1a;font-family:'Segoe UI',Tahoma,Geneva,Verdana,sans-serif;">

<table width="100%" cellpadding="0" cellspacing="0" style="background:linear-gradient(135deg,#1a1a2e,#16213e,#0f3460);">
<tr><td style="padding:30px 20px;text-align:center;">
  <h1 style="margin:0;font-size:26px;color:#e94560;">📋 Full Breakdown — {len(ideas)} Idea{'s' if len(ideas) != 1 else ''}</h1>
  <p style="margin:8px 0 0;font-size:14px;color:#a8b2d1;">{date_str}</p>
  <p style="margin:6px 0 0;font-size:12px;color:#94a3b8;">Here are the detailed breakdowns you requested</p>
</td></tr>
</table>

<table width="100%" cellpadding="0" cellspacing="0">
<tr><td style="padding:0 20px 20px;">
{ideas_html}
</td></tr>
</table>

<table width="100%" cellpadding="0" cellspacing="0" style="background:#1a1a2e;">
<tr><td style="padding:20px;text-align:center;">
  <p style="margin:0;font-size:11px;color:#475569;">Business Automation System • Daily Ideas at 6:00 AM NPT</p>
</td></tr>
</table>

</body></html>"""
    return html


# ─── Send detail email ───────────────────────────────────────────────────────
def send_email(config, subject, html):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = config["sender_email"]
    msg["To"] = config["recipient_email"]
    msg.attach(MIMEText(html, "html", "utf-8"))

    with smtplib.SMTP(config["smtp_server"], config["smtp_port"]) as s:
        s.ehlo()
        s.starttls()
        s.ehlo()
        s.login(config["sender_email"], config["sender_password"])
        s.send_message(msg)
    log.info("📧 Detail email sent!")


# ─── Main ────────────────────────────────────────────────────────────────────
def main():
    config = load_json(CONFIG_FILE)
    pending = load_json(PENDING_FILE)
    processed = load_json(PROCESSED_FILE) if PROCESSED_FILE.exists() else {"processed_ids": []}

    if not pending or "ideas" not in pending:
        return  # No pending ideas — nothing to check

    # Check for replies
    replies = get_reply_emails(config)

    if not replies:
        return  # No replies found — silent exit

    log.info(f"📨 Found {len(replies)} new reply(ies)")

    for reply in replies:
        msg_id = reply["msg_id"]

        # Skip already processed replies
        if msg_id in processed.get("processed_ids", []):
            continue

        # Match idea titles
        matched = match_ideas(reply["body"], pending["ideas"])

        if not matched:
            log.info(f"⚠ Reply didn't match any ideas: \"{reply['body'][:100]}\"")
            # Send a helpful response
            no_match_html = f"""<!DOCTYPE html>
<html><body style="margin:0;padding:20px;background:#0f0f1a;font-family:'Segoe UI',sans-serif;">
<div style="background:#1e1e32;border-radius:12px;padding:24px;border:1px solid #2d2d4a;">
  <h2 style="color:#e94560;">🤔 Couldn't match your request</h2>
  <p style="color:#cbd5e1;">I couldn't find matching ideas for: <em>"{reply['body'][:200]}"</em></p>
  <p style="color:#94a3b8;">Available ideas today:</p>
  <ul style="color:#a78bfa;">
    {"".join(f"<li>{name}</li>" for name in pending['ideas'].keys())}
  </ul>
  <p style="color:#94a3b8;">Reply with one or more of these names, or just type <strong>"all"</strong> for everything.</p>
</div>
</body></html>"""
            send_email(config, f"📋 Help — Available Ideas for {pending.get('date_display', 'Today')}", no_match_html)
        else:
            log.info(f"✅ Matched {len(matched)} ideas: {[i['business_name'] for i in matched]}")
            date_str = pending.get("date_display", datetime.now().strftime("%B %d, %Y"))
            names = ", ".join(i["business_name"] for i in matched)
            html = build_detail_html(matched, date_str)
            send_email(config, f"📋 Full Breakdown: {names}", html)

        # Mark as processed
        processed.setdefault("processed_ids", []).append(msg_id)

    save_json(PROCESSED_FILE, processed)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log.error(f"❌ Reply checker error: {e}", exc_info=True)
        sys.exit(1)
