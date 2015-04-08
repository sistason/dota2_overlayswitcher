import websocket
import json
import time

from threading import Thread

class OBSRemoteSwitcher():
    """Handler to talk to OBSRemote by websocket.
    
    Handles authentication, SceneChanges and SceneUpdates
    """

    def switch_to_scene(self, scene):
        # Set the current scene
        data = {"request-type":'SetCurrentScene', 'scene-name':scene}
        self.send(data)
             
    def update_scenes(self):
        data = {"request-type":'GetSceneList'}
        self.send(data)
        
    def send(self, data):
        if not type(data) == dict or not data:
            return False
        data = self.json_encoder.encode(data)
        self.ws.send(data)

    def authenticate(self):
        #TODO: Authentication
        print 'authenticate not yet implemented'
        
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
            self._overlayswitcher.active_scene = current_scene
            self.updated_scenes = True        
        
    def on_error(self, ws, error):
        print "Error in the OBS Remote Handler:", error

    def on_open(self, ws):
        self.update_scenes()
        data = {"request-type":'GetAuthRequired'}
        self.send(data)

    def __init__(self, settings, overlayswitcher):
        self.json_encoder = json.JSONEncoder()
        self.json_decoder = json.JSONDecoder()
        self.password = settings.OBS_REMOTE_PASS
        self._overlayswitcher = overlayswitcher
        self.updated_scenes = False #have the scenes been updated yet?

        #websocket.enableTrace(True)
        self.ws = websocket.WebSocketApp("ws://{0}/".format(settings.OBS_REMOTE_URL),
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
    import settings
    import time
    class _():  #Dummy Overlayswitcher to avoid exceptions in updates()
        active_scene=None
    dummy_ols = _()
    handler = OBSRemoteSwitcher(settings, dummy_ols)
    print 'OBS Remote works!'
    handler.ws.close()