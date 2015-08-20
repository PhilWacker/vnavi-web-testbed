from flask import Flask, jsonify, render_template, request
import multiprocessing as mp
import numpy as np

import time

delay = 5

webServer = Flask(__name__)
webServer.debug = True


@webServer.route("/")
def serve():
    return render_template('index.html')


@webServer.route('/_send_motors', methods=["PUT", "POST"])
def send_motors():
    requestJson = request.get_json()
    webServer.extensions['queue'].put(requestJson)

    retVal = {"message": "hi from Flask"}
    return jsonify(**retVal)


def webserverProcess(queue):
    if not hasattr(webServer, 'extensions'):
        webServer.extensions = {}
    webServer.extensions['queue'] = queue

    webServer.run(use_reloader=False)


def workerProcess(queue):
    i = 0
    while True:

        if not queue.empty():
            requestJson = queue.get()

            frame = np.array(requestJson["motors"])
            mode = requestJson["mode"]

            print "Set mode: %s" % mode

            if mode == "web":
                print frame
        else:
            print "%d: no data" % i

        i += delay
        time.sleep(delay)


if __name__ == "__main__":
    q = mp.Queue()

    p_webserver = mp.Process(target=webserverProcess, args=(q, ))
    p_webserver.start()

    p_worker = mp.Process(target=workerProcess, args=(q, ))
    p_worker.start()
