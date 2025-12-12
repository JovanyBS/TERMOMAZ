from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from models import db, Client, Product, Order, OrderItem
import os
import sys
from datetime import datetime, date

# --- Configuración de la Aplicación ---
if getattr(sys, 'frozen', False):
    template_folder = os.path.join(sys._MEIPASS, 'templates')
    static_folder = os.path.join(sys._MEIPASS, 'static')
    app = Flask(__name__, template_folder=template_folder, static_folder=static_folder)
else:
    app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///termomaz.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# La clave secreta es necesaria para las sesiones y los mensajes flash
app.secret_key = os.environ.get('SECRET_KEY', 'super_safe_and_secret_default_key_for_dev') 

db.init_app(app)

# --- Funciones de Utilidad ---

# Función para obtener el primer día del mes actual (para calcular ventas mensuales)
def get_start_of_current_month():
    today = date.today()
    return datetime(today.year, today.month, 1)

# --- Rutas del Dashboard ---

@app.route('/')
def index():
    # 1. Obtener estadísticas básicas
    total_clients = Client.query.count()
    total_products = Product.query.count()
    pending_orders = Order.query.filter_by(status='Pending').count()
    
    # 2. Calcular ventas mensuales (CORREGIDO: Solo pedidos completados desde el inicio del mes)
    start_of_month = get_start_of_current_month()
    
    monthly_sales_orders = Order.query.filter(
        Order.status == 'Completed',
        Order.date >= start_of_month
    ).all()
    
    # Sumar los totales
    monthly_sales = sum(order.total for order in monthly_sales_orders)
    
    # 3. Pedidos recientes
    # El `relationship` de Cliente en Orden debería ser accedido vía Order.client.name
    recent_orders = Order.query.order_by(Order.date.desc()).limit(5).all()
    
    return render_template('index.html', 
                           total_clients=total_clients, 
                           total_products=total_products,
                           pending_orders=pending_orders,
                           # Formateo básico del valor monetario (se puede mejorar en Jinja)
                           monthly_sales=f"{monthly_sales:.2f}", 
                           recent_orders=recent_orders)

# --- Rutas de Clientes ---

@app.route('/clients')
def clients():
    all_clients = Client.query.all()
    return render_template('clients.html', clients=all_clients)

@app.route('/clients/add', methods=['POST'])
def add_client():
    try:
        name = request.form.get('name')
        phone = request.form.get('phone')
        email = request.form.get('email')
        address = request.form.get('address')
        
        new_client = Client(name=name, phone=phone, email=email, address=address)
        db.session.add(new_client)
        db.session.commit()
        flash(f'Cliente "{name}" agregado correctamente.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al agregar cliente: {e}', 'error')
    return redirect(url_for('clients'))

@app.route('/clients/edit/<int:id>', methods=['POST'])
def edit_client(id):
    client = Client.query.get_or_404(id)
    try:
        client.name = request.form.get('name')
        client.phone = request.form.get('phone')
        client.email = request.form.get('email')
        client.address = request.form.get('address')
        db.session.commit()
        flash(f'Cliente "{client.name}" actualizado correctamente.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al editar cliente: {e}', 'error')
    return redirect(url_for('clients'))

@app.route('/clients/delete/<int:id>')
def delete_client(id):
    client = Client.query.get_or_404(id)
    try:
        db.session.delete(client)
        db.session.commit()
        flash(f'Cliente "{client.name}" eliminado correctamente.', 'success')
    except Exception as e:
        db.session.rollback()
        # Esto podría fallar si el cliente tiene pedidos asociados (Foreign Key constraint)
        flash(f'Error al eliminar cliente: {e}. Asegúrate de que no tenga pedidos asociados.', 'error')
    return redirect(url_for('clients'))

# --- Rutas de Inventario (Productos) ---

@app.route('/inventory')
def inventory():
    all_products = Product.query.all()
    return render_template('inventory.html', products=all_products)

