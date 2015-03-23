"""
This is the Config File for the Dota 2 Overlayswitcher
Everything here is python syntax and get imported.
"""

# Define the path of the console logging file inside your SteamApps.
DOTA_CONSOLE_DIR = 'C:\Spiele\Steam\SteamApps\common\dota 2 beta\dota\console.log'

_USE_HOTKEYS = False

if _USE_HOTKEYS:
# Define the hotkeys for the Dota 2 states. Hotkeys are lists of codes.
# For Windows, these are Virtual Keycodes, the comprehensive list is here:
#http://msdn.microsoft.com/en-us/library/windows/desktop/dd375731%28v=vs.85%29.aspx)
# You should choose key combinations which do not print anything to avoid interruptions.

    KEY_CTRL_ALT_M = [0x11, 0x12, 0x60]
    KEY_CTRL_ALT_N = [0x11, 0x12, 0x61]
    KEY_CTRL_ALT_PLUS = [0x11, 0x12, 0xBB]

# This structure needs to be filled.
    OVERLAYS = {
            'INIT':                     KEY_CTRL_ALT_M,
            'WAIT_FOR_PLAYERS_TO_LOAD': KEY_CTRL_ALT_M,
            'HERO_SELECTION':           KEY_CTRL_ALT_N,
            'STRATEGY_TIME':            KEY_CTRL_ALT_M,
            'PRE_GAME':                 KEY_CTRL_ALT_PLUS,
            'GAME_IN_PROGRESS':         KEY_CTRL_ALT_PLUS,
            'POST_GAME':                KEY_CTRL_ALT_M,           
            'MENU':                     KEY_CTRL_ALT_M,

            # Useable in img_process-mode (advanced, half-broken)
            'transition_startofgame':KEY_CTRL_ALT_M,
            'transition_endofgame':KEY_CTRL_ALT_M,
            
            # Not yet implemented
            'pick_cm':KEY_CTRL_ALT_M,
            'pick_ap':KEY_CTRL_ALT_M,
            'pick_xx':KEY_CTRL_ALT_M
            }
else:
    OBS_REMOTE_URL = '127.0.0.1:4444'
    OBS_REMOTE_PASS = ''

    OVERLAYS = {
            'INIT':                     'Dota noOverlay',
            'WAIT_FOR_PLAYERS_TO_LOAD': 'Dota noOverlay',
            'HERO_SELECTION':           'Dota Overlay CM-Draft',
            'STRATEGY_TIME':            'Dota Overlay CM-Draft',
            'PRE_GAME':                 'Dota Overlay Ingame',
            'GAME_IN_PROGRESS':         'Dota Overlay Ingame',
            'POST_GAME':                'Dota noOverlay',           
            'MENU':                     'Dota noOverlay',
            }
    # Either blacklist or whitelist scenes which should not be interrupted
    LOCKED_SCENES = []#['Intro', 'Waiting']
    WHITELIST_SCENES = ['Dota noOverlay', 'Dota Overlay CM-Draft', 'Dota Overlay Ingame']
