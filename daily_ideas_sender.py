#!/usr/bin/env python3
"""
Daily Business Ideas — Main Sender
Phase 1: Sends FULL detailed email (5 ideas + 1 high-risk) with complete breakdowns.
Phase 2: Appends 3 BONUS preview ideas (titles only) — reply to get those details.
"""

import json
import random
import smtplib
import sys
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).parent
CONFIG_FILE = BASE_DIR / "config.json"
IDEAS_FILE = BASE_DIR / "ideas_database.json"
HISTORY_FILE = BASE_DIR / "sent_history.json"
PENDING_FILE = BASE_DIR / "pending_details.json"
LOG_FILE = BASE_DIR / "automation.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger(__name__)


def load_json(fp):
    with open(fp, "r", encoding="utf-8-sig") as f:
        return json.load(f)

def save_json(fp, data):
    with open(fp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def select_ideas(ideas, history, main_count=5, bonus_count=3):
    sent = set(history.get("sent_ids", []))
    reg = [i for i in ideas if not i["is_high_risk"] and i["id"] not in sent]
    hr = [i for i in ideas if i["is_high_risk"] and i["id"] not in sent]

    need = main_count + bonus_count
    if len(reg) < need:
        log.warning("⚠ Cycling database.")
        history["sent_ids"] = []
        history["cycle_count"] = history.get("cycle_count", 0) + 1
        reg = [i for i in ideas if not i["is_high_risk"]]
        hr = [i for i in ideas if i["is_high_risk"]]

    chosen = random.sample(reg, min(need, len(reg)))
    main_ideas = chosen[:main_count]
    bonus_ideas = chosen[main_count:main_count + bonus_count]
    high_risk = random.choice(hr) if hr else None
    return main_ideas, bonus_ideas, high_risk, history


# ═══════════════════════════════════════════════════════════════════════════
#  FULL DETAIL HTML — for main 5 ideas + high-risk
# ═══════════════════════════════════════════════════════════════════════════
def render_idea_full(idea, idx):
    cc = {"Low": "#22c55e", "Medium": "#f59e0b", "High": "#ef4444"}.get(idea["startup_cost"], "#64748b")
    rows = "".join(f'<tr><td style="padding:4px 8px;font-size:12px;color:#cbd5e1;border-bottom:1px solid #2d2d4a;">{s}</td></tr>' for s in idea.get("action_plan", []))

    return f"""
<table width="100%" cellpadding="0" cellspacing="0" border="0" style="margin:20px 0;background:#1e1e32;border-radius:12px;border:1px solid #2d2d4a;">
<tr><td style="padding:24px;">
  <table width="100%"><tr>
    <td style="font-size:22px;font-weight:bold;color:#e2e8f0;">💡 Idea #{idx}: {idea['business_name']}</td>
    <td style="text-align:right;"><span style="background:#2d2d4a;color:#a78bfa;padding:4px 12px;border-radius:20px;font-size:11px;">{idea['category']}</span></td>
  </tr></table>
  <p style="margin:16px 0 4px;font-size:11px;font-weight:bold;color:#e94560;text-transform:uppercase;letter-spacing:1px;">🔹 What It Does</p>
  <p style="margin:0;font-size:14px;color:#cbd5e1;line-height:1.6;">{idea['what_it_does']}</p>
  <p style="margin:16px 0 4px;font-size:11px;font-weight:bold;color:#e94560;text-transform:uppercase;letter-spacing:1px;">🔹 Where It Is Working</p>
  <p style="margin:0;font-size:14px;color:#cbd5e1;">{idea['where_working']}</p>
  <p style="margin:16px 0 4px;font-size:11px;font-weight:bold;color:#e94560;text-transform:uppercase;letter-spacing:1px;">🔹 Why It Is Growing</p>
  <p style="margin:0;font-size:14px;color:#cbd5e1;line-height:1.6;">{idea['why_growing']}</p>
  <p style="margin:16px 0 4px;font-size:11px;font-weight:bold;color:#e94560;text-transform:uppercase;letter-spacing:1px;">🔹 How To Adapt For Nepal</p>
  <p style="margin:0;font-size:14px;color:#cbd5e1;line-height:1.6;">{idea['nepal_adaptation']}</p>
  <table width="100%" style="margin-top:16px;" cellpadding="0" cellspacing="0"><tr>
    <td width="50%" style="vertical-align:top;">
      <p style="margin:0 0 4px;font-size:11px;font-weight:bold;color:#e94560;text-transform:uppercase;letter-spacing:1px;">🔹 Startup Cost</p>
      <p style="margin:0;"><span style="background:{cc}22;color:{cc};padding:3px 10px;border-radius:8px;font-size:13px;font-weight:bold;">{idea['startup_cost']}</span>
      <span style="color:#64748b;font-size:12px;margin-left:6px;">{idea.get('cost_estimate','')}</span></p>
    </td>
    <td width="50%" style="vertical-align:top;">
      <p style="margin:0 0 4px;font-size:11px;font-weight:bold;color:#e94560;text-transform:uppercase;letter-spacing:1px;">🔹 Monetization</p>
      <p style="margin:0;font-size:13px;color:#cbd5e1;">{idea['monetization']}</p>
    </td>
  </tr></table>
  <p style="margin:16px 0 8px;font-size:11px;font-weight:bold;color:#e94560;text-transform:uppercase;letter-spacing:1px;">🔹 First 30-Day Action Plan</p>
  <table width="100%" style="background:#15152a;border-radius:8px;" cellpadding="0" cellspacing="0">{rows}</table>
</td></tr></table>"""


def render_high_risk_full(idea):
    rows = "".join(f'<tr><td style="padding:4px 8px;font-size:12px;color:#cbd5e1;border-bottom:1px solid #4a1a1a;">{s}</td></tr>' for s in idea.get("action_plan", []))

    return f"""
<table width="100%" cellpadding="0" cellspacing="0" border="0" style="margin:20px 0;background:linear-gradient(135deg,#2a1a1a,#3d1515);border-radius:12px;border:2px solid #e94560;">
<tr><td style="padding:24px;">
  <p style="margin:0;font-size:13px;font-weight:bold;color:#f59e0b;text-transform:uppercase;letter-spacing:2px;">🔥 HIGH-RISK HIGH-REWARD BONUS</p>
  <h2 style="margin:8px 0 0;font-size:24px;color:#e94560;">{idea['business_name']}</h2>
  <span style="background:#2d2d4a;color:#a78bfa;padding:3px 10px;border-radius:20px;font-size:11px;">{idea['category']}</span>
  <p style="margin:16px 0 4px;font-size:11px;font-weight:bold;color:#f59e0b;text-transform:uppercase;letter-spacing:1px;">🔹 What It Does</p>
  <p style="margin:0;font-size:14px;color:#cbd5e1;line-height:1.6;">{idea['what_it_does']}</p>
  <p style="margin:16px 0 4px;font-size:11px;font-weight:bold;color:#f59e0b;text-transform:uppercase;letter-spacing:1px;">🔹 Where It Is Working</p>
  <p style="margin:0;font-size:14px;color:#cbd5e1;">{idea['where_working']}</p>
  <p style="margin:16px 0 4px;font-size:11px;font-weight:bold;color:#f59e0b;text-transform:uppercase;letter-spacing:1px;">🔹 Why It Is Growing</p>
  <p style="margin:0;font-size:14px;color:#cbd5e1;line-height:1.6;">{idea['why_growing']}</p>
  <p style="margin:16px 0 4px;font-size:11px;font-weight:bold;color:#f59e0b;text-transform:uppercase;letter-spacing:1px;">🔹 How To Adapt For Nepal</p>
  <p style="margin:0;font-size:14px;color:#cbd5e1;line-height:1.6;">{idea['nepal_adaptation']}</p>
  <table width="100%" style="margin-top:16px;" cellpadding="0" cellspacing="8"><tr>
    <td width="50%" style="background:#1a0a0a;border-radius:8px;padding:12px;vertical-align:top;">
      <p style="margin:0 0 4px;font-size:11px;font-weight:bold;color:#ef4444;">⚠ WHY IT'S HIGH RISK</p>
      <p style="margin:0;font-size:13px;color:#fca5a5;line-height:1.5;">{idea.get('high_risk_reason','')}</p>
    </td>
    <td width="50%" style="background:#0a1a0a;border-radius:8px;padding:12px;vertical-align:top;">
      <p style="margin:0 0 4px;font-size:11px;font-weight:bold;color:#22c55e;">💎 WHY IT'S HIGH REWARD</p>
      <p style="margin:0;font-size:13px;color:#86efac;line-height:1.5;">{idea.get('high_risk_reward','')}</p>
    </td>
  </tr></table>
  <table width="100%" style="margin-top:12px;" cellpadding="0" cellspacing="0"><tr>
    <td width="50%">
      <p style="margin:0 0 4px;font-size:11px;font-weight:bold;color:#f59e0b;">🔹 Startup Cost</p>
      <p style="margin:0;font-size:13px;color:#fbbf24;">{idea['startup_cost']} — {idea.get('cost_estimate','')}</p>
    </td>
    <td width="50%">
      <p style="margin:0 0 4px;font-size:11px;font-weight:bold;color:#f59e0b;">🔹 Monetization</p>
      <p style="margin:0;font-size:13px;color:#cbd5e1;">{idea['monetization']}</p>
    </td>
  </tr></table>
  <p style="margin:16px 0 8px;font-size:11px;font-weight:bold;color:#f59e0b;text-transform:uppercase;letter-spacing:1px;">🔹 First 30-Day Action Plan</p>
  <table width="100%" style="background:#1a0a0a;border-radius:8px;" cellpadding="0" cellspacing="0">{rows}</table>
</td></tr></table>"""


# ═══════════════════════════════════════════════════════════════════════════
#  BONUS PREVIEW — titles + short desc for extra ideas (reply for details)
# ═══════════════════════════════════════════════════════════════════════════
def render_bonus_preview(bonus_ideas):
    if not bonus_ideas:
        return ""

    names = ", ".join(i["business_name"] for i in bonus_ideas[:2])
    rows = ""
    for idea in bonus_ideas:
        rows += f"""
        <tr><td style="padding:12px 16px;border-bottom:1px solid #2d2d4a;">
          <p style="margin:0;font-size:16px;font-weight:bold;color:#e2e8f0;">✦ {idea['business_name']}</p>
          <p style="margin:4px 0 0;font-size:12px;color:#a78bfa;">{idea['category']} • 💰 {idea['startup_cost']}</p>
          <p style="margin:6px 0 0;font-size:13px;color:#94a3b8;line-height:1.5;">{idea['what_it_does'][:150]}...</p>
        </td></tr>"""

    return f"""
<table width="100%" cellpadding="0" cellspacing="0" border="0">
<tr><td style="padding:10px 20px 0;">
  <table width="100%" style="background:#1a2744;border-radius:12px;border:1px solid #3b82f6;">
  <tr><td style="padding:20px;">
    <p style="margin:0;font-size:15px;font-weight:bold;color:#93c5fd;">📩 Want More? Here are {len(bonus_ideas)} bonus ideas!</p>
    <p style="margin:6px 0 16px;font-size:13px;color:#64748b;">Reply to this email with the names to get full details (e.g. "{names}")</p>
    <table width="100%" style="background:#15152a;border-radius:8px;" cellpadding="0" cellspacing="0">
    {rows}
    </table>
  </td></tr>
  </table>
</td></tr>
</table>"""


# ═══════════════════════════════════════════════════════════════════════════
#  FULL EMAIL BUILDER
# ═══════════════════════════════════════════════════════════════════════════
def build_email(main_ideas, bonus_ideas, high_risk, date_str):
    main_html = "".join(render_idea_full(i, idx) for idx, i in enumerate(main_ideas, 1))
    hr_html = render_high_risk_full(high_risk) if high_risk else ""
    bonus_html = render_bonus_preview(bonus_ideas)

    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Daily Startup Ideas — {date_str}</title></head>
<body style="margin:0;padding:0;background:#0f0f1a;font-family:'Segoe UI',Tahoma,Geneva,Verdana,sans-serif;">

<table width="100%" cellpadding="0" cellspacing="0" border="0" style="background:linear-gradient(135deg,#1a1a2e 0%,#16213e 50%,#0f3460 100%);">
<tr><td style="padding:40px 20px;text-align:center;">
  <h1 style="margin:0;font-size:32px;color:#e94560;letter-spacing:1px;">🚀 Daily Startup Ideas</h1>
  <p style="margin:10px 0 0;font-size:16px;color:#a8b2d1;">{date_str}</p>
  <p style="margin:8px 0 0;font-size:13px;color:#64748b;">5 Trending Ideas + 1 High-Risk Bonus — Adapted for Nepal</p>
</td></tr></table>

<table width="100%" cellpadding="0" cellspacing="0" border="0">
<tr><td style="padding:10px 20px 0;">{main_html}</td></tr>
</table>

<table width="100%" cellpadding="0" cellspacing="0" border="0">
<tr><td style="padding:0 20px;">{hr_html}</td></tr>
</table>

{bonus_html}

<table width="100%" cellpadding="0" cellspacing="0" border="0" style="background:#1a1a2e;margin-top:20px;">
<tr><td style="padding:30px 20px;text-align:center;">
  <p style="margin:0;font-size:12px;color:#64748b;">
    Automated by <strong style="color:#e94560;">Business Automation System</strong><br>
    Ideas curated from USA, Europe, India, Southeast Asia &amp; AI/SaaS ecosystems<br>
    <em>New ideas every day at 6:00 AM NPT</em>
  </p>
</td></tr></table>

</body></html>"""


# ═══════════════════════════════════════════════════════════════════════════
#  MARKDOWN REPORT
# ═══════════════════════════════════════════════════════════════════════════
def build_markdown(main_ideas, bonus_ideas, high_risk, date_str):
    lines = [f"# 🚀 Daily Startup Ideas — {date_str}\n",
             "**5 Trending, Tech-Enabled Business Ideas Adapted for Nepal**\n",
             "> Curated from validated models across USA, Europe, India, SE Asia & AI/SaaS.\n", "---\n"]

    for idx, idea in enumerate(main_ideas, 1):
        lines.append(f"## 💡 Idea #{idx}: {idea['business_name']}\n")
        lines.append(f"**Category:** {idea['category']}\n")
        for field, label in [("what_it_does","What It Does"),("where_working","Where Working"),
                             ("why_growing","Why Growing"),("nepal_adaptation","Nepal Adaptation")]:
            lines.append(f"### 🔹 {label}\n{idea[field]}\n")
        lines.append(f"### 🔹 Cost\n**{idea['startup_cost']}** — {idea.get('cost_estimate','')}\n")
        lines.append(f"### 🔹 Monetization\n{idea['monetization']}\n")
        lines.append("### 🔹 30-Day Action Plan\n| Phase | Action |\n|-------|--------|")
        for s in idea.get("action_plan", []):
            p = s.split(": ", 1)
            lines.append(f"| {p[0]} | {p[1] if len(p)>1 else s} |")
        lines.append("\n---\n")

    if high_risk:
        lines.append(f"## 🔥 HIGH-RISK: {high_risk['business_name']}\n")
        lines.append(f"**{high_risk['category']}** | {high_risk['what_it_does']}\n---\n")

    if bonus_ideas:
        lines.append("## 📩 Bonus Previews (reply for details)\n")
        for i in bonus_ideas:
            lines.append(f"- **{i['business_name']}** ({i['category']}) — {i['what_it_does'][:120]}...\n")

    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════════════
#  EMAIL SEND
# ═══════════════════════════════════════════════════════════════════════════
def send_email(config, subject, html):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = config["sender_email"]
    msg["To"] = config["recipient_email"]
    msg.attach(MIMEText(html, "html", "utf-8"))
    with smtplib.SMTP(config["smtp_server"], config["smtp_port"]) as s:
        s.ehlo(); s.starttls(); s.ehlo()
        s.login(config["sender_email"], config["sender_password"])
        s.send_message(msg)
    log.info("📧 Email sent to %s", config["recipient_email"])


# ═══════════════════════════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════════════════════════
def main():
    log.info("=" * 60)
    log.info("🚀 Daily Business Ideas Automation — Starting")
    log.info("=" * 60)

    config = load_json(CONFIG_FILE)
    ideas = load_json(IDEAS_FILE)
    history = load_json(HISTORY_FILE) if HISTORY_FILE.exists() else {"sent_ids":[],"log":[],"cycle_count":0}

    total_r = len([i for i in ideas if not i["is_high_risk"]])
    total_hr = len([i for i in ideas if i["is_high_risk"]])
    remaining = total_r - len([s for s in history.get("sent_ids",[]) if any(i["id"]==s and not i["is_high_risk"] for i in ideas)])
    log.info(f"📊 Database: {total_r} regular + {total_hr} high-risk | {remaining} unsent")

    main_count = config.get("ideas_per_day", 5)
    bonus_count = config.get("bonus_preview_count", 3)
    main_ideas, bonus_ideas, high_risk, history = select_ideas(ideas, history, main_count, bonus_count)

    log.info(f"✅ Selected {len(main_ideas)} main + {len(bonus_ideas)} bonus" + (" + 1 high-risk" if high_risk else ""))

    date_str = datetime.now().strftime("%B %d, %Y")

    # Save bonus ideas to pending_details.json for reply_checker
    if bonus_ideas:
        pending = {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "date_display": date_str,
            "ideas": {i["business_name"]: i for i in bonus_ideas},
        }
        save_json(PENDING_FILE, pending)
        log.info(f"💾 {len(bonus_ideas)} bonus ideas saved for reply-on-demand")

    # Save markdown report
    if config.get("save_reports", True):
        rdir = BASE_DIR / config.get("reports_dir", "reports")
        rdir.mkdir(exist_ok=True)
        md = build_markdown(main_ideas, bonus_ideas, high_risk, date_str)
        (rdir / f"daily_ideas_{datetime.now().strftime('%Y-%m-%d')}.md").write_text(md, encoding="utf-8")
        log.info("💾 Report saved")

    # Send email
    html = build_email(main_ideas, bonus_ideas, high_risk, date_str)
    send_email(config, f"🚀 Daily Startup Ideas — {date_str}", html)

    # Update history (main ideas + high-risk marked as sent; bonus stays available)
    for i in main_ideas:
        history["sent_ids"].append(i["id"])
    if high_risk:
        history["sent_ids"].append(high_risk["id"])
    # Bonus ideas also marked sent to avoid showing them as main later
    for i in bonus_ideas:
        history["sent_ids"].append(i["id"])

    history["log"].append({
        "date": datetime.now().strftime("%Y-%m-%d"),
        "main": [i["business_name"] for i in main_ideas],
        "bonus": [i["business_name"] for i in bonus_ideas],
        "high_risk": high_risk["business_name"] if high_risk else None,
    })
    save_json(HISTORY_FILE, history)

    log.info("✅ ALL DONE — Full ideas + bonus previews sent!")
    log.info("=" * 60)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log.error(f"❌ Fatal: {e}", exc_info=True)
        sys.exit(1)
