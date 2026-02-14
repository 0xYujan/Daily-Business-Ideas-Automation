#!/usr/bin/env python3
"""
Daily Business Ideas — CEO Briefing Sender
Delivers a high-level strategic briefing with 3 actionable ideas + 1 execution task.
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


def select_ideas(ideas, history, count=3):
    sent = set(history.get("sent_ids", []))
    
    available = [i for i in ideas if i["id"] not in sent]
    
    if len(available) < count:
        log.warning("⚠ Cycling database (running low on fresh ideas).")
        history["sent_ids"] = [] # Reset history
        available = ideas

    # Prioritize "priority" ideas (freshly added)
    priority_ideas = [i for i in available if i.get("priority") is True]
    regular_ideas = [i for i in available if i.get("priority") is not True]
    
    selected = []
    
    # 1. Take priority ideas first (randomized within priority group)
    if priority_ideas:
        take = min(count, len(priority_ideas))
        selected.extend(random.sample(priority_ideas, take))
        
    # 2. Fill remaining slots from regular ideas
    remaining_slots = count - len(selected)
    if remaining_slots > 0 and regular_ideas:
        take = min(remaining_slots, len(regular_ideas))
        selected.extend(random.sample(regular_ideas, take))
    
    # Shuffle the final selection so priority ideas aren't always top if mixed
    random.shuffle(selected)
        
    return selected, history


# ═══════════════════════════════════════════════════════════════════════════
#  HTML GENERATOR (CEO BRIEFING STYLE)
# ═══════════════════════════════════════════════════════════════════════════
def render_idea_html(idea):
    # Mapping some JSON fields to the new format if they don't exist exactly
    # We'll use defaults or derived values where necessary
    
    revenue = idea.get('monetization', 'NPR 5 Lakhs/mo') # Placeholder if not specific
    # Extract just the first action plan item for "Execution Task" candidate
    first_action = idea.get('action_plan', ["Research the market"])[0] 
        
    return f"""
    <div style="margin-bottom: 40px; padding: 25px; background: #fff; border: 1px solid #e5e7eb; border-radius: 12px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);">
        <h2 style="margin: 0 0 10px; color: #111827; font-size: 22px; font-weight: 800;">💡 {idea['business_name']}</h2>
        
        <p style="margin: 0 0 20px; color: #4b5563; font-size: 16px; line-height: 1.5;">
            🔹 {idea['what_it_does'].split('.')[0]}. (Simple & Clear)
        </p>
        
        <div style="display: grid; grid-template-columns: 1fr; gap: 15px;">
            <div>
                <strong style="color: #374151; font-size: 13px; text-transform: uppercase; letter-spacing: 0.5px;">🎯 Target Customer</strong>
                <div style="color: #1f2937; margin-top: 4px;">{idea.get('nepal_adaptation', 'Nepali Businesses').split('.')[0]}</div>
            </div>
            
            <div>
                <strong style="color: #374151; font-size: 13px; text-transform: uppercase; letter-spacing: 0.5px;">💰 Revenue Potential</strong>
                <div style="color: #059669; font-weight: 700; margin-top: 4px;">{idea.get('monetization', '').split('.')[0]}</div>
            </div>
            
            <div>
                <strong style="color: #374151; font-size: 13px; text-transform: uppercase; letter-spacing: 0.5px;">🧠 Why Now?</strong>
                <div style="color: #1f2937; margin-top: 4px;">{idea['why_growing'].split('.')[0]}.</div>
            </div>
            
            <div style="background: #f3f4f6; padding: 15px; border-radius: 8px; margin-top: 10px;">
                <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                    <span style="color: #6b7280; font-size: 14px;">⚡ Build Difficulty:</span>
                    <strong style="color: #111827;">3/5 (Medium)</strong>
                </div>
                <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                    <span style="color: #6b7280; font-size: 14px;">💸 Startup Cost:</span>
                    <strong style="color: #111827;">{idea['startup_cost']}</strong>
                </div>
                <div style="display: flex; justify-content: space-between;">
                    <span style="color: #6b7280; font-size: 14px;">🔥 Founder Fit:</span>
                    <strong style="color: #db2777;">9/10 (High)</strong>
                </div>
            </div>
            
             <div style="margin-top: 15px;">
                <strong style="color: #374151; font-size: 13px; text-transform: uppercase; letter-spacing: 0.5px;">🚀 Simple MVP Plan:</strong>
                <ol style="margin: 8px 0 0; padding-left: 20px; color: #4b5563; font-size: 14px; line-height: 1.6;">
                    {''.join(f'<li>{step}</li>' for step in idea.get('action_plan', [])[:4])}
                </ol>
            </div>
        </div>
    </div>
    """

def build_email(ideas, date_str):
    ideas_html = "".join(render_idea_html(i) for i in ideas)
    
    # Pick the best idea (just the first one for now)
    best_idea = ideas[0]
    
    # Pick a random execution task from the best idea's plan or generic
    task = best_idea.get('action_plan', ["Market Research"])[0]
    
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
</head>
<body style="margin:0; padding:0; background:#f9fafb; font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; color: #111827;">

<div style="max-width: 600px; margin: 0 auto; padding: 20px;">
    
    <!-- Header -->
    <div style="text-align: center; padding: 40px 0;">
        <h1 style="margin: 0; font-size: 28px; font-weight: 900; color: #111827; letter-spacing: -0.5px;">🚀 CEO DAILY BRIEFING</h1>
        <p style="margin: 8px 0 0; font-size: 15px; color: #6b7280;">SaaS Opportunities for Nepal • {date_str}</p>
    </div>

    <!-- Ideas Section -->
    {ideas_html}

    <!-- Execution Section (The most important part) -->
    <div style="background: #111827; color: #fff; padding: 30px; border-radius: 12px; margin-top: 40px; box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);">
        <h3 style="margin: 0 0 15px; font-size: 14px; text-transform: uppercase; letter-spacing: 1px; color: #60a5fa;">⭐ Today's Execution Task</h3>
        <p style="margin: 0 0 5px; font-size: 18px; font-weight: 600;">🪜 {task.split(':')[0]}</p>
        <p style="margin: 0; font-size: 14px; color: #9ca3af; line-height: 1.5;">{task}</p>
    </div>

    <!-- Winner Section -->
    <div style="text-align: center; margin-top: 40px; padding: 20px; border: 2px dashed #d1d5db; border-radius: 12px;">
         <h3 style="margin: 0 0 5px; font-size: 14px; text-transform: uppercase; letter-spacing: 1px; color: #059669;">🏆 Best Idea Today</h3>
         <p style="margin: 0; font-size: 20px; font-weight: 800; color: #111827;">{best_idea['business_name']}</p>
         <p style="margin: 8px 0 0; font-size: 14px; color: #6b7280;">High potential for immediate revenue in the Nepali market.</p>
    </div>

    <!-- Footer -->
    <div style="text-align: center; margin-top: 50px; padding-top: 20px; border-top: 1px solid #e5e7eb; color: #9ca3af; font-size: 12px;">
        <p>Generated by your Ultra-Elite Startup Intelligence System</p>
    </div>

</div>

</body>
</html>"""


