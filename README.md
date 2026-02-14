# 🚀 Daily CEO Briefing Automation

A fully automated system that delivers a high-impact **CEO Briefing** to your inbox twice daily. 

It curates specific, actionable SaaS and AI business opportunities tailored for the **Nepali market**, helping you stay ahead of global trends like **Agentic AI** and **Vertical SaaS**.

---

## ✨ Key Features

- **📅 Twice Daily Briefings**: Automatically scheduled for **6:00 AM** (Morning Kickoff) and **5:00 PM** (Evening Review).
- **🧠 Fresh Ideas Engine**: 
  - Prioritizes high-growth trends (e.g., *SarakariSaathi AI*, *GymMate Nepal*).
  - Uses a "Priority Queue" to ensure you see the newest ideas first.
- **📊 CEO-Ready Format**:
  - **No Fluff**: Direct "Target Customer", "Revenue Potential", and "Why Now?" analysis.
  - **Execution Focused**: Includes a specific "Today's Execution Task" to start building immediately.
  - **Visuals**: Clean, modern HTML email design.
- **⚡ Zero API Cost**: Runs locally on your machine using Python + standard libraries.

---

## 🛠️ Setup & Usage

### 1. Requirements
- Windows OS (Task Scheduler is pre-configured).
- Python 3.x installed.
- A Gmail account with an **App Password** (for SMTP).

### 2. Configuration
Create a `config.json` file in the root directory:
```json
{
  "sender_email": "your-email@gmail.com",
  "sender_password": "your-app-password",
  "recipient_email": "recipient@example.com",
  "smtp_server": "smtp.gmail.com",
  "smtp_port": 587
}
```

### 3. Adding Fresh Ideas
To inject new ideas into the system:
1. Edit `fresh_ideas.json` with your new concepts.
2. Run the update script:
   ```bash
   python update_database.py
   ```
   *This automatically merges them into the main database and marks them as **Priority**.*

### 4. Scheduler
The system is integrated with **Windows Task Scheduler**:
- **Task 1**: `DailyBusinessIdeas_Morning` (Trigger: 6:00 AM)
- **Task 2**: `DailyBusinessIdeas_Evening` (Trigger: 5:00 PM)

To verify status:
```powershell
schtasks /Query /TN "DailyBusinessIdeas_Morning"
schtasks /Query /TN "DailyBusinessIdeas_Evening"
```

---

### 5. Deploy to VPS (Linux)
If you want to run this 24/7 on a cloud server (DigitalOcean, AWS, Linode):

1. **Copy Files**:
   ```bash
   scp setup_vps.sh config.json root@YOUR_VPS_IP:~/
   ```
2. **Run Setup**:
   ```bash
   ssh root@YOUR_VPS_IP
   chmod +x setup_vps.sh
   ./setup_vps.sh
   ```
   *This script installs Python, clones the repo, and sets up the 6AM/5PM cron jobs automatically.*

- `daily_ideas_sender.py`: Main logic for selecting ideas and sending the email.
- `update_database.py`: Utility to merge new ideas from `fresh_ideas.json`.
- `ideas_database.json`: The core database covering 40+ validated business ideas.
- `config.json`: (Ignored by Git) Stores your sensitive credentials.

---

## 📜 License
Private & Confidential. Built for High-Performance Execution.
