from pathlib import Path
NAMES = {}  # Distribution defaults: discover controllers without personal addresses.
def read_batteries(root="/sys/class/power_supply"):
    result = {}
    for path in Path(root).glob("sony_controller_battery_*"):
        address = path.name[len("sony_controller_battery_"):][:17].lower()
        try:
            level = int((path / "capacity").read_text().strip())
            status = (path / "status").read_text().strip()
        except (OSError, ValueError):
            continue
        if 0 <= level <= 100:
            result[address] = {"name": NAMES.get(address, "Controller " + address[-5:]), "level": level, "status": status}
    return result

def transition(previous, level, status):
    # A charging report is not a measured percentage. Rearm on charge or recovery.
    if status in ("Charging", "Full") or level >= 50:
        return 0, None
    severity = 2 if level <= 1 else (1 if level <= 25 else 0)
    if severity > previous:
        return severity, ("critically low" if severity == 2 else "low")
    return previous, None

def lines(batteries):
    rows = []
    for address, name in NAMES.items():
        battery = batteries.get(address)
        if battery is None:
            rows.append(name + " (" + address[-5:].upper() + "): Not connected")
        else:
            status = battery["status"]
            value = status if status in ("Charging", "Full") else str(battery["level"]) + "%"
            rows.append(name + " (" + address[-5:].upper() + "): " + value)
    for address, battery in sorted(batteries.items()):
        if address not in NAMES:
            rows.append(battery["name"] + ": " + (battery["status"] if battery["status"] in ("Charging", "Full") else str(battery["level"]) + "%"))
    return rows
