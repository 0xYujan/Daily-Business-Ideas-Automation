#!/bin/bash

# 1. Update & Install Python
echo "🔄 Updating system..."
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3 python3-pip git nano

# 2. Clone Repository
echo "📂 Cloning repository..."
cd ~
if [ -d "daily-business-ideas-automation" ]; then
    echo "   Repo exists, pulling latest..."
    cd daily-business-ideas-automation
    git pull
else
    git clone https://github.com/0xYujan/daily-business-ideas-automation.git
    cd daily-business-ideas-automation
fi

# 3. Setup Config (Placeholder)
if [ ! -f "config.json" ]; then
    echo "⚠️ config.json not found! Creating template..."
    cp config.example.json config.json
    echo "❗ PLEASE EDIT config.json with your actual credentials!"
fi

# 4. Setup Cron Jobs (6:00 AM & 5:00 PM)
echo "⏰ Setting up Cron Jobs..."
REPO_DIR="$HOME/daily-business-ideas-automation"
CRON_CMD="python3 $REPO_DIR/daily_ideas_sender.py >> $REPO_DIR/cron_log.txt 2>&1"

# Check if cron already exists
(crontab -l 2>/dev/null | grep -v "daily_ideas_sender.py") | crontab -

# Add new jobs (Morning 6am, Evening 5pm)
(crontab -l 2>/dev/null; echo "0 6 * * * $CRON_CMD") | crontab -
(crontab -l 2>/dev/null; echo "0 17 * * * $CRON_CMD") | crontab -

echo "✅ Deployment Complete!"
echo "👉 Run 'nano config.json' to add your email password."
echo "👉 Run 'python3 daily_ideas_sender.py' to test immediately."
