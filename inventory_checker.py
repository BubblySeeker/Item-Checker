"""
Sam's Club Inventory Monitor
Checks stock status of items from Excel file and sends email reports.
"""

import pandas as pd
import json
import subprocess
from datetime import datetime
from pathlib import Path
import os
from dotenv import load_dotenv
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Load environment variables
load_dotenv()

# Configuration
API_KEY = os.getenv('UNWRANGLE_API_KEY', '80bb7e3325d434ecd2092bba2f72b8be86dab1ee')
EXCEL_FILE = 'items.xlsx'
TRACKING_FILE = 'oos_tracking.json'
EMAIL_FROM = os.getenv('EMAIL_FROM')
EMAIL_TO = os.getenv('EMAIL_TO')
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')
SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
SMTP_PORT = int(os.getenv('SMTP_PORT') or '465')


def load_items():
    """Load item numbers from Excel file."""
    print("Loading items from Excel...")
    df = pd.read_excel(EXCEL_FILE, skiprows=1)
    item_column = df.iloc[:, 0]
    items = item_column.dropna()
    items = items[items != 'Item Number']
    item_list = [str(int(float(x))) for x in items if pd.notna(x)]
    print(f"✅ Loaded {len(item_list)} items")
    return item_list


def load_tracking_data():
    """Load OOS tracking data from JSON file."""
    if Path(TRACKING_FILE).exists():
        with open(TRACKING_FILE, 'r') as f:
            return json.load(f)
    return {}


def save_tracking_data(data):
    """Save OOS tracking data to JSON file."""
    with open(TRACKING_FILE, 'w') as f:
        json.dump(data, f, indent=2)


def check_item_stock(item_number, max_retries=3):
    """
    Check stock status for a single item using Unwrangle API via curl.
    Includes retry logic for better reliability.
    Returns dict with item info or None if error.
    """
    import time

    url = f"https://data.unwrangle.com/api/getter/?platform=samsclub_search&search={item_number}&page=1&api_key={API_KEY}"

    for attempt in range(max_retries):
        try:
            # Balanced timeout for reliability
            result = subprocess.run(
                ['curl', '--max-time', '30', '-s', url],
                capture_output=True,
                text=True,
                timeout=35
            )

            if result.returncode == 0 and result.stdout:
                data = json.loads(result.stdout)

                if data.get('success') and data.get('results'):
                    # Get first result
                    product = data['results'][0]

                    return {
                        'item_number': item_number,
                        'product_id': product.get('id'),
                        'name': product.get('name'),
                        'brand': product.get('brand'),
                        'in_stock': product.get('in_stock', False),
                        'quantity': product.get('quantity', 0),
                        'price': product.get('price'),
                        'url': product.get('url'),
                        'checked_at': datetime.now().isoformat(),
                        'attempts': attempt + 1
                    }
                elif data.get('success') and data.get('result_count') == 0:
                    # Item not found in search results
                    return {
                        'item_number': item_number,
                        'name': 'Unknown',
                        'error': 'Item not found in search',
                        'in_stock': False,
                        'checked_at': datetime.now().isoformat(),
                        'attempts': attempt + 1
                    }

        except subprocess.TimeoutExpired:
            if attempt < max_retries - 1:
                print(f"⏱️  Timeout, retry {attempt + 2}/{max_retries}...", end=' ')
                time.sleep(2)  # Wait 2 seconds before retry
                continue
            else:
                return {
                    'item_number': item_number,
                    'name': 'Unknown',
                    'error': 'Timeout after retries',
                    'in_stock': False,
                    'checked_at': datetime.now().isoformat(),
                    'attempts': max_retries
                }

        except Exception as e:
            if attempt < max_retries - 1:
                print(f"⚠️  Error, retry {attempt + 2}/{max_retries}...", end=' ')
                time.sleep(2)
                continue
            else:
                return {
                    'item_number': item_number,
                    'name': 'Unknown',
                    'error': str(e),
                    'in_stock': False,
                    'checked_at': datetime.now().isoformat(),
                    'attempts': max_retries
                }

    return None


