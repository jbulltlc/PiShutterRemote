from pishutter.protocols.powersmart import PowerSmartRemote

SHUTTERS = {
    "islas-room": PowerSmartRemote(
        name="Isla's Room",
        up="fd90bca8aa6f4351",
        stop="fd90bda8aa6f4251",
        down="fd10bda8aaef4251",
    ),
    "islas-spare-room": PowerSmartRemote(
        name="Isla's Spare Room",
        up="fd88bca8aa774351",
        stop="fd88bda8aa774251",
        down="fd08bda8aaf74251",
    ),
    "kitchen": PowerSmartRemote(
        name="Kitchen",
        up="fd84bca8aa7b4351",
        stop="fd84bda8aa7b4251",
        down="fd04bda8aafb4251",
    ),
    "main-bedroom": PowerSmartRemote(
        name="Main Bedroom",
        up="fdc0bca8aa3f4351",
        stop="fdc0bda8aa3f4251",
        down="fd40bda8aabf4251",
    ),
    "studio": PowerSmartRemote(
        name="Studio",
        up="fda0bca8aa5f4351",
        stop="fda0bda8aa5f4251",
        down="fd20bda8aadf4251",
    ),
    "main-lounge": PowerSmartRemote(
        name="Main Lounge",
        up="fd82bca8aa7d4351",
        stop="fd82bda8aa7d4251",
        down="fd02bda8aafd4251",
    ),
}
#python tools/send_powersmart.py kitchen up
#python tools/send_powersmart.py kitchen down
#python tools/send_powersmart.py kitchen up
