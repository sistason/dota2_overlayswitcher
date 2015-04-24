import cv2
import numpy as np
import pylab as pl

from threading import Thread
from time import sleep

class DotaLogWatcher():
    path = ''
    _thread = None
    _dota_log = None
    _overlayswitcher = None
    _active = True

    
    def __init__(self, path, overlayswitcher):
        self.path = path
        self._overlayswitcher = overlayswitcher
        self._dota_log = open(self.path, 'r+')
        self._thread = Thread(target=self._spin)
        self._thread.start()
        
    def stop(self):
        self._active = False
        sleep(0.5)
        if self._thread.is_alive:
            self._thread._Thread__stop()
        self._dota_log.close()
      
    def _spin(self):
        while self._active and not sleep(0.016):  #frame at 60fps
            new_content = self._dota_log.read()
            if new_content:
                prev_state_ = self._overlayswitcher.base_state
                self._update_state(new_content)
                if self._overlayswitcher.base_state != prev_state_:
                    self._overlayswitcher.work()
        
    def _update_state(self, new_content):
        for line in reversed(new_content.split('\n')):
            if line.startswith('Start of Dota'):
                self._overlayswitcher.base_state = 'MENU'
                return

            pos_rule = line.find('DOTA_GAMERULES_STATE_')
            if pos_rule >= 0:
                self._overlayswitcher.base_state = line[pos_rule+21:-1]
                return
        
        
