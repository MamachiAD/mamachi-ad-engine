import os
import logging
from datetime import datetime, timezone, timedelta
from supabase import create_client, Client
import requests

# -----------------------------------------------------------------------------
# Logging & Environment Setup
# -----------------------------------------------------------------------------
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")
RESEND_API_KEY = os.environ.get("RESEND_API_KEY", "") # Or SendGrid API key

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def send_performance_email(vendor_email: str, vendor_name: str, product_title: str, stats: dict):
    """Sends a weekly/hourly performance breakdown report to the advertiser."""
    if not RESEND_API_KEY:
        logger.warning("RESEND_API_KEY missing. Skipping email delivery to %s", vendor_email)
        return

    html_content = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #e2e8f0; border-radius: 12px; background-color: #f8fafc;">
        <h2 style="color: #0284c7; text-align: center;">Mamachi Ad Engine Report</h2>
        <p>Hello <b>{vendor_name}</b>,</p>
        <p>Here is your latest performance update for your active campaign: <b>{product_title}</b></p>
        
        <table style="width: 100%; border-collapse: collapse; margin: 20px 0; background: #ffffff; border-radius: 8px; overflow: hidden;">
            <tr style="background: #0284c7; color: white;">
                <th style="padding: 12px; text-align: left;">Metric</th>
                <th style="padding: 12px; text-align: right;">Value</th>
            </tr>
            <tr style="border-bottom: 1px solid #e2e8f0;">
                <td style="padding: 12px;">Total Posts Published</td>
                <td style="padding: 12px; text-align: right; font-weight: bold;">{stats.get('total_posts', 0)}</td>
            </tr>
            <tr style="border-bottom: 1px solid #e2e8f0;">
                <td style="padding: 12px;">Short Link Clicks</td>
                <td style="padding: 12px; text-align: right; font-weight: bold; color: #16a34a;">{stats.get('total_clicks', 0)}</td>
            </tr>
            <tr style="border-bottom: 1px solid #e2e8f0;">
                <td style="padding: 12px;">Billing Model</td>
                <td style="padding: 12px; text-align: right; font-weight: bold; text-transform: uppercase;">{stats.get('billing_model', 'N/A')}</td>
            </tr>
        </table>
        
        <p style="text-align: center; color: #64748b; font-size: 12px;">Thank you for advertising with Mamachi Ad Engine.</p>
    </div>
    """

    payload = {
        "from": "Mamachi Ad Reports <reports@mamachi.io>",
        "to": [vendor_email],
        "subject": f"📊 Performance Report: {product_title}",
        "html": html_content
    }

    try:
        response = requests.post(
            "https://api.resend.com/emails",
            json=payload,
            headers={"Authorization": f"Bearer {RESEND_API_KEY}", "Content-Type": "application/json"},
            timeout=10
        )
        if response.status_code in (200, 201):
            logger.info("Successfully sent performance report to %s", vendor_email)
        else:
            logger.warning("Failed to send email via Resend (%s): %s", response.status_code, response.text)
    except Exception as e:
      logger.warning("Email dispatch exception: %s", e)


def generate_and_deliver_reports():
    """Queries all active products, aggregates campaign logs, and sends reports."""
    logger.info("Starting automated campaign performance report generation...")

    # Fetch active campaigns with vendor details joined
    products = supabase.table("mamachi_products").select("*, mamachi_vendors(name, email)").eq("is_active", True).execute().data or []

    for prod in products:
        product_id = prod.get("product_id")
        title = prod.get("product_title")
        vendor = prod.get("mamachi_vendors") or {}
        email = vendor.get("email")
        name = vendor.get("name", "Advertiser")

        if not email:
            continue

        # Fetch logs for this product
        logs = supabase.table("mamachi_campaign_logs").select("*").eq("product_id", product_id).execute().data or []

        total_posts = len(logs)
        total_clicks = sum(log.get("clicks_count", 0) for log in logs)

        stats = {
            "total_posts": total_posts,
            "total_clicks": total_clicks,
            "billing_model": prod.get("billing_model", "hourly")
        }

        logger.info("Reporting for '%s' (%s): %d posts, %d clicks", title, email, total_posts, total_clicks)
        send_performance_email(email, name, title, stats)

    logger.info("All performance reports processed.")

if __name__ == "__main__":
    generate_and_deliver_reports()
