import websocket
import json
import time

from threading import Thread

class OBSRemoteWSHandler():
    """Handler to talk to OBSRemote by websocket.
    
    Handles authentication, SceneChanges and SceneUpdates
    """

    def switch_to_scene(self, scene):
        # Set the current scene
        data = {"request-type":'SetCurrentScene', 'scene-name':scene}

        self.send(data)
 
    def on_message(self, ws, message):
        """ Store new information for the overlayswitcher"""

        data = self.json_decoder.decode(message)
        if data.get('authRequired','False') == 'True':
            self.authenticate()
        if data.get('update-type','') == 'StreamStatus':
            pass
        if type(data.get('scenes',None)) == list:
            pass
#            print data.get('current-scene','')
#            print '\n'.join(i['name'] for i in data['scenes'])

        if data.has_key('current-scene'):
            current_scene = data.get('current-scene')
            self.update_scenes(current_scene)
            
    def update_scenes(self, current_scene):
        self._overlayswitcher.active_scene = current_scene
        self.updated_scenes = True

    def on_error(self, ws, error):
        print "Error in the OBS Remote Handler:", error

    def on_open(self, ws):
        data = {"request-type":'GetSceneList'}
        self.send(data)
        data = {"request-type":'GetAuthRequired'}
        self.send(data)

    def send(self, data):
        if not type(data) == dict or not data:
            return False
        data = self.json_encoder.encode(data)
        self.ws.send(data)

    def authenticate(self):
        #TODO: Authentication
        print 'authenticate not yet implemented'

    def __init__(self, url, auth, overlayswitcher):
        self.json_encoder = json.JSONEncoder()
        self.json_decoder = json.JSONDecoder()
        self.password = auth
        self._overlayswitcher = overlayswitcher
        self.updated_scenes = False #have the scenes been updated yet?

        #websocket.enableTrace(True)
        self.ws = websocket.WebSocketApp("ws://{0}/".format(url),
                                  on_message=self.on_message,
                                  on_error = self.on_error,
                                  on_open = self.on_open,
                                  header = ['Sec-WebSocket-Protocol: obsapi'])
        self.thread = Thread(target=self.ws.run_forever, args=())
        self.thread.start()
        timeout = 0
        while not self.updated_scenes and timeout < 10:
            time.sleep(0.5)
            timeout += 1
        if timeout >= 10:
            print 'No Data received by OBSRemote for 5 seconds! Connection Problems!'
            self.ws.close()
        else:
            print 'Websocket created'

if __name__ == '__main__':
    from settings import OBS_REMOTE_URL, OBS_REMOTE_PASS
    import time
    
    handler = OBSRemoteWSHandler(OBS_REMOTE_URL, OBS_REMOTE_PASS, None)
    print 'OBS Remote works!'
    handler.ws.close()