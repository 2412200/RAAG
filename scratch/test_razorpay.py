import os
from dotenv import load_dotenv
import razorpay

load_dotenv()

key_id = os.getenv("RAZORPAY_KEY_ID")
key_secret = os.getenv("RAZORPAY_KEY_SECRET")

print("Key ID:", key_id)
print("Key Secret:", key_secret)

try:
    client = razorpay.Client(auth=(key_id, key_secret))
    order = client.order.create({
        "amount": 100,
        "currency": "INR",
        "receipt": "test_receipt",
        "payment_capture": 1
    })
    print("SUCCESS! Created order:", order["id"])
except Exception as e:
    print("FAILED! Razorpay error:", str(e))
