import os
from supabase import create_client

SUPABASE_URL = os.environ.get("SUPABASE_URL", "YOUR_SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "YOUR_SUPABASE_SERVICE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

response = supabase.table("mamachi_vendors").insert({
    "name": "Acme Publishing",
    "email": "creator@acmebooks.com",
    "status": "active",
    "fee_paid": True
}).execute()

print("Vendor added successfully:", response.data)
