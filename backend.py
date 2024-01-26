import cozmo
from flask import Flask, Response, send_from_directory
import cv2
import threading
import numpy as np
import mimetypes

app = Flask(__name__)
video_frame = None
lock = threading.Lock()
queue = []
def cozmo_program(robot: cozmo.robot.Robot):
    global video_frame, lock
    global queue

    # Enable camera feed
    robot.camera.image_stream_enabled = True

    while True:
        frame = robot.world.latest_image
        if frame is not None:
            np_image = np.array(frame.raw_image)
            with lock:
                video_frame = np_image
        if len(queue) > 0:
            robot.abort_all_actions()
            command = queue.pop(0)
            if command == 'left': robot.turn_in_place(cozmo.util.degrees(50))
            elif command == 'right': robot.turn_in_place(cozmo.util.degrees(-50))
            elif command == 'forward': robot.drive_straight(cozmo.util.distance_mm(50), cozmo.util.speed_mmps(50))
            elif command == 'backward': robot.drive_straight(cozmo.util.distance_mm(-50), cozmo.util.speed_mmps(50))
            elif command == 'up': robot.set_lift_height(1.0, in_parallel=True)
            elif command == 'down': robot.set_lift_height(0.0, in_parallel=True)
            elif command == 'lookup': robot.set_head_angle(cozmo.util.degrees(robot.head_angle.degrees+10), in_parallel=True)
            elif command == 'lookdown': robot.set_head_angle(cozmo.util.degrees(robot.head_angle.degrees-10), in_parallel=True)



cozmo_thread = threading.Thread(target=cozmo.run_program, args=(cozmo_program,))
cozmo_thread.start()


def generate():
    global video_frame, lock
    while True:
        with lock:
            if video_frame is None:
                continue
            (flag, encodedImage) = cv2.imencode(".jpg", video_frame)
            if not flag:
                continue

        yield(b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + bytearray(encodedImage) + b'\r\n')

@app.route('/video_feed')
def video_feed():
    return Response(generate(), mimetype = "multipart/x-mixed-replace; boundary=frame")

@app.route('/')
def index():
    return Response(open('index.html').read(), mimetype="text/html")


@app.route('/left', methods=['POST'])
def left():
    queue.append('left')
    return Response('left')

@app.route('/right', methods=['POST'])
def right():
    queue.append('right')
    return Response('right')

@app.route('/forward', methods=['POST'])
def forward():
    queue.append('forward')
    return Response('forward')

@app.route('/backward', methods=['POST'])
def backward():
    queue.append('backward')
    return Response('backward')


@app.route('/up', methods=['POST'])
def up():
    queue.append('up')
    return Response('up')

@app.route('/down', methods=['POST'])
def down():
    queue.append('down')
    return Response('down')

@app.route('/lookup', methods=['POST'])
def lookup():
    queue.append('lookup')
    return Response('lookup')

@app.route('/lookdown', methods=['POST'])
def lookdown():
    queue.append('lookdown')
    return Response('lookdown')

# allow files to be read from ./icons/
@app.route('/icons/<path:path>')
def send_js(path):
    return send_from_directory('icons', path + ".svg")






if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, threaded=True)
