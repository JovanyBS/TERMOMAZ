from app import app, db
from models import Client, Product, Order

with app.app_context():
    print(f"Clients: {Client.query.count()}")
    print(f"Products: {Product.query.count()}")
    print(f"Orders: {Order.query.count()}")
