from flask import Blueprint, jsonify

# 使用蓝图，不需要Flask实例
user_bp = Blueprint('user', __name__)


@user_bp.route('/list')
def get_users():
    return jsonify({"users": ["Alice", "Bob"]})


@user_bp.route('/<int:user_id>')
def get_user(user_id):
    return jsonify({"id": user_id, "name": f"User{user_id}"})