@app.route('/inventory/add', methods=['POST'])
def add_product():
    try:
        name = request.form.get('name')
        category = request.form.get('category')
        price = float(request.form.get('price'))
        stock = int(request.form.get('stock'))
        description = request.form.get('description')
        
        new_product = Product(name=name, category=category, price=price, stock=stock, description=description)
        db.session.add(new_product)
        db.session.commit()
        flash(f'Producto "{name}" agregado correctamente.', 'success')
    except ValueError:
        flash('Error: El precio y el stock deben ser números válidos.', 'error')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al agregar producto: {e}', 'error')
    return redirect(url_for('inventory'))

@app.route('/inventory/edit/<int:id>', methods=['POST'])
def edit_product(id):
    product = Product.query.get_or_404(id)
    try:
        product.name = request.form.get('name')
        product.category = request.form.get('category')
        product.price = float(request.form.get('price'))
        product.stock = int(request.form.get('stock'))
        product.description = request.form.get('description')
        db.session.commit()
        flash(f'Producto "{product.name}" actualizado correctamente.', 'success')
    except ValueError:
        flash('Error: El precio y el stock deben ser números válidos.', 'error')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al editar producto: {e}', 'error')
    return redirect(url_for('inventory'))

@app.route('/inventory/delete/<int:id>')
def delete_product(id):
    product = Product.query.get_or_404(id)
    try:
        db.session.delete(product)
        db.session.commit()
        flash(f'Producto "{product.name}" eliminado correctamente.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al eliminar producto: {e}. Asegúrate de que no esté en pedidos.', 'error')
    return redirect(url_for('inventory'))

# --- Rutas de Pedidos (Órdenes) ---

@app.route('/orders')
def orders():
    all_orders = Order.query.order_by(Order.date.desc()).all()
    all_clients = Client.query.all() # Para el modal de creación
    return render_template('orders.html', orders=all_orders, clients=all_clients)

@app.route('/orders/create', methods=['POST'])
def create_order():
    client_id = request.form.get('client_id')
    client = Client.query.get(client_id)
    
    if not client:
        flash('Error: Cliente no encontrado.', 'error')
        return redirect(url_for('orders'))

    try:
        # Crear la orden inicial con total 0
        new_order = Order(client_id=client_id, status='Pending', shipping_address=client.address, total=0.0)
        db.session.add(new_order)
        db.session.commit() # Commit para obtener el ID de la orden
        flash(f'Orden #{new_order.id} creada para {client.name}. Agrega productos.', 'success')
        return redirect(url_for('order_details', id=new_order.id))
    except Exception as e:
        db.session.rollback()
        flash(f'Error al crear la orden: {e}', 'error')
        return redirect(url_for('orders'))


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
    
    if not product:
        flash('Error: Producto no encontrado.', 'error')
        return redirect(url_for('order_details', id=id))

    if product.stock >= quantity:
        try:
            # 1. Verificar si el item ya existe
            existing_item = OrderItem.query.filter_by(order_id=order.id, product_id=product.id).first()
            
            item_cost = product.price * quantity

            if existing_item:
                existing_item.quantity += quantity
            else:
                new_item = OrderItem(order_id=order.id, product_id=product.id, quantity=quantity, price_at_time=product.price)
                db.session.add(new_item)
            
            # 2. Actualizar stock y total de la orden
            product.stock -= quantity
            order.total += item_cost
            
            db.session.commit()
            flash(f'{quantity}x de {product.name} añadido a la orden.', 'success')

        except Exception as e:
            db.session.rollback()
            flash(f'Error al agregar producto: {e}', 'error')
    else:
        flash(f'Error: Stock insuficiente. Solo quedan {product.stock} de {product.name}.', 'error')
    
    return redirect(url_for('order_details', id=id))

