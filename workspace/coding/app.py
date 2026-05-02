from flask import Flask, jsonify, request

app = Flask(__name__)

# Sample data
users = [
    {"id": 1, "name": "Alice"},
    {"id": 2, "name": "Bob"}
]

# GET /users - Return list of users
@app.route('/users', methods=['GET'])
def get_users():
    return jsonify(users)

# GET /users/<id> - Return a single user by ID
@app.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    user = next((u for u in users if u["id"] == user_id), None)
    if user:
        return jsonify(user)
    return jsonify({"error": "User not found"}), 404

# POST /users - Create a new user
@app.route('/users', methods=['POST'])
def create_user():
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400
    
    data = request.get_json()
    if 'name' not in data:
        return jsonify({"error": "Name is required"}), 400

    new_user = {
        "id": max(u["id"] for u in users) + 1 if users else 1,
        "name": data['name']
    }
    users.append(new_user)
    return jsonify(new_user), 201

# Run the app
if __name__ == '__main__':
    app.run(port=5000, debug=True)