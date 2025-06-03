from fastapi import FastAPI, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
from datetime import datetime
import requests


app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

client = AsyncIOMotorClient("mongodb://mongo:27017")
db = client.warehouse_db
collection = db.warehouse_data

@app.get("/")
async def gui_home(request: Request):
    warehouses = await collection.find().to_list(100)

    for warehouse in warehouses:
        resolved_products = []
        for p in warehouse.get("productData", []):
            try:
                r = requests.get(f"http://product_service:8002/product/{p['id']}", timeout=3)
                if r.status_code == 200:
                    resolved_products.append(r.json())
                else:
                    resolved_products.append(p)
            except Exception as e:
                print(f"Fehler bei Produkt-ID {p['id']}: {e}")
                resolved_products.append(p)
        warehouse["productData"] = resolved_products

    return templates.TemplateResponse("warehouses.html", {
        "request": request,
        "warehouses": warehouses
    })


@app.post("/add")
async def gui_add(
    warehouseID: str = Form(...),
    warehouseName: str = Form(...),
    timestamp: str = Form(...),
    warehousePostalCode: int = Form(...),
    warehouseCity: str = Form(...),
    warehouseCountrz: str = Form(...),
):
    try:
        parsed_time = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return RedirectResponse("/", status_code=303)  # ungültige Eingabe → ignorieren

    data = {
        "warehouseID": warehouseID,
        "warehouseName": warehouseName,
        "timestamp": parsed_time,
        "warehousePostalCode": warehousePostalCode,
        "warehouseCity": warehouseCity,
        "warehouseCountrz": warehouseCountrz,
        "productData": []
    }
    await collection.insert_one(data)
    return RedirectResponse("/", status_code=303)


@app.get("/edit/{id}")
async def gui_edit(id: str, request: Request):
    warehouse = await collection.find_one({"_id": ObjectId(id)})
    if not warehouse:
        return RedirectResponse("/", status_code=303)

    # Produktdetails auflösen
    resolved_products = []
    for p in warehouse.get("productData", []):
        try:
            r = requests.get(f"http://product_service:8002/product/{p['id']}", timeout=3)
            if r.status_code == 200:
                resolved_products.append(r.json())
            else:
                resolved_products.append(p)
        except Exception as e:
            print(f"Fehler bei Produkt-ID {p['id']}: {e}")
            resolved_products.append(p)

    warehouse["productData"] = resolved_products

    return templates.TemplateResponse("edit_warehouse.html", {
        "request": request,
        "warehouse": warehouse
    })


@app.post("/update/{id}")
async def gui_update(
    id: str,
    warehouseName: str = Form(...),
    warehousePostalCode: int = Form(...),
    warehouseCity: str = Form(...),
    warehouseCountrz: str = Form(...),
):
    await collection.update_one(
        {"_id": ObjectId(id)},
        {"$set": {
            "warehouseName": warehouseName,
            "warehousePostalCode": warehousePostalCode,
            "warehouseCity": warehouseCity,
            "warehouseCountrz": warehouseCountrz,
        }}
    )
    return RedirectResponse("/", status_code=303)


@app.post("/delete/{id}")
async def gui_delete(id: str):
    await collection.delete_one({"_id": ObjectId(id)})
    return RedirectResponse("/", status_code=303)


# 🔥 NEU: Produkt zu einem Warehouse hinzufügen
from fastapi import Request

@app.post("/add_product/{id}")
async def add_product_to_warehouse(
    id: str,
    request: Request,
    productID: int = Form(...)
):
    warehouse = await collection.find_one({"_id": ObjectId(id)})
    if not warehouse:
        print(f"WARNUNG: Warehouse mit ID {id} nicht gefunden.")
        return RedirectResponse("/", status_code=303)

    try:
        # Produktdaten vom product_service holen
        res = requests.get(f"http://product_service:8002/product/{productID}", timeout=5)
        if res.status_code != 200:
            print(f"Produkt {productID} nicht gefunden.")
            return RedirectResponse(f"/edit/{id}", status_code=303)

        product = res.json()
    except Exception as e:
        print("Fehler beim Product-Service:", e)
        return RedirectResponse(f"/edit/{id}", status_code=303)

    # Produkt im Warehouse speichern
    await collection.update_one(
        {"_id": ObjectId(id)},
        {"$push": {
            "productData": {
                "id": product["id"],
                "name": product["name"],
                "price": product["price"],
                "stock": product["stock"]
            }
        }}
    )
    return RedirectResponse(f"/edit/{id}", status_code=303)

from fastapi import Request
from fastapi.responses import RedirectResponse
import requests

from fastapi import Form, Request
import requests

@app.post("/update_product_in_warehouse/{warehouse_id}/{product_id}")
async def update_product_in_warehouse(
    warehouse_id: str,
    product_id: int,
    name: str = Form(...),
    price: float = Form(...),
    stock: int = Form(...),
    username: str = Form(...),
    password: str = Form(...)
):
    try:
        session = requests.Session()

        # Login mit Session, damit Cookie erhalten bleibt
        login_response = session.post(
            "http://product_service:8002/login",
            data={"username": username, "password": password},
            timeout=5,
            allow_redirects=True  # wichtig, damit redirect zu / akzeptiert wird
        )

        if login_response.status_code != 200 and login_response.status_code != 303:
            print("❌ Login fehlgeschlagen:", login_response.text)
            return RedirectResponse(f"/edit/{warehouse_id}", status_code=303)

        # Produkt aktualisieren mit gültiger Session
        update_response = session.post(
            f"http://product_service:8002/update_product/{product_id}",
            data={
                "name": name,
                "price": price,
                "stock": stock
            },
            timeout=5
        )

        if update_response.status_code != 200 and update_response.status_code != 303:
            print("❌ Fehler beim Updaten:", update_response.text)

    except Exception as e:
        print("❌ Ausnahme beim Update:", e)

    return RedirectResponse(f"/edit/{warehouse_id}", status_code=303)
@app.post("/delete_product/{warehouse_id}/{product_id}")
async def delete_product_in_warehouse(warehouse_id: str, product_id: int):
    try:
        res = requests.post(f"http://product_service:8002/delete_product/{product_id}", timeout=5)
    except Exception as e:
        print("Fehler beim Löschen:", e)

    # Produktdaten auch lokal aus dem Warehouse entfernen:
    await collection.update_one(
        {"_id": ObjectId(warehouse_id)},
        {"$pull": {"productData": {"id": product_id}}}
    )

    return RedirectResponse(f"/edit/{warehouse_id}", status_code=303)
