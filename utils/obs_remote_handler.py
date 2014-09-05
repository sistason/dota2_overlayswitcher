import websocket
import json
import thread
import time

class OBSRemoteWSHandler():
    """Incomplete Handler to talk to OBSRemote by websocket.
    
    But apparently, the only complete websocket-implementation
    is in Python3. So no. Not gonna happen now ;)"""
    
    def on_message(self, ws, message):
        print "Message:", message

    def on_error(self, ws, error):
        print "Error:", error

    def on_close(self, ws):
        print "### closed ###"

    def on_open(self, ws):
        data = {"request-type":'GetVersion'}
        self.send(data)
        time.sleep(3)
        data = {"request-type":'GetAuthRequired'}
        self.send(data)
        #thread.start_new_thread(run, ())
    def send(self, data):
        if not type(data) == dict or not data:
            return False

        data['message-id'] = self.id
        self.id += 1

        data = self.json_encoder.encode(data)
        self.ws.send(data)

    def authenticate(self):
        print 'authenticate not yet implemented'

    def __init__(self, url, port, auth):
        self.json_encoder = json.JSONEncoder()
        self.password = auth

        websocket.enableTrace(True)
        self.ws = websocket.WebSocketApp("ws://{0}:{1}".format(url, port),
                                  on_message=self.on_message,
                                  on_error = self.on_error,
                                  on_close = self.on_close,
                                  on_open = self.on_open,
                                  header = ['Protocol: obsapi'])
                            #FIXME: websocket0.16 has no protocol
                            #       option. Fail because of this?
        self.id = 1
        self.ws.run_forever()

if __name__ == '__main__':
    handler = OBSRemoteWSHandler('127.0.0.1', 4444, 'bvijkaxbfiwtafafas8f')
    time.sleep(5)
