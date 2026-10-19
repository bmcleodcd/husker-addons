import json
from pathlib import Path
import xbmc
import xbmcaddon
import xbmcgui
import xbmcvfs
from battery import read_batteries, transition
profile = Path(xbmcvfs.translatePath(xbmcaddon.Addon().getAddonInfo("profile")))
profile.mkdir(parents=True, exist_ok=True)
state_file = profile / "alerts.json"
try:
    state = json.loads(state_file.read_text())
    if not isinstance(state, dict):
        state = {}
except (OSError, ValueError):
    state = {}
monitor = xbmc.Monitor()
xbmc.log("Controller batteries: service started", xbmc.LOGINFO)
# Let the driver receive initial reports before using its default 100% reading.
if not monitor.waitForAbort(15):
    while not monitor.abortRequested():
        try:
            batteries = read_batteries()
            changed = False
            for address, battery in batteries.items():
                previous = state.get(address, 0)
                if previous not in (0, 1, 2):
                    previous = 0
                current, alert = transition(previous, battery["level"], battery["status"])
                if current != previous:
                    state[address] = current
                    changed = True
                if alert:
                    xbmcgui.Dialog().notification("Controller battery " + alert,
                        battery["name"] + " (" + address[-5:].upper() + "): " + str(battery["level"]) + "% - please charge",
                        xbmcgui.NOTIFICATION_WARNING, 8000, False)
            if changed:
                temporary = state_file.with_suffix(".tmp")
                temporary.write_text(json.dumps(state))
                temporary.replace(state_file)
            # Read-only diagnostic snapshot confirms visibility from Kodi's sandbox.
            (profile / "status.json").write_text(json.dumps(batteries))
        except Exception as error:
            xbmc.log("Controller batteries: " + str(error), xbmc.LOGERROR)
        if monitor.waitForAbort(30):
            break
