#!/usr/bin/env python

from overlayswitcher import OverlaySwitcher
import sys

if __name__ == '__main__':
    """Currently not neccessary due to no templates."""
    if len(sys.argv) != 2:
        print 'Usage: {0} Path\n\tWhere Path is the path the templates should be saved to'.format(sys.argv[0])
    template_path = sys.argv[1]
    switcher = OverlaySwitcher(bare=True)
    switcher.get_dota_hwnd()
    l, t, width, height = win32gui.GetWindowRect(switcher.dota_hwnd)
    img = switcher.get_dota_screenshot()
    if not img:
        sys.exit(1)
    print 'You are running Dota 2 at a resolution of {0}x{1} pixels'.format(width-t, height-l)
    print 'Does this screenshot look okay?'
    switcher.plot_image(img, title='Test Dota 2 Screenshot')
    ret = raw_input('Y/n')
    if ret == 'n':
        sys.exit(1)
    print 'This program will make templates for your resolution and save them into "{0}".'.format()
    print 'You will be asked to display the scenes in your Dota window and press "Enter" here to continue.'
    print 'Now lets start!'
    print 'Please display the beginning of a game, where the table is shown which player is still Loading. Pause when there is at least one player still loading (red) and one player has already loaded (green)'
    #TODO: Continue seeing the problem with non-scalable templates
    #      and continously upgrading the template-match functions
    #      to more complicated image recognition blobs... *sigh*