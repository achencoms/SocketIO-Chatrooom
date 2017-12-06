from flask import Flask, render_template, session, redirect, url_for, request
from flask_socketio import SocketIO, send, emit, join_room, leave_room, rooms, disconnect

import os, json

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(32);
socketio = SocketIO(app)
users = {}

@app.route('/')
def home():
    if 'user' in session:
        return redirect(url_for("chat"))
    return render_template("enter.html")

@app.route('/enter', methods=['POST'])
def index():
    d = request.form
    user = d['user']
    if 'user' in session:
        return redirect(url_for("chat"))
    if user not in users:
        users[user] = ""
        session['user'] = user
        return redirect(url_for("chat"))
    return redirect(url_for("home"))

@app.route('/chatroom')
def chat():
    if 'user' not in session:
        return redirect(url_for("home"))
    return render_template('index.html')

@app.route('/disconnect')
def disconnect():
    users.pop(session['user'],None)
    session.pop('user',None)
    return redirect(url_for("home"))

@app.route("/checkName", methods=["GET"])
def checkName():
    d = request.args
    name = d['name']
    out = {"check" : name in users}
    return json.dumps(out)

@socketio.on('message', namespace="/chatroom")
def handle_message(message):
    if message['room'] in users.values():
        emit('userMessage',{'m' : message['m'], 'user' : session['user'], 'sid' : request.sid}, room=message['room'])
    else:
        emit('userMessage',{'m' : message['m'], 'user' : session['user']}, room=message['room'])

@socketio.on('chatUser', namespace="/chatroom")
def chatWith(data):
    join_room(data['user'])

@socketio.on('connect', namespace="/chatroom")
def test_connect():
    users[session['user']] = request.sid
    join_room("general")
    for name,sid in users.items():
        userDict = dict([(n,s) for n,s in users.items() if n != name])
        emit("users_online", {'users' : userDict}, room = sid)

@socketio.on('join', namespace="/chatroom")
def on_join(data):
    room = data['room']
    if room not in rooms():
        join_room(room)
        roomList = [room for room in rooms() if room != request.sid]
        emit("room_check", {
            "rooms" : roomList
        })
        #send("Your current rooms are: " + str(roomList))
        emit("message", {'m': session['user'] + " has joined <b>" + room + "</b>.", 'room' : room}, room = room)

@socketio.on('leave', namespace="/chatroom")
def on_leave(data):
    username = session['user']
    room = data['room']
    leave_room(room)
    emit("message",{'m' : username + 'has left the room.', 'room' : room},room = room)

@socketio.on('disconnect', namespace="/chatroom")
def on_disconnect():
    disconnect()
    for name,sid in users.items():
        userDict = dict([(n,s) for n,s in users.items() if n != name])
        emit("users_online", {'users' : userDict}, room = sid)

'''
@socketio.on('my broadcast event')
def test_message(message):
    emit('my response', {'data': message['data']}, broadcast=True)

'''
if __name__ == '__main__':
    app.debug = True
    socketio.run(app)
