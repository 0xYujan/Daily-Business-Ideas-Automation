#!/bin/bash
# ============================================
#  Daily Business Ideas — VPS Setup Script
#  Run this ON your Ubuntu VPS after uploading files
# ============================================

set -e

echo "============================================"
echo "  Daily Business Ideas — VPS Setup"
echo "============================================"
echo ""

# ─── 1. Install Python if not present ───
echo "[1/6] Checking Python..."
if command -v python3 &>/dev/null; then
    PYTHON_PATH=$(which python3)
    echo "  ✅ Python3 found: $PYTHON_PATH ($(python3 --version))"
else
    echo "  ⚠ Python3 not found. Installing..."
    sudo apt update && sudo apt install -y python3 python3-pip
    PYTHON_PATH=$(which python3)
    echo "  ✅ Python3 installed: $PYTHON_PATH"
fi

# ─── 2. Create project directory ───
echo ""
echo "[2/6] Setting up project directory..."
PROJECT_DIR="$HOME/business-automation"
mkdir -p "$PROJECT_DIR/reports"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ "$SCRIPT_DIR" != "$PROJECT_DIR" ]; then
    echo "  Copying files to $PROJECT_DIR..."
    cp -f "$SCRIPT_DIR/daily_ideas_sender.py" "$PROJECT_DIR/"
    cp -f "$SCRIPT_DIR/reply_checker.py" "$PROJECT_DIR/"
    cp -f "$SCRIPT_DIR/ideas_database.json" "$PROJECT_DIR/"
    cp -f "$SCRIPT_DIR/config.json" "$PROJECT_DIR/"
    if [ ! -f "$PROJECT_DIR/sent_history.json" ]; then
        cp -f "$SCRIPT_DIR/sent_history.json" "$PROJECT_DIR/"
    fi
fi
echo "  ✅ Project directory: $PROJECT_DIR"

# ─── 3. Set permissions ───
echo ""
echo "[3/6] Setting permissions..."
chmod +x "$PROJECT_DIR/daily_ideas_sender.py"
chmod +x "$PROJECT_DIR/reply_checker.py"
echo "  ✅ Permissions set"

# ─── 4. Set timezone ───
echo ""
echo "[4/6] Setting timezone to Asia/Kathmandu..."
sudo timedatectl set-timezone Asia/Kathmandu
echo "  ✅ Timezone: $(timedatectl show --property=Timezone --value)"

# ─── 5. Test the preview sender ───
echo ""
echo "[5/6] Sending test email..."
cd "$PROJECT_DIR"
python3 daily_ideas_sender.py
if [ $? -eq 0 ]; then
    echo "  ✅ Test email sent — check your inbox!"
else
    echo "  ❌ Test failed. Run: cat $PROJECT_DIR/automation.log"
    exit 1
fi

# ─── 6. Set up cron jobs ───
echo ""
echo "[6/6] Setting up cron jobs..."

# Remove old entries
(crontab -l 2>/dev/null | grep -v "daily_ideas_sender" | grep -v "reply_checker") > /tmp/cron_clean 2>/dev/null || true

# Add new entries:
# - Preview email at 6:00 AM NPT (local time since we set timezone)
# - Reply checker every 5 minutes
echo "0 6 * * * cd $PROJECT_DIR && $PYTHON_PATH daily_ideas_sender.py >> $PROJECT_DIR/cron.log 2>&1" >> /tmp/cron_clean
echo "*/5 * * * * cd $PROJECT_DIR && $PYTHON_PATH reply_checker.py >> $PROJECT_DIR/cron_reply.log 2>&1" >> /tmp/cron_clean

crontab /tmp/cron_clean
rm /tmp/cron_clean

echo "  ✅ Cron jobs installed!"
echo ""

echo "============================================"
echo "  ✅ SETUP COMPLETE!"
echo "============================================"
echo ""
echo "  📁 Project:     $PROJECT_DIR"
echo "  ⏰ Preview:     Every day at 6:00 AM NPT"
echo "  🔄 Reply check: Every 5 minutes"
echo "  📧 Sending to:  $(python3 -c "import json; print(json.load(open('$PROJECT_DIR/config.json'))['recipient_email'])")"
echo ""
echo "  HOW IT WORKS:"
echo "  ──────────────────────────────────────────"
echo "  1. You receive a preview email at 6 AM"
echo "     with idea titles + short descriptions"
echo "  2. Reply with the names you want details on"
echo "     (or reply 'all' for everything)"
echo "  3. Within 5 minutes, you get full breakdowns!"
echo ""
echo "  USEFUL COMMANDS:"
echo "  ──────────────────────────────────────────"
echo "  Run preview:   cd $PROJECT_DIR && python3 daily_ideas_sender.py"
echo "  Check replies: cd $PROJECT_DIR && python3 reply_checker.py"
echo "  View logs:     cat $PROJECT_DIR/automation.log"
echo "  Check cron:    crontab -l"
echo ""
