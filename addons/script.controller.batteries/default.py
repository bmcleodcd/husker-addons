import xbmcgui
from battery import read_batteries, lines
xbmcgui.Dialog().ok("Controller batteries", "\n".join(lines(read_batteries())) + "\n\nBattery readings are approximate.")