@app.route('/orders/<int:id>/remove_item/<int:item_id>')
def remove_order_item(id, item_id):
    order = Order.query.get_or_404(id)
    item = OrderItem.query.get_or_404(item_id)
    
    try:
        # 1. Restaurar stock
        product = Product.query.get(item.product_id)
        if product:
            product.stock += item.quantity
        
        # 2. Actualizar total
        order.total -= item.price_at_time * item.quantity
        
        # 3. Eliminar item
        db.session.delete(item)
        db.session.commit()
        flash('Ítem de la orden eliminado y stock restaurado.', 'warning')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al eliminar ítem: {e}', 'error')
    
    return redirect(url_for('order_details', id=id))

@app.route('/orders/delete/<int:id>')
def delete_order(id):
    order = Order.query.get_or_404(id)
    
    try:
        # Restaurar stock para todos los ítems antes de eliminar la orden
        for item in order.items:
            product = Product.query.get(item.product_id)
            if product:
                product.stock += item.quantity
                
        db.session.delete(order)
        db.session.commit()
        flash(f'Orden #{id} eliminada y stock restaurado.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al eliminar la orden: {e}', 'error')

    return redirect(url_for('orders'))

@app.route('/orders/<int:id>/update_status', methods=['POST'])
def update_order_status(id):
    order = Order.query.get_or_404(id)
    new_status = request.form.get('status')
    
    try:
        order.status = new_status
        db.session.commit()
        flash(f'Estado de la Orden #{id} actualizado a {new_status}.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al actualizar estado: {e}', 'error')

    return redirect(url_for('order_details', id=id))

