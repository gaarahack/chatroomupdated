from flask import Flask, render_template, request, redirect, url_for, session
from flask_socketio import SocketIO, join_room, leave_room, send

app = Flask(__name__)
app.config['SECRET_KEY'] = 'alkdnfencakenan'
socketio = SocketIO(app)

active_rooms = {}
blocked_users = set()
MODERATOR_PASSWORD = 'lit3x7' 

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/chat/<room_id>')
def chat(room_id):
    username = request.args.get('username')
    if 'rahul' in username.lower():
        return "Username should not contain 'rahul'", 400
    if username in blocked_users:
        return "You are blocked from the chat", 403
    session['username'] = username
    return render_template('chat.html', room_id=room_id)

@app.route('/moderator')
def moderator():
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    return render_template('moderator.html', rooms=active_rooms, blocked_users=blocked_users)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        password = request.form['password']
        if password == MODERATOR_PASSWORD:
            session['logged_in'] = True
            return redirect(url_for('moderator'))
        else:
            return "Invalid password", 403
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('home'))

@app.route('/block_user', methods=['POST'])
def block_user():
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    username = request.form['username']
    blocked_users.add(username)
    return redirect(url_for('moderator'))

@app.route('/join_room', methods=['POST'])
def join_room_as_moderator():
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    room = request.form['room']
    # Logic to join the room as a moderator
    return redirect(url_for('moderator'))

@socketio.on('join')
def handle_join(data):
    username = data['username']
    room_id = data['room_id']
    
    if 'rahul' in username.lower() or username in blocked_users:
        return

    join_room(room_id)
    
    if room_id not in active_rooms:
        active_rooms[room_id] = []
    if username not in active_rooms[room_id]:
        active_rooms[room_id].append(username)
    
    message = f'{username} has joined the room.'
    send({'message': message}, room=room_id)
    print(message)  

@socketio.on('leave')
def handle_leave(data):
    username = data['username']
    room_id = data['room_id']
    leave_room(room_id)
    if room_id in active_rooms and username in active_rooms[room_id]:
        active_rooms[room_id].remove(username)
    send(f'{username} has left the room.', room=room_id)

@socketio.on('message')
def handle_message(data):
    username = data['username']
    room_id = data['room_id']
    message = data['message']
    
    if username in blocked_users:
        return
    
    send({'username': username, 'message': message}, room=room_id)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=80, debug=True)
