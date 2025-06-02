

# **Entwicklungsprotokoll Microservice-Shop**

**Projekt:** Microservice-Shop-System  
**Bearbeiter:** Lukas Schrenk

---

### **Schritt 1: Projektstruktur anlegen**
- Vier Verzeichnisse für die Services erstellt: `user_service`, `product_service`, `order_service`, `payment_service`.
- In jedem Verzeichnis ein neues FastAPI-Projekt initialisiert (`main.py` angelegt).

---

### **Schritt 2: User-Service implementieren**
- In `user_service/main.py` das User-Modell mit `username`, `email`, `password` erstellt.
- Dictionary `users_db` für die User-Daten angelegt.
- POST-Endpunkt `/signup` zum Registrieren von Usern programmiert.
- POST-Endpunkt `/login` hinzugefügt, der Username und Passwort prüft.
- Fehlerbehandlung für doppelte User und falsche Logins eingebaut.

---

### **Schritt 3: Product-Service implementieren**
- In `product_service/main.py` das Product-Modell erstellt.
- Dictionary `products_db` für Produktdaten angelegt.
- CRUD-Endpunkte (`/product`, `/product/{id}`) für Produkte programmiert.
- Jinja2-Templates für die Produkt-GUI erstellt.
- `static`-Ordner für CSS angelegt.
- Fehler beim Start wegen fehlendem `static`-Ordner erkannt und durch Anlegen des Ordners behoben.
- Fehler beim Mounten von `static` ohne führenden Slash erkannt und durch Änderung zu `/static` behoben.

---

### **Schritt 4: Authentifizierung für Product-GUI**
- Login-Formular in der GUI erstellt.
- Beim Login POST-Request an User-Service `/login` implementiert.
- Dummy-Email im Login-Request verwendet, da User-Service das Feld verlangt.
- Bei erfolgreichem Login Session-Cookie gesetzt (`session=ok`).
- Alle GUI-Routen prüfen das Session-Cookie, sonst Redirect auf Login.
- Fehlerbehandlung bei Login-Fehlern und User-Service-Timeouts eingebaut.

---

### **Schritt 5: Order-Service implementieren**
- In `order_service/main.py` das Order-Modell mit `order_id`, `product_id`, `quantity` erstellt.
- Dictionary `orders_db` für Bestellungen angelegt.
- CRUD-Endpunkte für Orders programmiert.

---

### **Schritt 6: Payment-Service implementieren**
- In `payment_service/main.py` PaymentRequest- und Payment-Modell erstellt.
- Liste `payments_db` für Zahlungen angelegt.
- POST-Endpunkt `/pay` programmiert:
    - HTTP-Request an Order-Service (`/order/{order_id}`) eingebaut, um Existenz der Order zu prüfen.
    - Fehlerbehandlung für nicht existierende Orders und Verbindungsprobleme eingebaut.
    - Optional: Betrag muss positiv sein, sonst Fehler.
    - Zahlung wird gespeichert, wenn alles passt.
- GET- und DELETE-Endpunkte für Zahlungen ergänzt.

---

### **Schritt 7: Service-Kommunikation testen**
- Alle Services mit Docker Compose gestartet.
- Überprüft, dass alle Services über ihre Service-Namen erreichbar sind (z.B. `http://user_service:8001`).
- Produkt-GUI im Browser getestet: Login, Produkt-CRUD, Logout.
- Mit HTTP-Client (z.B. REST Client) die Endpunkte von Order- und Payment-Service getestet.

---

### **Schritt 8: Fehlerbehebung und Anpassungen**
- Fehler beim Login-Request (fehlende Email) durch Dummy-Email im Product-Service behoben.
- Fehler beim Mounten von `static` durch Korrektur des Pfads und Anlegen des Ordners gelöst.
- Ursprünglicher Versuch, im Payment-Service einen Maximalbetrag zu prüfen, verworfen, da Order kein Preisfeld hat.
- Payment-Service so angepasst, dass nur noch die Existenz der Order und ein positiver Betrag geprüft werden.

---

### **Schritt 9: Endgültige Tests**
- User-Registrierung und Login getestet.
- Produktverwaltung (CRUD) nur mit Login getestet.
- Orders angelegt und abgerufen.
- Zahlungen für existierende und nicht existierende Orders getestet (Fehlerfall geprüft).
- Negative Zahlbeträge getestet (werden abgelehnt).

---

### **Schritt 10: Abschluss**
- Alle Anforderungen wurden umgesetzt.
- Die Microservices funktionieren einzeln und im Zusammenspiel.
- Die Kommunikation über HTTP und Docker Compose läuft stabil.
- Das System ist bereit für weitere Erweiterungen.

---

