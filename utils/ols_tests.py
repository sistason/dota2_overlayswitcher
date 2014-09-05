import cv2
import numpy as np
import pylab as pl

class TestGameEnv():
    """Base Class for everything concerning actual Dota 2 processing
    """
    def __init__(self):
        pass

    def get_newest_base_state(self):
        """Get the newest state from the log-file of Dota 2"""
        ret = self.dota_log.read()
        for line in reversed(ret.split('\n')):
            if line.startswith('Start of Dota'):
                return 'MENU'

            pos_rule = line.find('DOTA_GAMERULES_STATE_')
            if pos_rule >= 0:
                return line[pos_rule+21:-1]
        
    def determine_game_state(self, img):
        """Determine which state Dota 2 is currently in.
        
        First, get the base_environment from the log file. This
        is accurate except it cannot check if the menu is up or not,
        so check this with the screenshot.
        """
        # Break if screen is blank
        if img is None or not img.any():
            return ''

        base_state = self.get_newest_base_state()
        if base_state:
            self.base_state = base_state
            
        # Order-Dependencies:
        # scoreboard > loadingplayers (black top/bot-border)
        # draft, scoreboard, loadingplayers > ingame (minimize-icon)

        #Simple, distinct icon-searches
        if self.base_state == 'menu' or self.test_menu(img):
            return 'MENU'
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

    def test_menu(self, img):
        """ Tests if Dota is in the menu

        Checks if the settings-icon is in the top left corner. The icon
        is symbolized by having a hole in the middle (the gear-symbol)."""
        img = img[:40, :100]
        
        # The icons are distinguishable by their special grey color
        img_hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        bot_grey, top_grey = self.COLOR_HSV_MENU
        img_thresh = cv2.inRange(img_hsv, bot_grey, top_grey)

        # Erode twice as it does not matter for the purpose of finding the hole,
        # but eliminates possible noise in the image
        img_thresh_eroded = cv2.erode(img_thresh, np.ones((2,2),np.uint8), iterations=2)
        if not img_thresh_eroded.any():
            return False
        
        # Crop the image to only keep the icons
        left_border, right_border, top_border, bot_border = self.utils_find_borders(img_thresh_eroded)
        
        img_cropped = img_thresh_eroded[top_border:bot_border, left_border:right_border]
        height, width = img_cropped.shape[:2]
        
        # If the image has a blank line in the middle, its because there are
        # two icons. Split in the middle and recrop!
        if not img_cropped[:, width/2].any():
            img_cropped = img_cropped[:, width/2:]
            left_border, right_border = self.utils_find_borders(img_cropped, leftright=True)
            img_cropped = img_cropped[:, left_border:right_border]
            height, width = img_cropped.shape[:2]
            
        # Check if a hole of 3x3 is in the middle of the img
        return not img_cropped[height/2-1:height/2+1, width/2-1:width/2+1].any()
        
        #return self.template_matching(img_thresh, self.template_menu, callee='menu')
        
    def utils_find_borders(self, img, leftright=False):
        """Get the set left, right, top and bottom borders of the images.
        
        If left_right is set, just compute left and right border"""
        height, width = img.shape[:2]
        if not leftright:
            top_border = 0
            for i in xrange(height):
                if img[i,:].any():
                    top_border = i
                    break
            bot_border = height
            for i in xrange(height-1, 0, -1):
                if img[i,:].any():
                    bot_border = i
                    break
                    
        left_border = 0
        for i in xrange(width):
            if img[:,i].any():
                left_border = i
                break
                
        right_border = width
        for i in xrange(width-1, 0, -1):
            if img[:,i].any():
                right_border = i
                break
                
        if not leftright:
            return left_border, right_border, top_border, bot_border
        return left_border, right_border

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