# ═══════════════════════════════════════════════════════════════════════════
#  EMAIL SEND
# ═══════════════════════════════════════════════════════════════════════════
def send_email(config, subject, html):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = config["sender_email"]
    msg["To"] = config["recipient_email"]
    msg.attach(MIMEText(html, "html", "utf-8"))
    
    try:
        with smtplib.SMTP(config["smtp_server"], config["smtp_port"]) as s:
            s.ehlo()
            s.starttls()
            s.ehlo()
            s.login(config["sender_email"], config["sender_password"])
            s.send_message(msg)
        log.info("📧 Email sent to %s", config["recipient_email"])
    except Exception as e:
        log.error(f"❌ Failed to send email: {e}")
        raise


# ═══════════════════════════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════════════════════════
def main():
    log.info("=" * 60)
    log.info("🚀 CEO Briefing Automation — Starting")
    log.info("=" * 60)

    config = load_json(CONFIG_FILE)
    ideas = load_json(IDEAS_FILE)
    history = load_json(HISTORY_FILE) if HISTORY_FILE.exists() else {"sent_ids":[], "log":[]}

    # Select 3 Ideas
    selected_ideas, history = select_ideas(ideas, history, count=3)
    
    if not selected_ideas:
        log.error("❌ No ideas found to send!")
        return

    log.info(f"✅ Selected 3 ideas: {[i['business_name'] for i in selected_ideas]}")

    date_str = datetime.now().strftime("%B %d, %Y")
    
    # Build Subject
    subject = f"🚀 CEO Briefing: Profitable SaaS Opportunities for Nepal — {date_str}"

    # Build Content
    html = build_email(selected_ideas, date_str)

    # Send
    send_email(config, subject, html)

    # Update History
    for i in selected_ideas:
        history["sent_ids"].append(i["id"])
    
    history["log"].append({
        "date": datetime.now().strftime("%Y-%m-%d"),
        "ideas": [i["business_name"] for i in selected_ideas]
    })
    
    save_json(HISTORY_FILE, history)
    log.info("✅ CEO Briefing Sent Successfully!")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log.error(f"❌ Fatal: {e}", exc_info=True)
        sys.exit(1)
