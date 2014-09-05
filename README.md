dota2_overlayswitcher
=====================

Small project to switch overlays of a streaming program depending on what state Dota 2 is in. Can be used for much else, since switching is done by sending global hotkeys.

Similar to [Netherswap](https://github.com/tec27/NetherSwap), but focusses more on the different Dota 2 states (init, draft, ingame, post-game, menu). And its missing the GUI and intuitivity...
* Use Netherswap, if you want to distinguish between Desktop and Dota Overlay.
* Use dota2_overlayswitcher, if you want to change just ingame between your overlays, i.e. forget to disable the ingame-overlay after the game every time ;)

Currently, dota2_overlayswitcher can send hotkeys depending on the Dota 2 state only on Windows, while Dota 2 is running in windowed/borderless window mode.


Installation
===========
* You need Python 2 (2.7, but should work maybe down to 2.5)
* You need OpenCV, Matplotlib and Numpy for python, together with [pywin32](http://sourceforge.net/projects/pywin32/)


Usage
=====
You need to specifiy your Steam-directory and the overlays/Key-Combinations you want in utils/settings.py

Then, just execute the overlayswitcher.py
