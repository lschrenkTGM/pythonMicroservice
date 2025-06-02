from fastapi import FastAPI, HTTPException, Request, Form, Response
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import requests


app = FastAPI()

# Static files für CSS
app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

class Product(BaseModel):
    id: int
    name: str
    price: float
    stock: int

products_db = {}

# =======================
# LOGIN
# =======================

def is_logged_in(request: Request):
    return request.cookies.get("session") == "ok"

@app.get("/login")
def login_form(request: Request):
    return templates.TemplateResponse("login.html", {"request": request, "error": None})

@app.post("/login")
def login(request: Request, response: Response, username: str = Form(...), password: str = Form(...)):
    # Dummy-Email für den Login-Request, weil user_service das Feld erwartet
    email = "dummy@example.com"
    try:
        r = requests.post(
            "http://user_service:8001/login",
            json={"username": username, "email": email, "password": password},
            timeout=5
        )
        if r.status_code == 200:
            resp = RedirectResponse("/", status_code=303)
            resp.set_cookie("session", "ok")
            return resp
        else:
            return templates.TemplateResponse("login.html", {"request": request, "error": "Login fehlgeschlagen!"})
    except Exception:
        return templates.TemplateResponse("login.html", {"request": request, "error": "User-Service nicht erreichbar!"})

@app.get("/logout")
def logout():
    resp = RedirectResponse("/login", status_code=303)
    resp.delete_cookie("session")
    return resp

# =======================
# GUI CRUD
# =======================

@app.get("/")
def gui_home(request: Request):
    if not is_logged_in(request):
        return RedirectResponse("/login")
    products = list(products_db.values())
    return templates.TemplateResponse("products.html", {"request": request, "products": products})

@app.post("/add_product")
def gui_add_product(
    request: Request,
    id: int = Form(...),
    name: str = Form(...),
    price: float = Form(...),
    stock: int = Form(...)
):
    if not is_logged_in(request):
        return RedirectResponse("/login")
    products_db[id] = Product(id=id, name=name, price=price, stock=stock)
    return RedirectResponse("/", status_code=303)

@app.get("/edit_product/{id}")
def gui_edit_product(id: int, request: Request):
    if not is_logged_in(request):
        return RedirectResponse("/login")
    if id not in products_db:
        return RedirectResponse("/", status_code=303)
    product = products_db[id]
    return templates.TemplateResponse("edit_product.html", {"request": request, "product": product})

@app.post("/update_product/{id}")
def gui_update_product(
    id: int,
    request: Request,
    name: str = Form(...),
    price: float = Form(...),
    stock: int = Form(...)
):
    if not is_logged_in(request):
        return RedirectResponse("/login")
    if id in products_db:
        products_db[id] = Product(id=id, name=name, price=price, stock=stock)
    return RedirectResponse("/", status_code=303)

@app.post("/delete_product/{id}")
def gui_delete_product(id: int, request: Request):
    if not is_logged_in(request):
        return RedirectResponse("/login")
    if id in products_db:
        del products_db[id]
    return RedirectResponse("/", status_code=303)

# =======================
# API CRUD (wie gehabt)
# =======================

@app.post("/product")
def create_product(productIn: Product):
    if productIn.id in products_db:
        product = products_db[productIn.id]
        product.stock = productIn.stock
        product.price = productIn.price
        productIn = product
    products_db[productIn.id] = productIn
    return {"message": "Product created/updated successfully"}

@app.get("/product/{id}")
def get_product(id: int):
    if id not in products_db:
        raise HTTPException(status_code=404, detail="Product not found")
    return products_db[id]

@app.post("/product/order")
def order_product(productIn: Product):
    if productIn.id in products_db:
        product = products_db[productIn.id]
        product.stock = product.stock - productIn.stock
        products_db[productIn.id] = product
    return {"message": "Product stock updated."}

@app.delete("/product/{id}")
def delete_product(id: int):
    if id not in products_db:
        raise HTTPException(status_code=404, detail="Product not found")
    del products_db[id]
    return {"message": "Product deleted successfully"}

@app.get("/product")
def list_products():
    return list(products_db.values())

@app.put("/product/{id}")
def update_product(id: int, updated: Product):
    if id not in products_db:
        raise HTTPException(status_code=404, detail="Product not found")
    products_db[id] = updated
    return {"message": "Product updated successfully"}
