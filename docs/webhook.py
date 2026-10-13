import os
import logging
from flask import Flask, request, jsonify
from supabase import create_client, Client
import stripe

# -----------------------------------------------------------------------------
# Logging & Environment Setup
# -----------------------------------------------------------------------------
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

app = Flask(__name__)

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")
STRIPE_SECRET_KEY = os.environ.get("STRIPE_SECRET_KEY", "")
STRIPE_WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET", "")
FRONTEND_URL = os.environ.get("FRONTEND_URL", "https://mamachi.io") # Your GitHub Pages URL or domain

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
stripe.api_key = STRIPE_SECRET_KEY

# Pricing mappings (in cents for Stripe)
PRICE_MAPPING = {
    "hourly": {"amount": 199, "name": "Flash Hourly Ad Burst"},
    "daily": {"amount": 1299, "name": "Daily Ad Surge"},
    "monthly": {"amount": 14900, "name": "Monthly Powerhouse Subscription"}
}

@app.route("/create-checkout-session", methods=["POST"])
def create_checkout_session():
    """Receives campaign data from advertise.html and creates a secure Stripe Checkout Session."""
    try:
        data = request.json
        billing_model = data.get("billing_model", "hourly")
        pricing = PRICE_MAPPING.get(billing_model, PRICE_MAPPING["hourly"])

        # First, insert the campaign into Supabase as inactive (pending payment)
        vendor_res = supabase.table("mamachi_vendors").insert({
            "name": data.get("vendor_name"),
            "email": data.get("vendor_email"),
            "status": "pending",
            "fee_paid": False
        }).execute()

        vendor_id = vendor_res.data[0]["id"] if vendor_res.data else None

        product_payload = {
            "vendor_id": vendor_id,
            "product_title": data.get("product_title"),
            "destination_url": data.get("destination_url"),
            "manuscript_text": data.get("manuscript_text"),
            "target_cities": data.get("target_cities"),
            "target_neighborhoods": data.get("target_neighborhoods"),
            "billing_model": billing_model,
            "hourly_limit_usd": data.get("hourly_limit_usd"),
            "daily_limit_usd": data.get("daily_limit_usd"),
            "is_active": False,
            "fee_paid": False
        }
        
        prod_res = supabase.table("mamachi_products").insert(product_payload).execute()
        product_id = prod_res.data[0]["product_id"] if prod_res.data else None

        # Create Stripe Checkout Session
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'unit_amount': pricing["amount"],
                    'product_data': {
                        'name': pricing["name"],
                        'description': f"Campaign: {data.get('product_title')}"
                    },
                },
                'quantity': 1,
            }],
            mode='payment' if billing_model in ['hourly', 'daily'] else 'subscription',
            success_url=f"{FRONTEND_URL}/success.html?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{FRONTEND_URL}/advertise.html",
            metadata={
                "product_id": product_id,
                "vendor_id": vendor_id
            }
        )

        return jsonify({"url": checkout_session.url})

    except Exception as e:
        logger.exception("Failed to create checkout session: %s", e)
        return jsonify({"error": str(e)}), 500


@app.route("/stripe-webhook", methods=["POST"])
def stripe_webhook():
    """Listens for Stripe payment confirmations and activates the ad campaign in Supabase."""
    payload = request.data
    sig_header = request.headers.get('Stripe-Signature')
    event = None

    try:
        if STRIPE_WEBHOOK_SECRET:
            event = stripe.Webhook.construct_event(payload, sig_header, STRIPE_WEBHOOK_SECRET)
        else:
            event = request.json
    except Exception as e:
        logger.warning("Webhook signature verification failed: %s", e)
        return jsonify({"error": str(e)}), 400

    # Handle successful payment
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        metadata = session.get('metadata', {})
        product_id = metadata.get('product_id')
        vendor_id = metadata.get('vendor_id')

        if product_id and vendor_id:
            logger.info("Payment confirmed for product_id: %s. Activating campaign...", product_id)
            
            # Activate Product Campaign
            supabase.table("mamachi_products").update({
                "is_active": True,
                "fee_paid": True
            }).eq("product_id", product_id).execute()

            # Activate Vendor Account
            supabase.table("mamachi_vendors").update({
                "status": "active",
                "fee_paid": True
            }).eq("id", vendor_id).execute()

            logger.info("Campaign successfully activated in Supabase!")

    return jsonify({"status": "success"}), 200


if __name__ == "__main__":
    app.run(port=5000, debug=True)