@app.route('/orders/<int:id>/update_address', methods=['POST'])
def update_order_address(id):
    order = Order.query.get_or_404(id)
    try:
        order.shipping_address = request.form.get('shipping_address')
        db.session.commit()
        flash('Dirección de envío actualizada', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al actualizar dirección: {e}', 'error')
    return redirect(url_for('order_details', id=id))

@app.route('/orders/<int:id>/add_payment', methods=['POST'])
def add_order_payment(id):
    order = Order.query.get_or_404(id)
    try:
        amount = float(request.form.get('amount', 0))
        
        if amount <= 0:
            flash('El monto del pago debe ser mayor a 0.', 'error')
            return redirect(url_for('order_details', id=id))

        # Actualizar monto pagado
        order.paid_amount = (order.paid_amount or 0) + amount
        
        # Calcular restante
        remaining = order.total - order.paid_amount

        # Lógica de auto-completado
        if remaining <= 0.01: # Usamos un pequeño margen por errores de punto flotante
            order.status = 'Completed'
            order.payment_status = 'Paid'
            # Si pagó de más, podríamos ajustar el paid_amount al total exacto o dejarlo como "crédito"
            # Por simplicidad, dejamos el paid_amount tal cual se ingresó.
            flash(f'Pago registrado. ¡La orden ha sido totalmente liquidada y marcada como COMPLETADA!', 'success')
        else:
            order.payment_status = 'Partial'
            flash(f'Pago de ${amount} registrado. Restan ${remaining:.2f}', 'success')

        db.session.commit()

    except ValueError:
        flash('Monto inválido.', 'error')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al registrar pago: {e}', 'error')

    return redirect(url_for('order_details', id=id))

@app.route('/orders/<int:id>/note')
def order_note(id):
    order = Order.query.get_or_404(id)
    return render_template('order_note.html', order=order)

# --- Rutas de POS (Punto de Venta) ---

@app.route('/pos')
def pos():
    products = Product.query.all()
    clients = Client.query.all()
    return render_template('pos.html', products=products, clients=clients)

@app.route('/pos/create_order', methods=['POST'])
def create_pos_order():
    """
    Crea una orden directamente desde el POS usando una solicitud JSON.
    CORREGIDO: El cálculo del total debe hacerse antes del commit final
    """
    data = request.get_json()
    client_id = data.get('client_id')
    items = data.get('items')
    
    if not client_id or not items:
        return jsonify({'success': False, 'message': 'Faltan datos (cliente o ítems)'})
    
    try:
        client = Client.query.get(client_id)
        if not client:
            return jsonify({'success': False, 'message': 'Cliente no encontrado.'})

        # 1. Crear Orden base (status 'Completed' ya que es venta directa)
        new_order = Order(client_id=client_id, status='Completed', shipping_address=client.address, total=0.0)
        db.session.add(new_order)
        # Hacemos un flush para que new_order tenga un ID, necesario para OrderItem
        db.session.flush() 
        
        total_order = 0
        
        # 2. Procesar ítems y verificar stock
        for item in items:
            product = Product.query.get(item['id'])
            quantity = item['quantity']

            if not product:
                db.session.rollback()
                return jsonify({'success': False, 'message': f'Producto ID {item["id"]} no existe.'})
            
            if product.stock < quantity:
                db.session.rollback()
                return jsonify({'success': False, 'message': f'Stock insuficiente para {product.name}. Solo quedan {product.stock}'})
                
            order_item = OrderItem(
                order_id=new_order.id, # Ahora new_order.id ya existe
                product_id=product.id,
                quantity=quantity,
                price_at_time=product.price
            )
            
            # En lugar de usar append, agregamos el OrderItem a la sesión
            db.session.add(order_item)
            
            # Actualizar stock
            product.stock -= quantity
            total_order += product.price * quantity
            
        # 3. Asignar el total final a la orden
        # 3. Asignar el total final a la orden
        new_order.total = total_order

        # --- Payment Logic ---
        payment_type = data.get('payment_type', 'full') # 'full' or 'partial'
        payment_amount = float(data.get('payment_amount', 0))
        
        if payment_type == 'full':
            new_order.paid_amount = total_order
            new_order.payment_status = 'Paid'
            # Explicitly keep status as Pending per user request
            new_order.status = 'Pending'
        else:
            new_order.paid_amount = payment_amount
            if payment_amount >= total_order - 0.01:
                 new_order.payment_status = 'Paid'
            elif payment_amount > 0:
                 new_order.payment_status = 'Partial'
            else:
                 new_order.payment_status = 'Pending'
            
            # Ensure status is Pending
            new_order.status = 'Pending'
        # ---------------------
        
        # 4. Commit final
        db.session.commit()
        
        return jsonify({'success': True, 'order_id': new_order.id, 'message': 'Venta registrada con éxito.'})
        
    except Exception as e:
        # 5. Rollback en caso de cualquier error (CRUCIAL)
        db.session.rollback()
        print(f"Error en create_pos_order: {e}")
        return jsonify({'success': False, 'message': f'Error interno del servidor: {str(e)}'})

# --- API Endpoints para AJAX (Modales) ---

@app.route('/api/clients', methods=['POST'])
def api_add_client():
    data = request.get_json()
    try:
        name = data.get('name')
        if not name:
             return jsonify({'success': False, 'message': 'El nombre es requerido'})
             
        new_client = Client(
            name=name,
            phone=data.get('phone'),
            email=data.get('email'),
            address=data.get('address')
        )
        db.session.add(new_client)
        db.session.commit()
        return jsonify({
            'success': True, 
            'client': {
                'id': new_client.id,
                'name': new_client.name,
                'phone': new_client.phone
            },
            'message': 'Cliente agregado correctamente'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/products', methods=['POST'])
def api_add_product():
    data = request.get_json()
    try:
        name = data.get('name')
        price = data.get('price')
        stock = data.get('stock')
        
        if not name or price is None or stock is None:
            return jsonify({'success': False, 'message': 'Nombre, precio y stock son requeridos'})

        new_product = Product(
            name=name,
            category=data.get('category'),
            price=float(price),
            stock=int(stock),
            description=data.get('description')
        )
        db.session.add(new_product)
        db.session.commit()
        return jsonify({
            'success': True,
            'product': {
                'id': new_product.id,
                'name': new_product.name,
                'price': new_product.price,
                'stock': new_product.stock,
                'category': new_product.category,
                'description': new_product.description
            },
            'message': 'Producto agregado correctamente'
        })
    except ValueError:
        return jsonify({'success': False, 'message': 'Precio y stock deben ser números válidos'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})

# --- Rutas de Reportes (Simplificadas) ---

@app.route('/reports')
def reports():
    # 1. Obtener filtros de fecha
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')
    
    # Valores por defecto: Mes actual
    today = date.today()
    if not start_date_str:
        start_date = datetime(today.year, today.month, 1)
        start_date_str = start_date.strftime('%Y-%m-%d')
    else:
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
        except ValueError:
             start_date = datetime(today.year, today.month, 1) # Fallback

    if not end_date_str:
        # Fin de mes (aproximado, o hoy)
        end_date = datetime.combine(today, datetime.max.time())
        end_date_str = today.strftime('%Y-%m-%d')
    else:
        try:
             # Aseguramos que cubra todo el día final
             end_date_dt = datetime.strptime(end_date_str, '%Y-%m-%d')
             end_date = datetime.combine(end_date_dt.date(), datetime.max.time())
        except ValueError:
             end_date = datetime.combine(today, datetime.max.time())

    # 2. Consultas para Reporte de Pedidos
    orders_query = Order.query.filter(Order.date >= start_date, Order.date <= end_date)
    orders = orders_query.all()
    
    total_sales = sum(o.total for o in orders)
    total_orders_count = len(orders)
    completed_orders = sum(1 for o in orders if o.status == 'Completed')
    pending_orders = sum(1 for o in orders if o.status == 'Pending')
    
    # 3. Consultas para Rotación de Inventario
    # Queremos: Producto, Unidades Vendidas (en el rango), Stock Actual, Ingresos Generados
    
    # Obtenemos todos los items de las órdenes en el rango
    # Optimización: Podríamos hacer esto con una query de agregación de SQL, pero en Python es más legible para este prototipo.
    
    rotation_data = {} # {product_id: {'product': obj, 'sold': 0, 'revenue': 0}}
    
    # Precargamos productos para no hacer N queries
    all_products = {p.id: p for p in Product.query.all()}
    
    # Inicializamos con 0 para todos los productos (para ver los que NO se vendieron también, opcional)
    for p_id, p in all_products.items():
        rotation_data[p_id] = {'product': p, 'sold': 0, 'revenue': 0}

    for order in orders:
        # Solo contamos ventas de pedidos no cancelados? O todos?
        # Generalmente rotación incluye todo lo que salió del inventario.
        # Si el pedido está 'Cancelled' y repusimos stock, NO debería contar.
        if order.status == 'Cancelled':
            continue
            
        for item in order.items:
            if item.product_id in rotation_data:
                rotation_data[item.product_id]['sold'] += item.quantity
                rotation_data[item.product_id]['revenue'] += (item.price_at_time * item.quantity)
    
    # Convertir a lista y ordenar por unidades vendidas (descendente)
    rotation_list = sorted(rotation_data.values(), key=lambda x: x['sold'], reverse=True)

    return render_template('reports.html', 
                           start_date=start_date_str,
                           end_date=end_date_str,
                           total_sales=total_sales,
                           total_orders_count=total_orders_count,
                           completed_orders=completed_orders,
                           pending_orders=pending_orders,
                           rotation_data=rotation_list)

# --- Inicialización de la Aplicación ---

if __name__ == '__main__':
    # Crear la base de datos si no existe
    with app.app_context():
        # Verificamos si ya existe la base de datos antes de crearla para evitar advertencias
        if not os.path.exists('termomaz.db'):
            db.create_all()
            # Opcional: Agregar algunos datos de prueba al inicio si la DB está vacía
            print("Database initialized and models created.")
        else:
            print("Database already exists.")
            
    # Ejecutar la aplicación
    # Se recomienda usar gunicorn o waitress para producción, pero para desarrollo está bien.
    if getattr(sys, 'frozen', False):
        # Si se ejecuta como ejecutable (PyInstaller), desactivar debug
        # y abrir el navegador automáticamente (opcional, pero útil)
        import webbrowser
        from threading import Timer
        def open_browser():
            webbrowser.open_new('http://127.0.0.1:5000/')
        Timer(1, open_browser).start()
        app.run(debug=False, port=5000)
    else:
        app.run(debug=True, port=5000)