# Daily Business Ideas Automation 🚀

A self-hosted automation system that delivers curated, high-quality business ideas to your inbox daily—specifically adapted for Nepal.

## Features

- **Daily Email (6:00 AM):** Sends 5 fresh ideas + 1 high-risk/high-reward bonus.
- **Bonus Previews:** Includes 3 extra "preview" ideas at the bottom of each email.
- **Reply-to-Reveal:** Reply to the email with the name of a bonus idea (or "all"), and the system automatically sends you the full detailed breakdown within 5 minutes.
- **Smart Tracking:** Remembers what it sent you to avoid repeats until the entire database is cycled.
- **Zero API Costs:** Runs on simple Python scripts with a local JSON database.

## Setup

### 1. Requirements
- A VPS or local server (tested on Ubuntu 20.04+)
- Python 3.8+
- A Gmail account with an **App Password** (for SMTP)

### 2. Configuration
Copy the example config and add your credentials:
```bash
cp config.example.json config.json
nano config.json
```
*Note: `config.json` is git-ignored to protect your secrets.*

### 3. Deploy to VPS
Use the included setup script:
```bash
# Upload files to your server
scp daily_ideas_sender.py reply_checker.py ideas_database.json config.json setup_vps.sh root@YOUR_IP:~/

# SSH in and run setup
ssh root@YOUR_IP
chmod +x setup_vps.sh
bash setup_vps.sh
```

### 4. How to Add Ideas
Edit `ideas_database.json` to add new business concepts. The system will automatically pick them up.

## License
MIT License