def update_oos_tracking(tracking_data, item_info):
    """Update OOS tracking with current item status."""
    item_number = item_info['item_number']
    today = datetime.now().date().isoformat()

    if item_number not in tracking_data:
        tracking_data[item_number] = {
            'name': item_info.get('name', 'Unknown'),
            'oos_since': None,
            'days_oos': 0,
            'last_in_stock': today if item_info['in_stock'] else None,
            'history': []
        }

    item_tracking = tracking_data[item_number]

    # Update name if available
    if item_info.get('name'):
        item_tracking['name'] = item_info['name']

    # Update stock status
    if not item_info['in_stock']:
        # Item is out of stock
        if item_tracking['oos_since'] is None:
            # Just went out of stock
            item_tracking['oos_since'] = today
            item_tracking['days_oos'] = 1
        else:
            # Calculate days OOS
            oos_since = datetime.fromisoformat(item_tracking['oos_since']).date()
            days = (datetime.now().date() - oos_since).days
            item_tracking['days_oos'] = days
    else:
        # Item is in stock
        if item_tracking['oos_since'] is not None:
            # Item came back in stock
            item_tracking['oos_since'] = None
            item_tracking['days_oos'] = 0
        item_tracking['last_in_stock'] = today

    # Add to history
    item_tracking['history'].append({
        'date': today,
        'in_stock': item_info['in_stock'],
        'quantity': item_info.get('quantity', 0)
    })

    # Keep only last 30 days of history
    if len(item_tracking['history']) > 30:
        item_tracking['history'] = item_tracking['history'][-30:]

    return tracking_data


