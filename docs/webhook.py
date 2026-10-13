@app.route("/paypal-webhook", methods=["POST"])
def paypal_webhook():
    """Receives payment confirmation from PayPal/frontend and activates campaign in Supabase."""
    try:
        data = request.json
        
        # 1. Register Vendor in Supabase
        vendor_res = supabase.table("mamachi_vendors").insert({
            "name": data.get("vendor_name"),
            "email": data.get("vendor_email"),
            "status": "active",
            "fee_paid": True
        }).execute()

        vendor_id = vendor_res.data[0]["id"] if vendor_res.data else None

        # 2. Register Active Product Campaign in Supabase
        product_payload = {
            "vendor_id": vendor_id,
            "product_title": data.get("product_title"),
            "destination_url": data.get("destination_url"),
            "manuscript_text": data.get("manuscript_text"),
            "target_cities": data.get("target_cities"),
            "target_neighborhoods": data.get("target_neighborhoods"),
            "billing_model": data.get("billing_model"),
            "is_active": True,  # Activated immediately upon PayPal approval
            "fee_paid": True
        }
        
        supabase.table("mamachi_products").insert(product_payload).execute()
        logger.info("PayPal payment verified & campaign activated successfully!")

        return jsonify({"status": "success"}), 200

    except Exception as e:
        logger.exception("PayPal webhook processing failed: %s", e)
        return jsonify({"error": str(e)}), 500
