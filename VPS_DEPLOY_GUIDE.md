# 🚀 Deploy to VPS — Quick Guide

## Files to upload

| File | Purpose |
|------|---------|
| `daily_ideas_sender.py` | Phase 1: sends preview email at 6 AM |
| `reply_checker.py` | Phase 2: checks for replies, sends full details |
| `ideas_database.json` | 34 curated business ideas |
| `config.json` | Gmail settings |
| `sent_history.json` | Tracking (will be reset fresh) |
| `setup_vps.sh` | Automated VPS setup |

## Step 1: Upload files

```powershell
scp "C:\Users\yujan\Desktop\Business Automation\daily_ideas_sender.py" root@YOUR_VPS_IP:~/
scp "C:\Users\yujan\Desktop\Business Automation\reply_checker.py" root@YOUR_VPS_IP:~/
scp "C:\Users\yujan\Desktop\Business Automation\ideas_database.json" root@YOUR_VPS_IP:~/
scp "C:\Users\yujan\Desktop\Business Automation\config.json" root@YOUR_VPS_IP:~/
scp "C:\Users\yujan\Desktop\Business Automation\sent_history.json" root@YOUR_VPS_IP:~/
scp "C:\Users\yujan\Desktop\Business Automation\setup_vps.sh" root@YOUR_VPS_IP:~/
```

## Step 2: SSH in and run setup

```bash
ssh root@YOUR_VPS_IP
chmod +x setup_vps.sh && bash setup_vps.sh
```

## That's it! 🎉

### How it works:

1. **6:00 AM** — You get a preview email with 5 idea titles + short descriptions
2. **Reply** with the names you want details on (or type "all")3. **Within 5 minutes** — You get full breakdowns for those ideas

### Useful commands:

```bash
cd ~/business-automation
python3 daily_ideas_sender.py     # Run manually
python3 reply_checker.py          # Check for replies manually
cat automation.log                # View logs
crontab -l                        # Check scheduled jobs
```
