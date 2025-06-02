from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
import requests

app = FastAPI()

class PaymentRequest(BaseModel):
    order_id: int
    amount: float

class Payment(PaymentRequest):
    payment_id: int
    status: str

payments_db = []
payment_counter = 1

ORDER_SERVICE_URL = "http://order_service:8003/order"  # Passe ggf. an

@app.post("/pay", response_model=Payment)
def make_payment(payment: PaymentRequest):
    global payment_counter

    # Prüfe, ob Order existiert
    try:
        resp = requests.get(f"{ORDER_SERVICE_URL}/{payment.order_id}", timeout=5)
        if resp.status_code != 200:
            raise HTTPException(status_code=404, detail="Order not found")
        # order = resp.json()   # wird nicht weiter benötigt
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Order-Service nicht erreichbar: {str(e)}")

    # Optional: Prüfe, ob Betrag positiv ist
    if payment.amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive.")

    # Zahlung anlegen
    payment_obj = Payment(
        payment_id=payment_counter,
        order_id=payment.order_id,
        amount=payment.amount,
        status="success"
    )
    payments_db.append(payment_obj)
    payment_counter += 1
    return payment_obj

@app.get("/payments", response_model=List[Payment])
def list_payments():
    return payments_db

@app.get("/payments/{payment_id}", response_model=Payment)
def get_payment(payment_id: int):
    for p in payments_db:
        if p.payment_id == payment_id:
            return p
    raise HTTPException(status_code=404, detail="Payment not found")

@app.delete("/payments/{payment_id}")
def delete_payment(payment_id: int):
    for idx, p in enumerate(payments_db):
        if p.payment_id == payment_id:
            del payments_db[idx]
            return {"message": "Payment deleted"}
    raise HTTPException(status_code=404, detail="Payment not found")
