import time
import win32api

def press_key(hexKeyCode):
    win32api.keybd_event(hexKeyCode, 0x0, 0)

def release_key(hexKeyCode):
    win32api.keybd_event(hexKeyCode, 0x0, 0x0002)

def send_keys(keys):
    for k in keys:
        press_key(k)
        time.sleep(0.05)    #OBS needs this! 0.01 is not enough

    for k in keys:
        release_key(k)