from flask import Flask, jsonify, render_template, request
import multiprocessing as mp
import numpy as np
import ctypes
import time

delay = 5

# ============================================================================
# Web server process (same code as OpenVNAVI/code/main.py, except host IP)
# ============================================================================
webServer = Flask(__name__)
webServer.debug = True


@webServer.route("/")
def serve():
    """ Web root. """
    return render_template('index.html')


@webServer.route('/_send_motors', methods=["PUT", "POST"])
def send_motors():

    """ Handles AJAX requests. """

    requestJson = request.get_json()

    # send to renderer process
    webServer.extensions['queue'].put(requestJson)
    return ""


@webServer.route('/_get_render_data')
def get_render_data():
    retVal = {"PWM": shared_PWM.tolist(), "depth": shared_depthImg.tolist()}
    return jsonify(**retVal)

def webserverProcess(webQueue, ipcQueue):

    """ Entry point for the web server process. """
    if not hasattr(webServer, 'extensions'):
        webServer.extensions = {}
    webServer.extensions['queue'] = webQueue

    webServer.run(use_reloader=False)

    while True:
        ipcCommand = ipcQueue.get()
        if ipcCommand == "terminate":
            print "[WebServer] shutdown requested"
            return

# ============================================================================
# Worker process
# ============================================================================
def workerProcess(webQueue, ipcQueue):
    i = 0
    while True:

        if not webQueue.empty():
            requestJson = webQueue.get()

            print "Received from web:\n%s" % requestJson

            if "motors" in requestJson:
                PWMFromWeb = np.array(requestJson["motors"])
                shared_PWM[:] = PWMFromWeb[:]

        i += delay
        time.sleep(delay)


# ============================================================================
# Entry point
# ============================================================================

if __name__ == "__main__":
    global shared_depthImg, shared_PWM

    # for inter-process communication
    webQueue = mp.Queue()
    ipcQueue = mp.Queue()

    # shared global variables
    # NOTE: ctypes will complain about PEP 3118, but it's fine. 
    # (Known ctypes bug: http://stackoverflow.com/questions/4964101/pep-3118-warning-when-using-ctypes-array-as-numpy-array)
    shared_depthImg_base = mp.Array(ctypes.c_double, 8 * 16)
    shared_depthImg = np.ctypeslib.as_array(shared_depthImg_base.get_obj())
    shared_depthImg = shared_depthImg.reshape(8, 16)

    shared_PWM_base = mp.Array(ctypes.c_double, 8 * 16)
    shared_PWM = np.ctypeslib.as_array(shared_PWM_base.get_obj())
    shared_PWM = shared_PWM.reshape(8, 16)

    p_webserver = mp.Process(target=webserverProcess, args=(webQueue, ipcQueue))
    p_webserver.start()

    p_worker = mp.Process(target=workerProcess, args=(webQueue, ipcQueue))
    p_worker.start()
