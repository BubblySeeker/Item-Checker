# Sam's Club Inventory Monitor

Automated system to monitor Sam's Club inventory, track out-of-stock items, and send daily email reports.

## Features

- ✅ Reads item numbers from Excel file
- ✅ Checks stock status via Unwrangle API
- ✅ Tracks how many days items have been out of stock
- ✅ Sends daily email reports with OOS items
- ✅ Runs automatically via GitHub Actions
- ✅ Saves historical tracking data

## Setup

### 1. Install Dependencies

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install requirements
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env
```

Edit `.env`:
```
UNWRANGLE_API_KEY=your_api_key_here
EMAIL_FROM=your-email@gmail.com
EMAIL_TO=recipient-email@gmail.com
EMAIL_PASSWORD=your_gmail_app_password
```

**Gmail Setup:**
1. Go to Google Account → Security
2. Enable 2-Factor Authentication
3. Create an "App Password" for this application
4. Use the app password (not your regular password) in `.env`

### 3. Prepare Your Items File

Ensure `items.xlsx` is in the project root with item numbers in the first column.

### 4. Test Locally

```bash
source venv/bin/activate
python inventory_checker.py
```

## GitHub Actions Setup

### 1. Add Repository Secrets

Go to your GitHub repository → Settings → Secrets and variables → Actions

Add these secrets:
- `UNWRANGLE_API_KEY` - Your Unwrangle API key
- `EMAIL_FROM` - Sender email address
- `EMAIL_TO` - Recipient email address
- `EMAIL_PASSWORD` - Gmail app password
- `SMTP_SERVER` - (Optional) Default: `smtp.gmail.com`
- `SMTP_PORT` - (Optional) Default: `587`

### 2. Enable GitHub Actions

- Go to Actions tab in your repository
- Enable workflows if prompted

### 3. Configure Schedule

The workflow runs **Monday and Thursday at 8:00 AM EST** by default. To change the time, edit `.github/workflows/daily-check.yml`:

```yaml
schedule:
  - cron: '0 13 * * 1,4'  # Change this line
```

Cron syntax: `minute hour day month weekday` (weekday: 0=Sunday, 1=Monday, etc.)
- `0 13 * * 1,4` = 8:00 AM EST on Monday and Thursday (default)
- `0 8 * * 1,4` = 3:00 AM EST on Monday and Thursday
- `0 13 * * *` = 8:00 AM EST daily (every day)
- `0 13 * * 1-5` = 8:00 AM EST weekdays only

**Timezone Note:**
- Times are in UTC (GitHub Actions servers)
- 8:00 AM EST = 1:00 PM UTC (13:00)
- Adjust the hour for your timezone

### 4. Manual Trigger

You can manually run the check:
1. Go to Actions tab
2. Select "Daily Inventory Check"
3. Click "Run workflow"

## Files

- `inventory_checker.py` - Main script
- `items.xlsx` - Input file with item numbers
- `oos_tracking.json` - Persistent OOS tracking data
- `results_*.json` - Timestamped result files
- `.env` - Local configuration (not committed)
- `.github/workflows/daily-check.yml` - GitHub Actions workflow

## How It Works

1. **Load Items**: Reads item numbers from Excel
2. **Check Stock**: Queries Unwrangle API for each item
3. **Track OOS Days**: Maintains a JSON file tracking how long each item has been out of stock
4. **Send Report**: Emails a summary with OOS items and days out of stock
5. **Save Results**: Stores results and updates tracking data

## Output

### Console Output
```
[1/148] Checking item 990361697... ✅ In stock (Qty: 1186)
[2/148] Checking item 990352342... ❌ OOS (3 days)
...

SUMMARY
Total items checked: 148
In stock: 145
Out of stock: 3
```

### Email Report
HTML email with:
- Summary statistics
- Table of OOS items with days out of stock
- Links to product pages

## Troubleshooting

### API Timeouts
The script uses `curl` via subprocess because Python's `requests` library may timeout. Ensure `curl` is installed on your system.

### Email Not Sending
- Verify Gmail app password is correct
- Check 2FA is enabled on Google account
- Ensure "Less secure app access" is NOT needed (use app passwords instead)

### GitHub Actions Failing
- Verify all secrets are set correctly
- Check Actions tab for error logs
- Ensure `items.xlsx` is committed to the repository

## Cost Estimation

**Unwrangle API Credits:**
- 10 credits per item check
- 148 items × 10 credits = 1,480 credits per run
- 2 runs per week = 2,960 credits/week
- **~12,830 credits per month**

**GitHub Actions:** FREE ✅
- Free tier: 2,000 minutes/month (private repos) or unlimited (public repos)
- This workflow uses ~5 minutes per run
- 2 runs/week × 5 min = 10 min/week = ~40 min/month
- Well within free tier limits!

Check your Unwrangle plan for credit allowances.

## License

MIT License - Feel free to modify and use as needed.
