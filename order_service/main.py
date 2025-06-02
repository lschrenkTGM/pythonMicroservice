import requests
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

class Order(BaseModel):
    order_id: int
    product_id: int
    quantity: int

orders_db = []

@app.post("/order")
def create_order(order: Order):
    # 1. Produkt holen und Fehler abfangen
    try:
        resp = requests.get(f"http://product_service:8002/product/{order.product_id}")
        if resp.status_code != 200:
            raise HTTPException(status_code=404, detail="Product not found")
        product = resp.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Product service error: {str(e)}")

    # 2. Bestand prüfen
    if product["stock"] < order.quantity:
        raise HTTPException(status_code=400, detail="Not enough stock available")

    # 3. Bestand reduzieren im Product-Service
    product["stock"] = order.quantity
    try:
        resp2 = requests.post("http://product_service:8002/product/order", json=product)
        if resp2.status_code != 200:
            raise HTTPException(status_code=500, detail="Product stock update failed")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Product stock update error: {str(e)}")

    # 4. Order-ID prüfen
    for o in orders_db:
        if o.order_id == order.order_id:
            raise HTTPException(status_code=400, detail="Order ID already exists")

    # 5. Order speichern
    orders_db.append(order)
    return {"message": "Order created successfully"}

@app.get("/order")
def list_orders():
    return orders_db

@app.get("/order/{order_id}")
def get_order(order_id: int):
    for order in orders_db:
        if order.order_id == order_id:
            return order
    raise HTTPException(status_code=404, detail="Order not found")

@app.put("/order/{order_id}")
def update_order(order_id: int, updated: Order):
    for idx, order in enumerate(orders_db):
        if order.order_id == order_id:
            orders_db[idx] = updated
            return {"message": "Order updated successfully"}
    raise HTTPException(status_code=404, detail="Order not found")

@app.delete("/order/{order_id}")
def delete_order(order_id: int):
    for idx, order in enumerate(orders_db):
        if order.order_id == order_id:
            del orders_db[idx]
            return {"message": "Order deleted successfully"}
    raise HTTPException(status_code=404, detail="Order not found")
