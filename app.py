from flask import Flask, render_template, session, redirect, url_for, request
from flask_socketio import SocketIO, send, emit, join_room, leave_room, rooms

import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(32);
socketio = SocketIO(app)

@app.route('/')
def home():
    return render_template('enter.html')

@app.route('/enter', methods=['POST'])
def index():
    d = request.form
    session['user'] = d["user"]
    return redirect(url_for("chat"))

@app.route('/chatroom')
def chat():
    if 'user' not in session:
        return redirect(url_for("home"))
    return render_template('index.html')

@socketio.on('message', namespace="/chatroom")
def handle_message(message):
    if len(rooms()) == 2:
        emit('userMessage',{'m' : message, 'user' : session['user']},room="general")
    else:
        for i in rooms():
            if i != request.sid:
                emit('userMessage',{'m' : message, 'user' : session['user']},room = i)

@socketio.on('connect', namespace="/chatroom")
def test_connect():
    print "client has connected\n\n"
    join_room("general")

@socketio.on('join', namespace="/chatroom")
def on_join(data):
    room = data['room']
    join_room(room)
    send("Your current rooms are: " + str(rooms()))
    send(session['user'] + " has joined " + room + ".", room = room)
    emit("room_check", {
        "rooms" : [room for room in rooms() if room != request.sid]
    })

@socketio.on('leave')
def on_leave(data):
    username = data['username']
    room = data['room']
    leave_room(room)
    send(username + ' has left the room.', room=room)

'''
@socketio.on('my broadcast event')
def test_message(message):
    emit('my response', {'data': message['data']}, broadcast=True)

@socketio.on('connect')
def test_connect():
    emit('my response', {'data': 'Connected'})

@socketio.on('disconnect')
def test_disconnect():
    print('Client disconnected')
'''
if __name__ == '__main__':
    app.debug = True
    socketio.run(app)
