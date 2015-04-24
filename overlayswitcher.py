#!/usr/bin/env python

import win32gui, win32con, win32ui
import time

import cv2

import tempfile
import os

import utils.sceneswitcher_obsremote, utils.sceneswitcher_hotkeys

from utils.ols_tests import TestGameEnv, DotaLogWatcher
from utils import settings

class OverlaySwitcher(TestGameEnv):
    """Program to switch scenes depending on the state Dota 2 is in.
    
    Takes screenshots of Dota 2, determines the current state with this
    and the console-logfile and changes scenes via hotkeys or websocket
    (OBSRemote) on changes of state.
    
    https://github.com/sistason/dota2_overlayswitcher
    Dota 2 must be in Borderless Window Mode :(
    """

    THRESH_DRAFT = 50 
    THRESH_INGAME = 65
    THRESH_LOADINGMAP = 10
    COLOR_BGR_SCORE = (26, 23, 22)
    COLOR_HSV_MENU = ((15,10,10),(41,255,255))
    COLOR_BGR_LOADINGPLAYERS_RED = ((0,0,100),(50,50,255))
    COLOR_RGB_LOADINGPLAYERS_RED = ((100,0,0),(255,50,50))
    COLOR_RGB_LOADINGPLAYERS_GREEN = ((0,100,0),(50,255,50))


    def __init__(self, bare=False, path=''):
        self.base_state = ''    #State of the log-file
        self.dota_hwnd = 0
        self._work_lock = False
        self._terminate = False

        self.active_scene = ''
        self.OVERLAYS = settings.OVERLAYS
        self.LOCKED_SCENES = settings.LOCKED_SCENES
        self.WHITELIST_SCENES = settings.WHITELIST_SCENES

        if settings._USE_HOTKEYS:
            self.switch_to_scene = utils.sceneswitcher_hotkeys.switch_to_scene
        else:
            _h = utils.sceneswitcher_obsremote.OBSRemoteWSHandler
            self.obsremotehandler = _h(settings.OBS_REMOTE_URL, settings.OBS_REMOTE_PASS, self)
            if not self.obsremotehandler.updated_scenes:
                print 'OverlaySwitcher not created, error with the OBS Remote'
                del self
                return
            self.switch_to_scene = self.obsremotehandler.switch_to_scene
            

        if not self.init_dota_log(path):
            print 'OverlaySwitcher not created, error with the Dota 2 logfile'
            del self
            return
        print 'OverlaySwitcher sucessfully created'
        
    def init_dota_log(self, path=''):
        """Try tp open the Dota 2 logfile"""
        if not path:
            path = settings.DOTA_CONSOLE_DIR
        if not os.access(path, os.R_OK):
            print 'Dota 2 Logfile ("{0}") not readable!'.format(path)
            print 'Have you enabled the logfile in Dota 2 via "con_logfile <path>"?'
            return
        
        self.dota_log_watcher = DotaLogWatcher(path, self)
       
        return True

    def obs_switch(self, dota_game_state):
        """Get scene for active game state and switch to the scene."""
        new_obs_scene = self.OVERLAYS.get(dota_game_state, '')
        if not new_obs_scene:
            print 'Warning! Key for state {0} not yet set! Not pressing anything...'.format(dota_game_state)
            return
        # Scene is already active
        if new_obs_scene == self.active_scene: 
            return
        # Scene is neither locked, or is whitelisted
        if self.active_scene in self.LOCKED_SCENES and self.LOCKED_SCENES or\
           self.active_scene not in self.WHITELIST_SCENES and self.WHITELIST_SCENES:
           return
        self.active_scene = new_obs_scene
        
        self.switch_to_scene(new_obs_scene)
        print "Dota state is now {0}, OBS scene changed to {1}".format(game_state, new_obs_scene)
        
    def work(self):
        """Main-loop: take screenshot, determine the game state and switch.

        Since it is called when the scene changes via the log-watcher, it
        needs to be locked..."""
        while self._work_lock:
            time.sleep(0.016)
        self._work_lock = True
        img = self.get_dota_screenshot()

        game_state = self.determine_game_state(img)
        if not game_state:
            print 'unsure or in transition'
            self._work_lock = False
            return
        
        self.obs_switch(game_state)
        self._work_lock = False
        
    def spin(self):
        """Set the Interval here for the main-loop.

        Faster loops cause linarly more computation power 
        (screenshots + analysis)
        """
        interval = 0.5
        try:
            while not self._terminate:
                next_ = time.time()+interval

                self.work()

                to_sleep_ = next_ - time.time()
                if to_sleep_ > 0:
                    time.sleep(to_sleep_)
        except Exception, e:
            print e
            time.sleep(10)  # To read the Exception ;)

        self.dota_log_watcher.stop()
        self._terminate = False

    def stop(self):
        self._terminate = True
        
    def get_dota_hwnd(self):
        """Get the current Dota 2 Windows window number."""
        if self.dota_hwnd and win32gui.GetWindowText(self.dota_hwnd) == 'DOTA 2':
            return self.dota_hwnd
    
        # Cycle through all windows to find the Dota window
        # Yes, this is the Windows-way, apparently.
        # Yes, it fails if you have a directory open named "DOTA 2" etc...
        hwnd = []
        def search_dota(hwnd_, results):
            if win32gui.GetWindowText(hwnd_) == 'DOTA 2':
                hwnd.append(hwnd_)
        win32gui.EnumWindows(search_dota, None)
        
        # If Dota is not yet open, wait for it recursively
        if not hwnd:
            print 'Dota is not yet running'
            time.sleep(1)
            return self.get_dota_hwnd()

        self.dota_hwnd = hwnd[0]
        return self.dota_hwnd
        
    def get_dota_screenshot(self):
        """Take a screenshot of the Dota 2 window and load it with OpenCV.
        
        This is basically Copy&Paste from Stackoverflow, as you may see from
        the complexity/bloatiness of the beautiful Windows code...
        Things to note:
          - width or height <= 0 means fullscreen application
          - if Dota is at a lower resolution than your monitor(s), it gets
            interesting with the virtual screen parameters l and t. Basically
            l=left, t=top distance from virtual to displayed screen. Well...
          - Save on disk/RAM and load with cv2 is way faster than (manual) 
            conversion in memory unless you find the perfect numpy-function
            for that. ...which I haven't.
        """
        hwnd = self.get_dota_hwnd()

        l, t, w, h = win32gui.GetWindowRect(hwnd)
        if w <= 0 or h <= 0:
            print 'Dota 2 is launched in Fullscreen! Cannot get image! Please launch Dota 2 in Window or Borderless Window mode'
            return     
        
        wDC = win32gui.GetWindowDC(hwnd)
        dcObj=win32ui.CreateDCFromHandle(wDC)
        cDC=dcObj.CreateCompatibleDC()
        dataBitMap = win32ui.CreateBitmap()
        dataBitMap.CreateCompatibleBitmap(dcObj, w, h)
        cDC.SelectObject(dataBitMap)
        cDC.BitBlt((0,0),(w, h) , dcObj, (0,0), win32con.SRCCOPY)
        
        t_ = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
        t_.close()
        dataBitMap.SaveBitmapFile(cDC, t_.name)
        
        # Free Resources
        dcObj.DeleteDC()
        cDC.DeleteDC()
        win32gui.ReleaseDC(hwnd, wDC)
        win32gui.DeleteObject(dataBitMap.GetHandle())
        
        img = cv2.imread(t_.name)
        try:
            os.remove(t_.name)
        except:
            pass
        img = img[:h-t, :w-l] #if dota-res < monitor-res, it bugs out
        return img
        

if __name__ == '__main__':
    switcher = OverlaySwitcher()
    switcher.spin()
