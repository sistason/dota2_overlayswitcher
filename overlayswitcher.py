#!/usr/bin/env python

import win32gui, win32con, win32ui
import time

import cv2

import tempfile
import os

from utils.send_hotkeys import send_keys
from utils.ols_tests import TestGameEnv
from utils.settings import *

class OverlaySwitcher(TestGameEnv):
    """Program to send hotkeys dependant on the state Dota 2 is in.
    
    Takes screenshots of Dota 2, determines the current state with this
    and the console-logfile and sends hotkey-presses on changes of state.
    
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
        self.prev_state = None
        self.base_state = ''
        self.dota_hwnd = 0
        self.OVERLAYS = OVERLAYS
#         if not bare:
#            self.load_templates()
        self.init_dota_log(path)
        
    def init_dota_log(self, path_=''):
        """Try tp open the Dota 2 logfile"""
        if not path_:
            path_ = os.path.join(DOTA_DIR, 'console.log')
        if not os.access(path_, os.R_OK):
            print 'Dota 2 Logfile ("{0}") not readable!'.format(path_)
            print 'Have you enabled the logfile in Dota 2 via "con_logfile <path>"?'
            return
        self.dota_log = open(path_, 'r')
        return True
        
        
    def load_templates(self):
        """Load the templates matching the current Dota 2 resolution"""
        # Load Templates
        l, t, width, height = win32gui.GetWindowRect(self.get_dota_hwnd())
        try:
            t_menu = cv2.imread('templates/settings-icon-threshed.png', 0)
            t_draft = cv2.imread('templates/chat-icon-threshed.png', 0)
            t_ingame = cv2.imread('templates/minimize-icon-threshed.png', 0)
            t_loadingmap = cv2.imread('templates/loadingmap-icon-threshed.png', 0)
            t_loadingplayers_l = cv2.imread('templates/loadingplayers_loading-icon-threshed.png', 0)    
            t_loadingplayers_r = cv2.imread('templates/loadingplayers_ready-icon-threshed.png', 0)
            # All Players Failed, while no one is loading any more is left out here. Not really necessary...
        except Exception, e:
            print 'Apparently, not all templates are accessable! Exception was:', e
            return ''
            
        #TODO: Templates in allen Auflosungen machen
        #TODO: np.uint8() == cv2.threshold?
        _, self.template_menu = cv2.threshold(t_menu, 1, 255, cv2.THRESH_BINARY)
        _, self.template_draft = cv2.threshold(t_draft, 1, 255, cv2.THRESH_BINARY)
        _, self.template_ingame = cv2.threshold(t_ingame, 1, 255, cv2.THRESH_BINARY)
        _, self.template_loadingmap = cv2.threshold(t_loadingmap, 1, 255, cv2.THRESH_BINARY)
        _, self.template_loadingplayers_loading = cv2.threshold(t_loadingplayers_l, 1, 255, cv2.THRESH_BINARY)
        _, self.template_loadingplayers_ready  =  cv2.threshold(t_loadingplayers_r, 1, 255, cv2.THRESH_BINARY)

    def work(self):
        """Main-loop: take screenshot, determine the game state and switch."""
        img = self.get_dota_screenshot()

        game_state = self.determine_game_state(img)
        if not game_state:
            print 'unsure or in transition'
            return
        
        if game_state != self.prev_state:
            print "### --- changed to {0} --- ###".format(game_state)
            self.obs_switch(game_state)
            self.prev_state = game_state
        
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
          - width or height < 0 means fullscreen application
          - if Dota is at a lower resolution than your monitor(s), it gets
            interesting with the virtual screen stuff l and t. Basically
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
        
    def obs_switch(self, game_state):
        """Send necessary hotkey to switch to the state."""
        scene_hotkey = self.OVERLAYS.get(game_state, [])
        if not scene_hotkey:
            print 'Warning! Key for state {0} not yet set! Not pressing anything...'
            return
        send_keys(scene_hotkey)
        
    def spin(self):
        """Set the Interval here for the main-loop."""
        interval = 0.1
        try:
            while True:
                next_ = time.time()+interval
                self.work()
                #print time.time()-(next_-interval)

                to_sleep_ = next_ - time.time()
                if to_sleep_ > 0:
                    time.sleep(to_sleep_)
        except Exception, e:
            print e
            time.sleep(10)  # To read the Exception ;)

        self.dota_log.close()

if __name__ == '__main__':
    switcher = OverlaySwitcher()
    switcher.spin()