class TestGameEnv():
    """Base Class for everything concerning actual Dota 2 processing
    """
    def __init__(self):
        pass

    def determine_game_state(self, img):
        """Determine which state Dota 2 is currently in.
        
        First, get the base_environment from the log file. This
        is accurate except it cannot check if the menu is up or not,
        so check this with the screenshot.
        """
        # Break if screen is blank
        if img is None or not img.any():
            return ''
     
        # Order-Dependencies:
        # scoreboard > loadingplayers (black top/bot-border)
        # draft, scoreboard, loadingplayers > ingame (minimize-icon)

        #Simple, distinct icon-searches
        if self.base_state == 'MENU' or self.test_menu(img):# or self.test_loadingscreen(img):
            return 'MENU'
        #self.plot_image(img)
        return self.base_state
        
        # ---------- Functions to determine complete state from screenshot ----
        # Reliant on templates and partly incomplete, so done by logfile
        # (I had everything finished before finding the logfile-mechanics...)
        
        if self.test_draft(img):
            return 'HERO_SELECTION'
        if self.test_loading_map(img):
            return 'INIT'
        if self.test_loading_players(img):
            return 'WAIT_FOR_PLAYERS_TO_LOAD'
            
        # Black area top or bot
        if self.test_score_or_loading(img):
            if self.test_scoreboard(img):
                return 'POST_GAME'
            if self.prev_env in ['loadingmap', 'transition_startofgame']:
                return 'transition_startofgame'
            if self.prev_env in ['ingame', 'transition_endofgame']:
                return 'transition_endofgame'
        
        if self.test_ingame(img):
            return 'ingame'
        return ''

    def test_score_or_loading(self, img):
        """Tests if there is a black border at the bottom

        Black border on the bottom is checked.
        Can happen in scoreboard and while player loading"""
        bottom_space = img[-100:].any(axis=1)
        # Amount of black lines (RGB = True True True = /3)
        empty_space = len(bottom_space[bottom_space==False])/3
        if empty_space >= 5:
                return True
        return False

    def test_loadingscreen(self, img):
        """Tests if Dota is in the loading screen
        
        Checks if the "Loading..." is there. Black-background around that
        """
        height, width = img.shape[:2]
        i_ = img[-width/100.0+width/20:-width/100.0, -height/100.0+height/20:-height/100.0]
        #self.plot_image(i_)
        
    def test_menu(self, img):
        """ Tests if Dota is in the menu

        Checks if the settings-icon is in the top left corner. The icon
        is symbolized by having a hole in the middle (the gear-symbol)."""
        height, width = img.shape[:2]

        #height/24 and width/16 crops only the icons
        img = img[:height/25.0, :width/16.0]

        # The icons are distinguishable by their special grey color
        img_hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        bot_grey, top_grey = self.COLOR_HSV_MENU
        img_thresh = cv2.inRange(img_hsv, bot_grey, top_grey)

        if not img_thresh.any():
            return False
        
        # Crop the image to only keep the icons
        left, right, top, bot = self.utils_find_topright_borders(img_thresh)
        if not left and not right and not top and not bot:
            print "Icon was not found! ?"
            self.plot_image(img_thresh)
            return False

        img_cropped = img_thresh[top:bot, left:right]
        height, width = img_cropped.shape[:2]
        
        # Check if a hole of (n+1)x(n+1) is in the middle of the img
        # n is appropriate to the whole size of the circle.
        n = np.floor(height/10.0)
        return not img_cropped[height/2-n:height/2+1+n, width/2-n:width/2+1+n].any()
        
    def utils_find_topright_borders(self, img):
        """Get the left, right, top and bottom borders of the rightmost icon in the image."""
        height, width = img.shape[:2]
        # Abort for Recursion
        if height < 5 or width < 5:
            return [0,0,0,0]
            
        right_border = width
        for i in xrange(width-1, 0, -1):
            if img[:,i].any():
                right_border = i+1
                break   
        left_border = 0
        for i in xrange(right_border-1, 0, -1):
            if not img[:,i].any():
                left_border = i+1
                break        
        top_border = 0
        for i in xrange(height):
            if img[i,:].any():
                top_border = i
                break   
        bot_border = height
        for i in xrange(top_border, height):
            if not img[i,:].any():
                bot_border = i
                break
        
        # if small area is found, noise is present. Try again with reduced image
        if right_border-left_border < width/10:
            return self.utils_find_topright_borders(img[:,0:right_border-1])
        if bot_border-top_border < height/10:
            return self.utils_find_topright_borders(img[top_border+1:,:])
        return left_border, right_border, top_border, bot_border


    def test_scoreboard(self, img):
        """ Tests if the scoreboard is on display
        
        Is done by selecting just the mid where the scoreboard will be, simplifying
        colors by kmeans and testing if most color is in "scoreboard-color" (the grey
        around the board. TODO: kmeans is waaay to computationally expensive"""
        height, width = img.shape[:2]
        img_scoreboard = img[height/7:-height/3, width/6:-width/6]
        height, width = img_scoreboard.shape[:2]
        img_scoreboard_bottom_bg_area = img_scoreboard[-(height/10):]

        Z = np.float32(img_scoreboard_bottom_bg_area.reshape((-1,3)))

        # define criteria, number of clusters(K) and apply kmeans()
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 5, 1.0)
        ret,label,center=cv2.kmeans(Z, 2, criteria, 5, cv2.KMEANS_RANDOM_CENTERS)

        # Now convert back into uint8, and make original image
        center = np.uint8(center)
        res = center[label.flatten()]
        
        blue = np.argmax(cv2.calcHist([res[:,0]], [0], None, [256], [0,256]))
        green =np.argmax(cv2.calcHist([res[:,1]], [0], None, [256], [0,256]))
        red  = np.argmax(cv2.calcHist([res[:,2]], [0], None, [256], [0,256]))

        bs, gs, rs = self.COLOR_BGR_SCORE
        if abs(blue-bs)<=3 and abs(green-gs)<=1 and abs(red-rs)<=1:
            return True
        return False

    def test_loading_players(self, img):
        """Tests if the players are still loading.

        Check by color-checking the "Ready" and "Loading..." texts.
        """
        height, width = img.shape[:2]
        img_loadingboard = img[height/7.4:-height/2.5, width/2.9:-width/2.9]
        height, width = img_loadingboard.shape[:2]
        img_loadingboard_status = img_loadingboard[height/5.0:-height/8.0, width/1.4:-width/9.0]


        bot_red, top_red = self.COLOR_BGR_LOADINGPLAYERS_RED
        bot_green, top_green = self.COLOR_RGB_LOADINGPLAYERS_GREEN
        img_red_thresh = cv2.inRange(img_loadingboard_status, bot_red, top_red)
        img_green_thresh = cv2.inRange(img_loadingboard_status, bot_green, top_green)
        
        mask = cv2.bitwise_or(img_green_thresh, img_red_thresh)
        height, width = mask.shape
        mask_draw = np.zeros((height,1))
        for i in xrange(height):
            if mask[i].any():
                mask_draw[i] = np.array([255])
            
        # There must be 10 blocks of a same size > height/21 (21: there are now 11 blocks possible (10 players + the space in the middle). So >= half the actual size counts
        # TODO: SHIT. 1-10 Players possible :(
            
        try:
            #Sobel detects gradients, in this case in y direction
            sobel_y = cv2.Sobel(mask_draw,cv2.CV_64F,0,1,ksize=1)
            sobel_y_uint8 = np.uint8(sobel_y)
            
            # Transitions are always 2 pixels wide, so /2
            players = np.sum(sobel_y_uint8)/255/2
            print players
            #TODO: Count not enough. Need something for "evenly spaced" or "blocks are height/x high"
            if players == 9 or players == 10 or players == 11:
                print 'Loadingscreen?'
                #self.plot_image([img, mask, mask_draw], gray=True)
        except Exception, e:
            print e

        if self.template_matching(img_red_thresh, self.template_loadingplayers_loading, callee='loadingplayers_loading'):
            return True
            
        if self.template_matching(img_green_thresh, self.template_loadingplayers_ready, callee='loadingplayers_loading_ready'):
            return True
        return False

    def test_loading_map(self, img):
        """Tests if Dota is in the loading screen
        
        Checks if the "Loading..." template is in the bottom right corner
        """

        img = img[-100:, -150:]
        img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        _, img_thresh = cv2.threshold(img_gray, self.THRESH_LOADINGMAP, 255, cv2.THRESH_BINARY)
        return self.template_matching(img_thresh, self.template_loadingmap, callee='loadingmap')
        
    def test_draft(self, img):
        """Tests if the dota client is in draft.
        
        Tested by checking the Chat-icon on the bottom-left corner.
        """
        img = img[-100:, :100]
        #img = cv2.threshold(img, 150, 255, cv2.THRESH_BINARY)
        img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        _, img_thresh = cv2.threshold(img_gray, self.THRESH_DRAFT, 255, cv2.THRESH_BINARY)
        
        return self.template_matching(img_thresh, self.template_draft, callee='draft')
    
    def test_ingame(self, img):
        """Tests if the dota client is 'just' ingame.

        Tested by checking the top left corner for the
        minimize-icon. That can also be there in draft and 
        loadingplayers, which get excluded before."""
        img_ingame = img[:50, :100]

        img_gray = cv2.cvtColor(img_ingame, cv2.COLOR_BGR2GRAY)
        _, img = cv2.threshold(img_gray, self.THRESH_INGAME, 255, cv2.THRESH_BINARY)
        
        return self.template_matching(img, self.template_ingame, callee='ingame')
    
    def template_matching(self, img, template, callee=''):
        res = cv2.matchTemplate(img, template, cv2.cv.CV_TM_CCOEFF_NORMED)
        best_point = list(cv2.minMaxLoc(res)[3])
        (y_, x_), (h_, w_) = best_point, template.shape

        # if best point would set the template (partially) outside the img
        if x_+h_ > img.shape[0] or y_+w_ > img.shape[1]:
            return False
        
        diff = cv2.absdiff(img[x_:x_+h_, y_:y_+w_], template)
        m_norm = np.sum(diff)/template.size
        if False and callee=='loadingplayers_loading':
            print m_norm, best_point
            pl.figure()
            pl.subplot(2,2,1)
            pl.imshow(img, cmap='gray')
            pl.subplot(2,2,2)
            pl.imshow(template, cmap='gray', interpolation='nearest')
            pl.subplot(2,2,3)
            pl.imshow(res, interpolation='nearest')
            pl.subplot(2,2,4)
            pl.imshow(diff, cmap='gray', interpolation='nearest')
            pl.show()

        if m_norm <= 20:
            return True
        return False
        
    def plot_image(self, imgs, title='', gray=False):
        pl.figure()
        
        if type(imgs) not in [list, set]:
            imgs = cv2.cvtColor(imgs, cv2.COLOR_BGR2RGB)
            pl.imshow(imgs, interpolation='nearest')
        else:
            for j, i in enumerate(imgs):
                pl.subplot(1, len(imgs), j+1)
                if gray:
                    pl.imshow(i, cmap='gray', interpolation='nearest')
                else:
                    pl.imshow(i, interpolation='nearest')
        pl.title(title)
        pl.show()
