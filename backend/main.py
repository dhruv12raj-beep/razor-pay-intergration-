from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import razorpay
import os
import hmac
import hashlib

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://aizenstore.vercel.app",
        "http://127.0.0.1:5500"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

KEY_ID = os.getenv("RAZORPAY_KEY_ID")
KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET")

print("KEY_ID =", KEY_ID)
print("KEY_SECRET exists =", bool(KEY_SECRET))

if not KEY_ID or not KEY_SECRET:
    raise Exception("Razorpay environment variables are missing")

client = razorpay.Client(auth=(KEY_ID, KEY_SECRET))

class OrderRequest(BaseModel):
    plan: str
    amount: int

class VerifyRequest(BaseModel):
    razorpay_payment_id: str
    razorpay_order_id: str
    razorpay_signature: str
    plan: str

@app.get("/")
def home():
    return {"message": "Backend running"}

@app.post("/create-order")
def create_order(data: OrderRequest):
    try:
        order = client.order.create({
            "amount": data.amount,
            "currency": "INR",
            "payment_capture": 1,
            "notes": {
                "plan": data.plan
            }
        })

        return {
            "id": order["id"],
            "amount": order["amount"],
            "currency": order["currency"]
        }

    except Exception as e:
        print("CREATE ORDER ERROR:", str(e))
        return {
            "success": False,
            "error": str(e)
        }

@app.post("/verify-payment")
def verify_payment(data: VerifyRequest):
    try:
        body = f"{data.razorpay_order_id}|{data.razorpay_payment_id}"

        expected_signature = hmac.new(
            KEY_SECRET.encode(),
            body.encode(),
            hashlib.sha256
        ).hexdigest()

        if expected_signature != data.razorpay_signature:
            return {
                "success": False,
                "message": "Invalid payment signature"
            }

        BASE_URL = "https://aizenstore.vercel.app"

        if data.plan == "basic":
            redirect_url = f"{BASE_URL}/success.html?plan=basic"
        elif data.plan == "standard":
            redirect_url = f"{BASE_URL}/success.html?plan=standard"
        else:
            redirect_url = f"{BASE_URL}/success.html?plan=premium"

        return {
            "success": True,
            "redirect_url": redirect_url
        }

    except Exception as e:
        print("VERIFY PAYMENT ERROR:", str(e))
        return {
            "success": False,
            "message": str(e)
        }