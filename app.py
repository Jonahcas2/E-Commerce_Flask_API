from __future__ import annotations
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy import ForeignKey, Table, Column, String, Integer, DateTime, Float
from marshmallow import ValidationError
from typing import List, Optional
from datetime import datetime

# Initialize App & Configuration
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:TrustInTheForce77!@localhost/ecommerce_api'
app.config['SQLALCHEMY_TRACK_MODIFICATION'] = False

# Initialize SQLAlchemy & Marshmallow
db = SQLAlchemy(app)
ma = Marshmallow(app)

# Association table
order_product = Table(
    'order_product',
    db.metadata,
    db.Column('order_id', ForeignKey("order.id"), primary_key=True),
    db.Column('product_id', ForeignKey('product.id'), primary_key=True)
)

# Models - User, Product, Order
class User(db.Model):
    __tablename__ = "user_account"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(30), nullable=False)
    address: Mapped[str] = mapped_column(String(200), unique=True)
    email: Mapped[Optional[str]] = mapped_column(String(200))
    orders: Mapped[List["Order"]] = relationship("Order", backref='user',cascade="all, delete-orphan")

class Order(db.Model):
    __tablename__ = "order"
    id: Mapped[int] = mapped_column(primary_key=True)
    order_date: Mapped[datetime] = mapped_column(DateTime, default=datetime)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('user_account.id'))
    product: Mapped[List["Product"]] = relationship("Product", secondary=order_product, backref="orders")

class Product(db.Model):
    __tablename__ = "product"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    product_name: Mapped[str] = mapped_column(String(30), nullable=False)
    price: Mapped[float] = mapped_column(Float)

# Associated Schemas
class UserSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = User
        include_fk = True
        load_instance = True
user_schema = UserSchema()
users_schema = UserSchema(many=True)

class OrderSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Order
        include_fk = True
        load_instance = True
order_schema = OrderSchema()
orders_schema = OrderSchema(many=True)

class ProductSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Product
        load_instance = True
product_schema = ProductSchema()
products_schema = ProductSchema(many=True)

@app.route('/')
def index():
    return "API is running!"

# User Routes
@app.route('/users', methods=['POST'])
def create_user():
    name = request.json['name']
    address = request.json['address']
    email = request.json['email']
    user = User(name=name, address=address, email=email)
    db.session.add(user)
    db.session.commit()
    return user_schema.jsonify(user)

@app.route('/users', methods=['GET'])
def get_users():
    all_users = User.query.all()
    return users_schema.jsonify(all_users)

@app.route('/users/<int:id>', methods=['GET'])
def get_user(id):
    user = User.query.get_or_404(id)
    return user_schema.jsonify(user)

@app.route('/users/<int:id>/update', methods=['PUT'])
def update_user(id):
    user = User.query.get_or_404(id)
    data = request.json
    user.name = data.get('name', user.name)
    user.address = data.get('address', user.address)
    user.email = data.get('email', user.email)
    db.session.commit()
    return user_schema.jsonify(user)

@app.route('/users/<int:id>', methods=['DELETE'])
def delete_user(id):
    user = User.query.get_or_404(id)
    db.session.delete(user)
    db.session.commit()
    return jsonify({'message': 'User deleted'})

# Product Routes
@app.route('/products', methods=['POST'])
def create_product():
    product = Product(
        product_name=request.json['product_name'],
        price=request.json['price']
    )
    db.session.add(product)
    db.session.commit()
    return product_schema.jsonify(product)

@app.route('/products', methods=['GET'])
def get_products():
    return products_schema.jsonify(Product.query.all())

@app.route('/products/<int:id>', methods=['GET'])
def get_product(id):
    product = Product.query.get_or_404(id)
    return product_schema.jsonify(product)

@app.route('/products/<int:id>/update', methods=['PUT'])
def update_product(id):
    product = Product.query.get_or_404(id)
    data = request.json
    product.product_name = data.get('product_name', product.product_name)
    product.price = data.get('price', product.price)
    db.session.commit()
    return product_schema.jsonify(product)

@app.route('/products/<int:id>', methods=['DELETE'])
def delete_product(id):
    product = Product.query.get_or_404(id)
    db.session.delete(product)
    db.session.commit()
    return jsonify({'message': 'Product deleted'})


# Orders Routes
@app.route('/orders', methods=['POST'])
def create_order():
    user_id = request.json['user_id']
    order_date = datetime.strptime(request.json['order_date'], '%Y-%m-%d')
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User does not exist'}), 404
    order = Order(user_id=user_id, order_date=order_date)
    db.session.add(order)
    db.session.commit()
    return order_schema.jsonify(order)

@app.route('/orders/<int:order_id>/add_product/<int:product_id>', methods=['PUT'])
def add_product_to_order(order_id, product_id):
    order = Order.query.get_or_404(order_id)
    product = Product.query.get_or_404(product_id)
    if product not in order.product:
        order.product.append(product)
        db.session.commit()
    return order_schema.jsonify(order)

@app.route('/orders/<int:order_id>/remove_product/<int:product_id>', methods=['DELETE'])
def remove_product_from_order(order_id, product_id):
    order = Order.query.get_or_404(order_id)
    product = Product.query.get_or_404(product_id)
    if product in order.product:
        order.product.remove(product)
        db.session.commit()
    return order_schema.jsonify(order)

@app.route('/orders/user/<int:user_id>', methods=['GET'])
def get_orders_by_user(user_id):
    orders = Order.query.filter_by(user_id=user_id).all()
    return orders_schema.jsonify(orders)

@app.route('/orders/<int:order_id>/products', methods=['GET'])
def get_products_in_order(order_id):
    order = Order.query.get_or_404(order_id)
    return product_schema.jsonify(order)

# Run server
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)