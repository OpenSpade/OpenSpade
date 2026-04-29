from flask import Blueprint, jsonify

product_bp = Blueprint('product', __name__)


@product_bp.route('/list')
def get_products():
    return jsonify({"products": ["Laptop", "Phone"]})


@product_bp.route('/<int:product_id>')
def get_product(product_id):
    return jsonify({"id": product_id, "name": f"Product{product_id}"})
