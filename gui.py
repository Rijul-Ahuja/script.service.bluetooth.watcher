import sys
import json
import os
import subprocess

import xbmc
import xbmcgui
import xbmcaddon

import common
from bluetooth_service import BluetoothService

def uniquify(mylist):
    dups = {}
    for i, val in enumerate(mylist):
        if val not in dups:
            # Store index of first occurrence and occurrence value
            dups[val] = [i, 1]
        else:
            # Special case for first occurrence
            if dups[val][1] == 1:
                mylist[dups[val][0]] += str(dups[val][1])
            # Increment occurrence value, index value doesn't matter anymore
            dups[val][1] += 1
            # Use stored occurrence value
            mylist[i] += str(dups[val][1])
    return mylist

def get_devices_dict():
    #k, v = device_name, device_mac
    log('Creating dictionary of devies')
    command_output = subprocess.check_output(BluetoothService.__GET_DEVICES__, shell = True).decode('utf-8')[:-1]
    devices_dict = dict(zip(uniquify([element[25:] for element in command_output.split('\n')]), [element.split(' ')[1] for element in command_output.split('\n')]))
    log('Created devices dictionary {}'.format(json.dumps(devices_dict)))
    return devices_dict

def log(msg):
    common.log(os.path.basename(__file__), msg)

def show_gui(thisAddon):
    log('Loaded thisAddon object')
    dialog = xbmcgui.Dialog()
    log('Created dialog object')
    try:
        saved_devices_to_disconnect = json.loads(thisAddon.getSettingString(BluetoothService.__SETTING_DEVICES_TO_DISCONNECT__))
    except ValueError:
        saved_devices_to_disconnect = {}
    log('Loaded saved_devices_to_disconnect {}'.format(saved_devices_to_disconnect))
    possible_devices_to_disconnect = get_devices_dict()
    log('Loaded possible_devices_to_disconnect {}'.format(possible_devices_to_disconnect))
    #remove items which were saved but are now no longer paired
    for device_name, device_mac in saved_devices_to_disconnect.iteritems():
        if device_mac not in possible_devices_to_disconnect.values():
            log('Found unpaired device {}, removing it from saved devices'.format(device_mac))
            saved_devices_to_disconnect.pop(device_name)
    #create preselect array
    log('Creating preselect array')
    preselect = []
    i = -1
    for device_name, device_mac in possible_devices_to_disconnect.iteritems():
        i = i + 1
        if device_mac in saved_devices_to_disconnect.values():
            log('Found pre-selected device {}'.format(device_mac))
            preselect.append(i)
    #show dialog with multiselect and preselect
    log('Displaying multiselect dialog')
    returned_devices_to_disconnect = dialog.multiselect(thisAddon.getLocalizedString(BluetoothService.__STRING_DEVICES_TO_DISCONNECT_ID__),
        [xbmcgui.ListItem("{} ({})".format(device_name, device_mac)) for device_name, device_mac in possible_devices_to_disconnect.iteritems()], preselect = preselect)
    if returned_devices_to_disconnect is None:
        log('Multiselect dialog was canceled, saving old config {}'.format(saved_devices_to_disconnect))
        thisAddon.setSettingString(BluetoothService.__SETTING_DEVICES_TO_DISCONNECT__, json.dumps(saved_devices_to_disconnect))
    else:
        to_save_devices = {list(possible_devices_to_disconnect.keys())[element]: list(possible_devices_to_disconnect.values())[element] for element in returned_devices_to_disconnect}
        log('Saving new config {}'.format(to_save_devices))
        thisAddon.setSettingString(BluetoothService.__SETTING_DEVICES_TO_DISCONNECT__, json.dumps(to_save_devices))

def disconnect_now(thisAddon):
    object = BluetoothService(thisAddon)
    object.refresh_settings()
    object.disconnect_possible_devices(True)

if (__name__ == '__main__'):
    thisAddon = xbmcaddon.Addon()
    log('GUI.py - main function')
    try:
        arg = sys.argv[1].lower()
    except IndexError:
        arg = None
    #log(str(arg))
    if arg is not None:
        if BluetoothService.__SETTING_DISCONNECT_NOW__ in arg:
            disconnect_now(thisAddon)
            if 'back' in arg:
                common.json_rpc(method = "Input.Back", id = 1)
        elif arg == common.__SETTING_SHOW_GUI__:
            show_gui(thisAddon)
        else:
            log('arg: {}'.format(arg))
            disconnect_now(thisAddon)
    else:
        disconnect_now(thisAddon)
