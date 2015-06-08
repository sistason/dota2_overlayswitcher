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
        try:
            self.ws.send(data)
        except:
            pass

    def authenticate(self):
        #TODO: Authentication
        print 'authenticate not yet implemented'

    def start(self):
        self.ws = websocket.WebSocketApp("ws://{0}/".format(self.obsurl),
                                  on_message=self.on_message,
                                  on_error = self.on_error,
                                  on_open = self.on_open,
                                  header = ['Sec-WebSocket-Protocol: obsapi'])
        websocket.setdefaulttimeout(5)
        self.thread = Thread(target=self.ws.run_forever, name='thread-overlayswitcher.sceneswitcher.obsremote.ws.fun_forever')
        self.thread.start()

    def stop(self):
        self.connected = False
        self.ws.close()
        self.thread._Thread__stop()
        
    def on_message(self, ws, message):
        """ Store new information for the overlayswitcher"""

        data = self.json_decoder.decode(message)
        if data.get('authRequired','False') == 'True':
            self.authenticate()
        if data.get('update-type','') == 'StreamStatus':
            self.stats = data
        if data.has_key('streaming'):
            pass
        if type(data.get('scenes',None)) == list:
            pass
#            print data.get('current-scene','')
#            print '\n'.join(i['name'] for i in data['scenes'])

        if data.has_key('current-scene'):
            current_scene = data.get('current-scene')
            self._overlayswitcher.active_scene = current_scene
        
    def on_error(self, ws, error):
        print "Error in the OBS Remote Handler:", error
        self.stop()

    def on_open(self, ws):
        if ws is None or ws.sock is None:
            print 'OBSRemote Socket Error!'
            return
        self.connected = ws.sock.connected
        if not self.connected:
            print 'Could not establish a connection to OBSRemote! Aborting'
            return
        else:
            print 'Websocket created'

        self.update_scenes()
        data = {"request-type":'GetAuthRequired'}
        self.send(data)

    def __init__(self, settings, overlayswitcher):
        self.json_encoder = json.JSONEncoder()
        self.json_decoder = json.JSONDecoder()
        self.password = settings.OBS_REMOTE_PASS
        self.obsurl = settings.OBS_REMOTE_URL
        self._overlayswitcher = overlayswitcher
        self.obs_streaming = 0
        self.connected = False  #have we got a message yet?

        #websocket.enableTrace(True)
        self.start()

if __name__ == '__main__':
    import settings
    import time
    import sys
    class _():  #Dummy Overlayswitcher to avoid exceptions in updates()
        active_scene=None
    dummy_ols = _()
    if len(sys.argv) > 1:
        settings.OBS_REMOTE_URL = sys.argv[1]
    handler = OBSRemoteSwitcher(settings, dummy_ols)
    print 'OBS Remote works!'
    handler.ws.close()
