import os
import logging
from flask import Flask, request, jsonify
from supabase import create_client, Client
from engine import check_global_ad_compliance

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

app = Flask(__name__)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Missing SUPABASE_URL or SUPABASE_KEY environment variables.")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

@app.route('/paypal-webhook', methods=['POST'])
def handle_paypal_payment():
    try:
        data = request.json
        if not data:
            return jsonify({"error": "Invalid payload"}), 400

        logger.info(f"Processing payment webhook for product: {data.get('product_title')}")

        compliance = check_global_ad_compliance(
            product_title=data.get('product_title', ''),
            manuscript_text=data.get('manuscript_text', ''),
            destination_url=data.get('destination_url', '')
        )
        
        is_approved = compliance.get('is_approved', False)
        status = "approved" if is_approved else "rejected"
        rejection_reason = compliance.get('reason', 'None')

        logger.info(f"Compliance check completed. Status: {status}")

        vendor_res = supabase.table("mamachi_vendors").upsert(
            {
                "name": data.get('vendor_name'),
                "email": data.get('vendor_email'),
                "status": "active",
                "fee_paid": True
            },
            on_conflict="email"
        ).execute()

        if not vendor_res.data:
            raise Exception("Failed to record or update vendor in database.")

        vendor_id = vendor_res.data[0]['id']

        product_payload = {
            "vendor_id": vendor_id,
            "product_title": data.get("product_title"),
            "destination_url": data.get("destination_url"),
            "manuscript_text": data.get("manuscript_text"),
            "service_category": data.get("service_category", "book_publication"),
            "target_cities": data.get("target_cities", []),
            "target_neighborhoods": data.get("target_neighborhoods", []),
            "billing_model": data.get("billing_model", "hourly"),
            "hourly_limit_usd": data.get("hourly_limit_usd", 3.00),
            "daily_limit_usd": data.get("daily_limit_usd", 15.00),
            "compliance_status": status,
            "rejection_reason": rejection_reason,
            "is_active": is_approved,
            "fee_paid": True
        }

        supabase.table("mamachi_products").insert(product_payload).execute()
        logger.info(f"PayPal payment processed & campaign created successfully! (Active: {is_approved})")

        return jsonify({
            "status": "success",
            "compliance_status": status,
            "message": rejection_reason
        }), 200

    except Exception as e:
        logger.exception("PayPal webhook processing failed: %s", e)
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
