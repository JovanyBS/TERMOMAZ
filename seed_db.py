from app import app, db
from models import Client, Product, Order, OrderItem
from datetime import datetime, timedelta

def seed_data():
    with app.app_context():
        # Check if data already exists
        if Client.query.first():
            print("Database already contains data. Skipping seed.")
            return

        print("Seeding database...")

        # Clients
        client1 = Client(name="Juan Perez", phone="555-0101", email="juan@example.com", address="Av. Reforma 123, CDMX")
        client2 = Client(name="Maria Garcia", phone="555-0102", email="maria@example.com", address="Calle 10 #45, Monterrey")
        client3 = Client(name="Empresa XYZ", phone="555-0103", email="contacto@xyz.com", address="Polanco 456, CDMX")
        
        db.session.add_all([client1, client2, client3])
        db.session.commit()

        # Products
        prod1 = Product(name="Termo Acero 500ml", category="thermos", price=250.00, stock=100, description="Termo de acero inoxidable doble pared")
        prod2 = Product(name="Termo Deportivo 1L", category="thermos", price=350.00, stock=50, description="Termo deportivo con boquilla")
        prod3 = Product(name="Caja Regalo Chica", category="box", price=50.00, stock=200, description="Caja de cartón decorada 20x20x20")
        prod4 = Product(name="Caja Regalo Grande", category="box", price=80.00, stock=150, description="Caja de cartón decorada 40x40x40")
        
        db.session.add_all([prod1, prod2, prod3, prod4])
        db.session.commit()

        # Orders
        # Order 1: Completed
        order1 = Order(client_id=client1.id, status='Completed', date=datetime.utcnow() - timedelta(days=5), shipping_address=client1.address)
        db.session.add(order1)
        db.session.commit()
        
        item1 = OrderItem(order_id=order1.id, product_id=prod1.id, quantity=2, price_at_time=prod1.price)
        order1.items.append(item1)
        order1.total = item1.quantity * item1.price_at_time
        
        # Order 2: Pending
        order2 = Order(client_id=client2.id, status='Pending', date=datetime.utcnow() - timedelta(days=1), shipping_address=client2.address)
        db.session.add(order2)
        db.session.commit()
        
        item2 = OrderItem(order_id=order2.id, product_id=prod2.id, quantity=1, price_at_time=prod2.price)
        item3 = OrderItem(order_id=order2.id, product_id=prod3.id, quantity=5, price_at_time=prod3.price)
        order2.items.append(item2)
        order2.items.append(item3)
        order2.total = (item2.quantity * item2.price_at_time) + (item3.quantity * item3.price_at_time)

        db.session.commit()
        
        print("Database seeded successfully!")

if __name__ == "__main__":
    seed_data()
