# ✅ System Ready: Twice-Weekly Inventory Monitoring

## What You Get

### 📧 Email Reports
**When:** Every **Monday and Thursday morning at 8 AM UTC**
- 3 AM EST
- 12 AM (midnight) PST

**What's Included:**
1. **Summary Stats**
   - Total items monitored (148)
   - Number in stock
   - Number out of stock

2. **Out of Stock Items Table**
   - Item number
   - Product name
   - Stock status: "OUT OF STOCK" (red)
   - Quantity: 0
   - Days out of stock
   - Link to product page

3. **In Stock Items Sample (First 10)**
   - Item number
   - Product name
   - Stock status: "IN STOCK" (green)
   - Current quantity available

## 💰 Cost Breakdown

### Completely FREE! ✅

| Service | Cost | Usage |
|---------|------|-------|
| **GitHub Actions** | $0 | 2 runs/week = ~40 min/month (free tier: 2,000 min/month) |
| **Unwrangle API** | Pay per credit | 2,960 credits/week (~12,830/month) |
| **Email (Gmail)** | $0 | Unlimited |

**API Credits Saved:**
- Daily runs: 10,360 credits/week
- Twice-weekly: 2,960 credits/week
- **Savings: 71% fewer API calls!**

## 🚀 How to Deploy

### 1. Local Setup (5 minutes)

```bash
# Clone/navigate to repo
cd Item-Checker

# Set up environment
cp .env.example .env
nano .env  # Add your email credentials

# Test locally
source venv/bin/activate
python inventory_checker.py
```

### 2. GitHub Setup (5 minutes)

```bash
# Push to GitHub
git add .
git commit -m "Set up inventory monitoring system"
git push origin main

# Add secrets in GitHub:
# Settings → Secrets and variables → Actions
```

**Required Secrets:**
- `UNWRANGLE_API_KEY` = `80bb7e3325d434ecd2092bba2f72b8be86dab1ee`
- `EMAIL_FROM` = Your Gmail address
- `EMAIL_TO` = Recipient email
- `EMAIL_PASSWORD` = Gmail App Password

**Optional Secrets:**
- `SMTP_SERVER` = `smtp.gmail.com` (default)
- `SMTP_PORT` = `587` (default)

### 3. Done! ✨

The system will automatically:
- Run every Monday at 8 AM UTC
- Run every Thursday at 8 AM UTC
- Email you the results
- Track OOS days across runs
- Save results as GitHub artifacts

## 📱 Gmail App Password Setup

1. Go to https://myaccount.google.com/
2. Security → 2-Step Verification (enable if not enabled)
3. Security → App passwords
4. Create new app password for "Mail"
5. Copy the 16-character password
6. Use this in your `.env` file and GitHub secrets

## 🎯 What Happens on Each Run

```
Monday 8 AM UTC:
  ✅ Check all 148 items
  ✅ Update OOS tracking
  ✅ Email report sent
  ✅ Results saved

Thursday 8 AM UTC:
  ✅ Check all 148 items (uses Monday's tracking data)
  ✅ Update OOS days (now shows "4 days" if item was OOS Monday)
  ✅ Email report sent
  ✅ Results saved
```

## 📊 Email Sample

```
=================================
Sam's Club Inventory Report
Date: February 10, 2026 at 8:00 AM
=================================

SUMMARY
Total Items: 148
In Stock: 145
Out of Stock: 3

OUT OF STOCK ITEMS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Item #      | Product Name             | Status        | Qty | Days OOS
990352342   | Perfume ABC              | OUT OF STOCK  | 0   | 7
990409970   | Fragrance XYZ            | OUT OF STOCK  | 0   | 3
...

IN STOCK ITEMS (First 10)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Item #      | Product Name                            | Status   | Qty
990361697   | Ariana Grande Cloud Eau de Parfum       | IN STOCK | 1186
990333741   | Ariana Grande Sweet Like Candy          | IN STOCK | 79
...

...and 135 more in-stock items
```

## 🛠️ Customization

### Change Run Time
Edit `.github/workflows/daily-check.yml`:
```yaml
- cron: '0 8 * * 1,4'  # Hour 8 = 8 AM UTC
```

### Change Days
```yaml
- cron: '0 8 * * 1,3,5'  # Monday, Wednesday, Friday
- cron: '0 8 * * *'      # Every day
```

### Change Recipient
Update `.env` or GitHub secret:
```
EMAIL_TO=different-email@example.com
```

## ❓ Troubleshooting

**Email not sending?**
- Verify Gmail App Password is correct
- Check 2FA is enabled
- Test locally first: `python inventory_checker.py`

**GitHub Actions not running?**
- Verify all secrets are set
- Check Actions tab for error logs
- Manually trigger: Actions → Twice Weekly Inventory Check → Run workflow

**API timeouts?**
- Normal - some items may fail intermittently
- Results are still saved for successful items
- Failed items will be retried on next run

## 📞 Support

- Issues: https://github.com/anthropics/claude-code/issues
- Unwrangle Support: console.unwrangle.com
- Gmail Help: https://support.google.com/accounts

---

**You're all set!** 🎉

Push to GitHub and your first report will arrive next Monday or Thursday morning!
