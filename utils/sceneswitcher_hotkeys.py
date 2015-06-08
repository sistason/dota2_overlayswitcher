import time
import win32api

class HotKeySwitcher():

    def press_key(self, hexKeyCode):
        win32api.keybd_event(hexKeyCode, 0x0, 0)

    def release_key(self, hexKeyCode):
        win32api.keybd_event(hexKeyCode, 0x0, 0x0002)

    def send_keys(self, keys):
        for k in keys:
            self.press_key(k)
            time.sleep(0.05)    #OBS needs this! 0.01 is not enough

        for k in keys:
            self.release_key(k)
            
    def switch_to_scene(self, scene):
        hotkey_sequence = self.settings.HOTKEYS.get(scene, [])
        self.send_keys(hotkey_sequence)
        self._overlayswitcher.active_scene = scene  #Open Loop
        
    def update_scenes(self):
        # Open Loop Control only, no backchannel available
        return

    def start(self):
        return

    def stop(self):
        return
        
    def __init__(self, settings):
        self.settings = settings