def send_email_report(oos_items, in_stock_items, failed_items, not_found_items, total_items):
    """Send email report with OOS items, in-stock items, failed items, and not found items."""
    if not EMAIL_FROM or not EMAIL_TO or not EMAIL_PASSWORD:
        print("⚠️  Email not configured. Skipping email report.")
        print("Set EMAIL_FROM, EMAIL_TO, and EMAIL_PASSWORD in .env file")
        return

    subject = f"Sam's Club Stock Checker - {datetime.now().strftime('%Y-%m-%d')}"

    # Build HTML email body
    html = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; }}
            table {{ border-collapse: collapse; width: 100%; margin: 10px 0; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            th {{ background-color: #4CAF50; color: white; }}
            tr:nth-child(even) {{ background-color: #f2f2f2; }}
            .summary {{ margin: 20px 0; padding: 10px; background-color: #f0f0f0; }}
            .warning {{ background-color: #fff3cd; }}
        </style>
    </head>
    <body>
        <h2>Sam's Club Stock Checker</h2>
        <p>Date: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</p>

        <div class="summary">
            <h3>Summary</h3>
            <p>Total Items Monitored: <strong>{total_items}</strong></p>
            <p>In Stock: <strong style="color: green;">{len(in_stock_items)}</strong></p>
            <p>Out of Stock: <strong style="color: red;">{len(oos_items)}</strong></p>
            <p>Not Found on Website: <strong style="color: orange;">{len(not_found_items)}</strong></p>
            <p>Failed to Check: <strong style="color: #dc3545;">{len(failed_items)}</strong></p>
        </div>

        <h3>Out of Stock Items ({len(oos_items)})</h3>
    """

    if oos_items:
        html += """
        <table>
            <tr>
                <th>Item #</th>
                <th>Product Name</th>
                <th>Stock Status</th>
                <th>Quantity</th>
                <th>Days OOS</th>
                <th>URL</th>
            </tr>
        """

        for item in oos_items:
            html += f"""
            <tr>
                <td>{item.get('item_number', 'N/A')}</td>
                <td>{item.get('name', 'Unknown')}</td>
                <td style="color: red; font-weight: bold;">OUT OF STOCK</td>
                <td>0</td>
                <td>{item.get('days_oos', 0)}</td>
                <td><a href="{item.get('url', '#')}">View</a></td>
            </tr>
            """

        html += "</table>"
    else:
        html += "<p>🎉 All items are in stock!</p>"

    # Show items not found on website
    if not_found_items:
        html += f"""
        <br>
        <h3>Items Not Found on Website ({len(not_found_items)})</h3>
        <p style="color: #856404; background-color: #fff3cd; padding: 10px; border-radius: 5px;">
            <strong>Note:</strong> These items could not be found on Sam's Club website. They may be discontinued, delisted, or have incorrect item numbers.
        </p>
        <table>
            <tr>
                <th>Item #</th>
                <th>Status</th>
            </tr>
        """

        for item_num in sorted(not_found_items):
            html += f"""
            <tr class="warning">
                <td>{item_num}</td>
                <td style="color: orange; font-weight: bold;">NOT FOUND ON WEBSITE</td>
            </tr>
            """

        html += "</table>"

    # Show all IN STOCK items
    if in_stock_items:
        html += f"""
        <br>
        <h3>In Stock Items ({len(in_stock_items)})</h3>
        <table>
            <tr>
                <th>Item #</th>
                <th>Product Name</th>
                <th>Stock Status</th>
                <th>Quantity</th>
            </tr>
        """

        for item in in_stock_items:
            html += f"""
            <tr>
                <td>{item.get('item_number', 'N/A')}</td>
                <td>{item.get('name', 'Unknown')}</td>
                <td style="color: green; font-weight: bold;">IN STOCK</td>
                <td>{item.get('quantity', 'N/A')}</td>
            </tr>
            """

        html += "</table>"

    # Show failed items
    if failed_items:
        html += """
        <br>
        <h3 style="color: #ff6b6b;">Failed to Check (Will Retry Next Run)</h3>
        <table>
            <tr>
                <th>Item #</th>
                <th>Product Name</th>
                <th>Reason</th>
            </tr>
        """

        for item in failed_items:
            html += f"""
            <tr>
                <td>{item.get('item_number', 'N/A')}</td>
                <td>{item.get('name', 'Unknown')}</td>
                <td style="color: #ff6b6b;">{item.get('error', 'Check failed')}</td>
            </tr>
            """

        html += "</table>"

    html += """
        <br>
        <p style="color: #888; font-size: 12px;">
            Generated by Sam's Club Inventory Monitor<br>
            Runs automatically Monday and Thursday at 8:00 AM EST
        </p>
    </body>
    </html>
    """

    # Create message
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = EMAIL_FROM
    msg['To'] = EMAIL_TO

    # Attach HTML
    html_part = MIMEText(html, 'html')
    msg.attach(html_part)

    SMTP_SERVER = "smtp.gmail.com"
    
    # Send email
    try:
        print(f"\n📧 Sending email report to {EMAIL_TO}...")
        with smtplib.SMTP(SMTP_SERVER, 587) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(EMAIL_FROM, EMAIL_PASSWORD)
            server.send_message(msg)
        print("✅ Email sent successfully!")
    except Exception as e:
        print(f"❌ Failed to send email: {e}")


def main():
    """Main execution function."""
    print("=" * 70)
    print("Sam's Club Inventory Monitor")
    print("=" * 70)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %I:%M:%S %p')}\n")

    # Load items and tracking data
    items = load_items()
    tracking_data = load_tracking_data()

    # Check each item
    results = []
    oos_items = []
    failed_items = []

    def check_and_update(item_number, index, total, pass_name=""):
        """Helper function to check an item and update tracking. Returns (success, item_info)."""
        print(f"[{index}/{total}] {pass_name}Checking item {item_number}...", end=' ', flush=True)

        item_info = check_item_stock(item_number)

        if item_info and not item_info.get('error'):
            # Successfully checked
            nonlocal tracking_data
            tracking_data = update_oos_tracking(tracking_data, item_info)
            results.append(item_info)

            if not item_info['in_stock']:
                oos_items.append({
                    **item_info,
                    'days_oos': tracking_data[item_number]['days_oos'],
                    'oos_since': tracking_data[item_number]['oos_since']
                })
                print(f"❌ OOS ({tracking_data[item_number]['days_oos']} days)")
            else:
                qty = item_info.get('quantity', 'Unknown')
                print(f"✅ In stock (Qty: {qty})")
            return True, item_info
        else:
            # Failed to check
            error_msg = item_info.get('error', 'No response') if item_info else 'No response'
            if error_msg == 'Item not found in search':
                print("❌ Item not found (discontinued/no page)")
            else:
                print(f"⚠️  Failed to check - {error_msg}")
            return False, item_info

    # Initial pass through all items
    for i, item_number in enumerate(items, 1):
        success, item_info = check_and_update(item_number, i, len(items))

        if not success:
            error_msg = item_info.get('error', 'No response') if item_info else 'No response'

            # Only add to retry list if it's not a "item not found" error
            # Items not found = discontinued/no page, no point retrying
            if error_msg != 'Item not found in search':
                failed_items.append({
                    'item_number': item_number,
                    'name': item_info.get('name', 'Unknown') if item_info else 'Unknown',
                    'error': error_msg
                })

        # Small delay between requests to avoid rate limiting
        if i < len(items):
            import time
            time.sleep(1)

    # Retry failed items - First retry pass
    if failed_items:
        print(f"\n{'=' * 70}")
        print(f"RETRY PASS 1: Retrying {len(failed_items)} failed items...")
        print(f"{'=' * 70}\n")

        first_retry_failed = []
        for i, failed_item in enumerate(failed_items, 1):
            item_number = failed_item['item_number']
            success, item_info = check_and_update(item_number, i, len(failed_items), "RETRY 1 - ")

            if not success:
                # Update error message in case it changed
                error_msg = item_info.get('error', 'No response') if item_info else 'No response'
                # Only keep in retry list if it's not a "item not found" error
                if error_msg != 'Item not found in search':
                    first_retry_failed.append({
                        'item_number': item_number,
                        'name': item_info.get('name', 'Unknown') if item_info else 'Unknown',
                        'error': error_msg
                    })

            # Small delay between requests
            if i < len(failed_items):
                import time
                time.sleep(1)

        # Update failed_items list
        failed_items = first_retry_failed

    # Retry failed items - Second retry pass
    if failed_items:
        print(f"\n{'=' * 70}")
        print(f"RETRY PASS 2: Retrying {len(failed_items)} still-failed items...")
        print(f"{'=' * 70}\n")

        second_retry_failed = []
        for i, failed_item in enumerate(failed_items, 1):
            item_number = failed_item['item_number']
            success, item_info = check_and_update(item_number, i, len(failed_items), "RETRY 2 - ")

            if not success:
                # Update error message in case it changed
                error_msg = item_info.get('error', 'No response') if item_info else 'No response'
                # Only keep in final failed list if it's not a "item not found" error
                if error_msg != 'Item not found in search':
                    second_retry_failed.append({
                        'item_number': item_number,
                        'name': item_info.get('name', 'Unknown') if item_info else 'Unknown',
                        'error': error_msg
                    })

            # Small delay between requests
            if i < len(failed_items):
                import time
                time.sleep(1)

        # Final failed items list
        failed_items = second_retry_failed

    # Save tracking data
    save_tracking_data(tracking_data)
    print(f"\n✅ Tracking data saved to {TRACKING_FILE}")

    # Save results
    results_file = f"results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"✅ Results saved to {results_file}")

    # Print summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Total items: {len(items)}")
    print(f"Successfully checked: {len(results)}")
    print(f"In stock: {len(results) - len(oos_items)}")
    print(f"Out of stock: {len(oos_items)}")
    print(f"Failed to check: {len(failed_items)}")

    if oos_items:
        print("\nOut of Stock Items:")
        for item in sorted(oos_items, key=lambda x: x['days_oos'], reverse=True):
            print(f"  • {item['item_number']} - {item.get('name', 'Unknown')} ({item['days_oos']} days OOS)")

    if failed_items:
        print("\nFailed to Check:")
        for item in failed_items:
            print(f"  • {item['item_number']} - {item['name']} - {item['error']}")

    # Get in-stock items
    in_stock_items = [r for r in results if r.get('in_stock', False)]

    # Find items not found on website (items in Excel but not in results)
    checked_item_numbers = set(r['item_number'] for r in results)
    excel_item_numbers = set(items)
    not_found_items = sorted(excel_item_numbers - checked_item_numbers)

    # Send email report
    send_email_report(oos_items, in_stock_items, failed_items, not_found_items, len(items))

    print("\n" + "=" * 70)
    print(f"Completed at: {datetime.now().strftime('%Y-%m-%d %I:%M:%S %p')}")
    print("=" * 70)


if __name__ == "__main__":
    main()
