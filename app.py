from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from models import db, Client, Product, Order, OrderItem
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///termomaz.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'supersecretkey' # Required for flash messages

db.init_app(app)

@app.route('/')
def index():
    # Basic stats
    total_clients = Client.query.count()
    total_products = Product.query.count()
    pending_orders = Order.query.filter_by(status='Pending').count()
    
    # Calculate monthly sales (simplified for MVP, just total of all completed orders)
    completed_orders = Order.query.filter_by(status='Completed').all()
    monthly_sales = sum(order.total for order in completed_orders)
    
    recent_orders = Order.query.order_by(Order.date.desc()).limit(5).all()
    
    return render_template('index.html', 
                           total_clients=total_clients, 
                           total_products=total_products,
                           pending_orders=pending_orders,
                           monthly_sales=monthly_sales,
                           recent_orders=recent_orders)

@app.route('/clients')
def clients():
    all_clients = Client.query.all()
    return render_template('clients.html', clients=all_clients)

@app.route('/clients/add', methods=['POST'])
def add_client():
    name = request.form.get('name')
    phone = request.form.get('phone')
    email = request.form.get('email')
    address = request.form.get('address')
    
    new_client = Client(name=name, phone=phone, email=email, address=address)
    db.session.add(new_client)
    db.session.commit()
    return redirect(url_for('clients'))

@app.route('/clients/edit/<int:id>', methods=['POST'])
def edit_client(id):
    client = Client.query.get_or_404(id)
    client.name = request.form.get('name')
    client.phone = request.form.get('phone')
    client.email = request.form.get('email')
    client.address = request.form.get('address')
    db.session.commit()
    return redirect(url_for('clients'))

@app.route('/clients/delete/<int:id>')
def delete_client(id):
    client = Client.query.get_or_404(id)
    db.session.delete(client)
    db.session.commit()
    return redirect(url_for('clients'))

@app.route('/inventory')
def inventory():
    all_products = Product.query.all()
    return render_template('inventory.html', products=all_products)

@app.route('/inventory/add', methods=['POST'])
def add_product():
    name = request.form.get('name')
    category = request.form.get('category')
    price = float(request.form.get('price'))
    stock = int(request.form.get('stock'))
    description = request.form.get('description')
    
    new_product = Product(name=name, category=category, price=price, stock=stock, description=description)
    db.session.add(new_product)
    db.session.commit()
    return redirect(url_for('inventory'))

@app.route('/inventory/edit/<int:id>', methods=['POST'])
def edit_product(id):
    product = Product.query.get_or_404(id)
    product.name = request.form.get('name')
    product.category = request.form.get('category')
    product.price = float(request.form.get('price'))
    product.stock = int(request.form.get('stock'))
    product.description = request.form.get('description')
    db.session.commit()
    return redirect(url_for('inventory'))

@app.route('/inventory/delete/<int:id>')
def delete_product(id):
    product = Product.query.get_or_404(id)
    db.session.delete(product)
    db.session.commit()
    return redirect(url_for('inventory'))

@app.route('/orders')
def orders():
    all_orders = Order.query.order_by(Order.date.desc()).all()
    all_clients = Client.query.all() # For the modal
    return render_template('orders.html', orders=all_orders, clients=all_clients)

@app.route('/orders/create', methods=['POST'])
def create_order():
    client_id = request.form.get('client_id')
    client = Client.query.get(client_id)
    
    # Create a basic order with client's address as default shipping address
    new_order = Order(client_id=client_id, status='Pending', shipping_address=client.address)
    db.session.add(new_order)
    db.session.commit()
    
    return redirect(url_for('order_details', id=new_order.id))

@app.route('/orders/<int:id>')
def order_details(id):
    order = Order.query.get_or_404(id)
    products = Product.query.all()
    return render_template('order_details.html', order=order, products=products)

@app.route('/orders/<int:id>/add_item', methods=['POST'])
def add_order_item(id):
    order = Order.query.get_or_404(id)
    product_id = request.form.get('product_id')
    quantity = int(request.form.get('quantity'))
    
    product = Product.query.get(product_id)
    
    if product and product.stock >= quantity:
        # Check if item already exists in order
        existing_item = OrderItem.query.filter_by(order_id=order.id, product_id=product.id).first()
        
        if existing_item:
            existing_item.quantity += quantity
        else:
            new_item = OrderItem(order_id=order.id, product_id=product.id, quantity=quantity, price_at_time=product.price)
            db.session.add(new_item)
        
        # Update stock and order total
        product.stock -= quantity
        order.total += product.price * quantity
        
        db.session.commit()
    else:
        flash(f'Error: No hay suficiente stock de {product.name}. Stock actual: {product.stock}', 'error')
    
    return redirect(url_for('order_details', id=id))

@app.route('/orders/<int:id>/remove_item/<int:item_id>')
def remove_order_item(id, item_id):
    order = Order.query.get_or_404(id)
    item = OrderItem.query.get_or_404(item_id)
    
    # Restore stock
    product = Product.query.get(item.product_id)
    if product:
        product.stock += item.quantity
        
    # Update total
    order.total -= item.price_at_time * item.quantity
    
    db.session.delete(item)
    db.session.commit()
    
    return redirect(url_for('order_details', id=id))

@app.route('/orders/delete/<int:id>')
def delete_order(id):
    order = Order.query.get_or_404(id)
    # Restore stock for all items
    for item in order.items:
        product = Product.query.get(item.product_id)
        if product:
            product.stock += item.quantity
            
    db.session.delete(order)
    db.session.commit()
    return redirect(url_for('orders'))

@app.route('/orders/<int:id>/update_status', methods=['POST'])
def update_order_status(id):
    order = Order.query.get_or_404(id)
    new_status = request.form.get('status')
    order.status = new_status
    db.session.commit()
    return redirect(url_for('order_details', id=id))

@app.route('/orders/<int:id>/update_address', methods=['POST'])
def update_order_address(id):
    order = Order.query.get_or_404(id)
    order.shipping_address = request.form.get('shipping_address')
    db.session.commit()
    flash('Dirección de envío actualizada', 'success')
    return redirect(url_for('order_details', id=id))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5000)
