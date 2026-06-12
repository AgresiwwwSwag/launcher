from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime, timedelta
import hashlib
import json
import os

app = Flask(__name__)
CORS(app)

# Файл для хранения данных
DATA_FILE = 'users.json'

def load_users():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_users(users):
    with open(DATA_FILE, 'w') as f:
        json.dump(users, f, indent=2)

# Хеширование пароля
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Регистрация
@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    
    users = load_users()
    
    if username in users:
        return jsonify({'success': False, 'error': 'Пользователь уже существует'}), 400
    
    users[username] = {
        'username': username,
        'email': email,
        'password': hash_password(password),
        'role': 'user',
        'registered': datetime.now().isoformat(),
        'lastLogin': None,
        'gameInstalled': False
    }
    
    save_users(users)
    return jsonify({'success': True, 'message': 'Регистрация успешна'})

# Вход
@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    users = load_users()
    
    if username not in users:
        return jsonify({'success': False, 'error': 'Неверный логин или пароль'}), 401
    
    if users[username]['password'] != hash_password(password):
        return jsonify({'success': False, 'error': 'Неверный логин или пароль'}), 401
    
    # Обновляем время последнего входа
    users[username]['lastLogin'] = datetime.now().isoformat()
    save_users(users)
    
    return jsonify({
        'success': True,
        'user': {
            'username': users[username]['username'],
            'email': users[username]['email'],
            'role': users[username]['role'],
            'registered': users[username]['registered'],
            'gameInstalled': users[username]['gameInstalled']
        }
    })

# Получить всех пользователей (только для админа)
@app.route('/api/users', methods=['POST'])
def get_users():
    data = request.json
    adminUsername = data.get('adminUsername')
    adminPassword = data.get('adminPassword')
    
    users = load_users()
    
    # Проверка админа
    if adminUsername not in users or users[adminUsername]['role'] != 'admin':
        return jsonify({'success': False, 'error': 'Доступ запрещен'}), 403
    
    if users[adminUsername]['password'] != hash_password(adminPassword):
        return jsonify({'success': False, 'error': 'Доступ запрещен'}), 403
    
    # Убираем пароли из ответа
    safe_users = []
    for u in users.values():
        safe_users.append({
            'username': u['username'],
            'email': u['email'],
            'role': u['role'],
            'registered': u['registered'],
            'lastLogin': u['lastLogin'],
            'gameInstalled': u['gameInstalled']
        })
    
    return jsonify({'success': True, 'users': safe_users})

# Обновить роль пользователя
@app.route('/api/update-role', methods=['POST'])
def update_role():
    data = request.json
    adminUsername = data.get('adminUsername')
    adminPassword = data.get('adminPassword')
    targetUsername = data.get('targetUsername')
    newRole = data.get('newRole')
    
    users = load_users()
    
    if adminUsername not in users or users[adminUsername]['role'] != 'admin':
        return jsonify({'success': False, 'error': 'Доступ запрещен'}), 403
    
    if users[adminUsername]['password'] != hash_password(adminPassword):
        return jsonify({'success': False, 'error': 'Доступ запрещен'}), 403
    
    if targetUsername not in users:
        return jsonify({'success': False, 'error': 'Пользователь не найден'}), 404
    
    users[targetUsername]['role'] = newRole
    save_users(users)
    
    return jsonify({'success': True, 'message': 'Роль обновлена'})

# Обновить статус установки игры
@app.route('/api/update-installed', methods=['POST'])
def update_installed():
    data = request.json
    username = data.get('username')
    installed = data.get('installed')
    
    users = load_users()
    
    if username not in users:
        return jsonify({'success': False, 'error': 'Пользователь не найден'}), 404
    
    users[username]['gameInstalled'] = installed
    save_users(users)
    
    return jsonify({'success': True})

# Получить онлайн игроков (кто заходил за последние 2 часа)
@app.route('/api/online', methods=['GET'])
def get_online():
    users = load_users()
    now = datetime.now()
    online = []
    
    for u in users.values():
        if u['lastLogin']:
            last = datetime.fromisoformat(u['lastLogin'])
            if now - last < timedelta(hours=2):
                online.append({
                    'username': u['username'],
                    'role': u['role']
                })
    
    return jsonify({'online': online, 'count': len(online)})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
