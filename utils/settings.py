"""
This is the Config File for the Dota 2 Overlayswitcher
Everything here is python syntax and imported as "from settings import *"
"""


# Define the directory of the dota-directory inside your dota 2 beta directory inside your SteamApps.
DOTA_DIR = 'C:\Spiele\Steam\SteamApps\common\dota 2 beta\dota'


# Define the hotkeys for the Dota 2 states. Hotkeys are lists of codes.
# For Windows, these are Virtual Keycodes, the comprehensive list is here:
#http://msdn.microsoft.com/en-us/library/windows/desktop/dd375731%28v=vs.85%29.aspx)
# You should choose key combinations which do not print anything to avoid interruptions.

KEY_CTRL_ALT_M = [0x11, 0x12, 0x60]
KEY_CTRL_ALT_PLUS = [0x11, 0x12, 0xBB]

# This structure needs to be filled.
OVERLAYS = {
            'INIT':                     KEY_CTRL_ALT_M,
            'WAIT_FOR_PLAYERS_TO_LOAD': KEY_CTRL_ALT_M,
            'HERO_SELECTION':           KEY_CTRL_ALT_M,
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