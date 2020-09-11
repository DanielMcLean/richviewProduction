'''
Author: Daniel McLean,
Date: September 2020

Description: 
    Python Script to intercept OSC commands from programs like open source control
    and translate them into VISCA commands for a Birddog P200 cammera.
    
    OSC Commands:
        /{camera ID}/{command}/ args[]
        
        commands:
            pan_{X} | args: pan_speed tilt_speed
                X = up,down,left,right,up_left,up_right,down_left,down_right
            pan_absolute_position | args: pan_speed tilt_speed abs_pan abs_tilt
            zoom_tele_variable |args: zoom_speed
            zoom_wide_variable |args: zoom_speed
        
'''
# receive OSC messages and send VISCA control messages to camera (both UDP)

# pip3 install aiosc
# https://pypi.org/project/aiosc/
# https://github.com/artfwo/aiosc
import asyncio # for receiving OSC
import aiosc # for receiving OSC
# pip3 install python-osc
# https://pypi.org/project/python-osc/
from pythonosc import udp_client # for sending OSC
from math import floor  # for fader
import socket
import binascii  # for printing the visca messages

### VISCA sender (socket)
camera_ip = '192.168.50.40'
camipDic = {
        "1":'192.168.50.40',
        "2":'192.168.50.28',
        "3":'192.168.50.111'}

#camera_ip = '127.0.0.1'
camera_port = 52381
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # IPv4, UDP

### VISCA receiver
buffer_size = 1024
s.bind(('', camera_port)) # for testing use the port one higher than the camera's port
s.settimeout(1.0) # only wait for a response for 1 second

### VISCA Commands (Payloads)
camera_on = '81 01 04 00 02 FF'
information_display_off = '81 01 7E 01 18 03 FF'
memory_recall = '81 01 04 3F 02 0p FF' # p: Memory number (=0 to F)
memory_set = '81 01 04 3F 01 0p FF' # p: Memory number (=0 to F)
movement_speed = '01'
'''
pan_speed = '05'
tilt_speed = '05'
pan_up = '81 01 06 01 VV WW 03 01 FF'.replace('VV', str(pan_speed)).replace('WW', str(tilt_speed))
pan_down = '81 01 06 01 VV WW 03 02 FF'.replace('VV', str(pan_speed)).replace('WW', str(tilt_speed))
pan_left = '81 01 06 01 VV WW 01 03 FF'.replace('VV', str(pan_speed)).replace('WW', str(tilt_speed))
pan_right = '81 01 06 01 VV WW 02 03 FF'.replace('VV', str(pan_speed)).replace('WW', str(tilt_speed))
pan_up_left = '81 01 06 01 VV WW 01 01 FF'.replace('VV', str(pan_speed)).replace('WW', str(tilt_speed))
pan_up_right = '81 01 06 01 VV WW 02 01 FF'.replace('VV', str(pan_speed)).replace('WW', str(tilt_speed))
pan_down_left = '81 01 06 01 VV WW 01 02 FF'.replace('VV', str(pan_speed)).replace('WW', str(tilt_speed))
pan_down_right = '81 01 06 01 VV WW 02 02 FF'.replace('VV', str(pan_speed)).replace('WW', str(tilt_speed))
pan_stop = '81 01 06 01 VV WW 03 03 FF'.replace('VV', str(pan_speed)).replace('WW', str(tilt_speed))
'''
pan_dictionary = {
    'pan_up' : '81 01 06 01 VV WW 03 01 FF',
    'pan_down' : '81 01 06 01 VV WW 03 02 FF',
    'pan_left' : '81 01 06 01 VV WW 01 03 FF',
    'pan_right' : '81 01 06 01 VV WW 02 03 FF',
    'pan_up_left' : '81 01 06 01 VV WW 01 01 FF',
    'pan_up_right' : '81 01 06 01 VV WW 02 01 FF',
    'pan_down_left' : '81 01 06 01 VV WW 01 02 FF',
    'pan_down_right' : '81 01 06 01 VV WW 02 02 FF'}

# YYYY: Pan Position DE00 (−170 degree) to 2200 (170 degree) (CENTER 0000)
# ZZZZ: Tilt Position EE00 (–90 degree) to 0400 (90 degree) (CENTER 0000)
# for high speed VV = 18 and WW = 17
pan_direct = '8x 01 06 02 18 17 0Y 0Y 0Y 0Y 0Z 0Z 0Z 0Z FF' # absolute position  
pan_stop = '81 01 06 01 15 15 03 03 FF' # replaced VV and WW with 15
pan_home = '81 01 06 04 FF'
pan_reset = '81 01 06 05 FF'
focus_stop = '81 01 04 08 00 FF'
focus_far = '81 01 04 08 02 FF'
focus_near = '81 01 04 08 03 FF'
focus_far_variable = '81 01 04 08 2p FF'.replace('p', '7') # 0 low to 7 high
focus_near_variable = '81 01 04 08 3p FF'.replace('p', '7') # 0 low to 7 high
focus_direct = '81 01 04 48 0p 0q 0r 0s FF' #.replace('p', ) q, r, s
focus_auto = '81 01 04 38 02 FF'
focus_manual = '81 01 04 38 03 FF'
focus_infinity = '81 01 04 18 02 FF'
zoom_stop = '81 01 04 07 00 FF'
zoom_tele = '81 01 04 07 02 FF'
zoom_wide = '81 01 04 07 03 FF'
zoom_tele_variable = '81 01 04 07 2p FF' # p=0 (Low) to 7 (High)
zoom_wide_variable = '81 01 04 07 3p FF' # p=0 (Low) to 7 (High)
zoom_direct = '81 01 04 47 0p 0q 0r 0s FF' # pqrs: Zoom Position
zoom_focus_direct = '81 01 04 47 0p 0q 0r 0s 0t 0u 0v 0w FF' # pqrs: Zoom Position  tuvw: Focus Position

inquiry_lens_control = '81 09 7E 7E 00 FF'
# response: 81 50 0p 0q 0r 0s 0H 0L 0t 0u 0v 0w 00 xx xx FF
inquiry_camera_control = '81 09 7E 7E 01 FF'


movement_speed = '05'
pan_speed = movement_speed
tilt_speed = movement_speed
panDic = {
'pan_up' : '81 01 06 01 VV WW 03 01 FF'        ,
'pan_down' : '81 01 06 01 VV WW 03 02 FF'      ,
'pan_left' : '81 01 06 01 VV WW 01 03 FF'      ,
'pan_right' : '81 01 06 01 VV WW 02 03 FF'     ,
'pan_up_left' : '81 01 06 01 VV WW 01 01 FF'   ,
'pan_up_right' : '81 01 06 01 VV WW 02 01 FF'  ,
'pan_down_left' : '81 01 06 01 VV WW 01 02 FF' ,
'pan_down_right' : '81 01 06 01 VV WW 02 02 FF',
'pan_stop' : '81 01 06 01 VV WW 03 03 FF'
}


# YYYY: Pan Position DE00 to 2200 (CENTER 0000)
# ZZZZ: Tilt Position FC00 to 1200 (CENTER 0000)
#           pan_direct = '8x 01 06 02 18 17 0Y 0Y 0Y 0Y 0Z 0Z 0Z 0Z FF' # absolute position  
pan_absolute_position = '81 01 06 02 VV WW 0Y1 0Y2 0Y3 0Y4 0Z1 0Z2 0Z3 0Z4 FF' #.replace('VV', str(VV)) #YYYY[0]
#pan_relative_position = '81 01 06 03 VV WW 0Y 0Y 0Y 0Y 0Z 0Z 0Z 0Z FF'.replace('VV', str(VV))
def panToHex(numP,numT):
    
    minPD = -175
    maxPD = 175
    rangePD = maxPD - minPD
    minTD = -30
    maxTD = 90
    rangeTD = maxTD - minTD
    
    minP = 0xF92A# -175
    maxP = 0x06d6# +175
    rangeP = 0x10000 + maxP - minP
    
    minT = 0xfe80 # -90
    maxT = 0x0480 # +90
    rangeT = 0x10000 + maxT - minT

    # Unclear if we need to adjust for birddog P200 range or not
    
    # Convert neg to positive
    convP = numP - minPD
    convT = numT - minTD
    
    # Scale and cast
    scaleP = int(round(convP/rangePD*rangeP))
    scaleT = int(round(convT/rangeTD*rangeT))
    
    absP = (minP + scaleP) & 0xffff
    absT = (minT + scaleT) & 0xffff
    
    return(hex(absP)[2:].zfill(4),hex(absT)[2:].zfill(4))
    
    
def send_message(message_string, camId = "1"):
    camera_ip = camipDic[camId]
    global sequence_number
    #global received_message
    payload_type = bytearray.fromhex('01 00')
    payload = bytearray.fromhex(message_string)
    payload_length = len(payload).to_bytes(2, 'big')
    message = payload_type + payload_length + sequence_number.to_bytes(4, 'big') + payload
    #if message_string == reset_sequence_number:
    #    sequence_number = 1
    #    #sequence_number = 4294967295
    #else:
    #    sequence_number += 1
    sequence_number += 1
    s.sendto(message, (camera_ip, camera_port))
    #print(binascii.hexlify(message), 'sent to', camera_ip, camera_port, sequence_number)
    # add a timeout in case we don't hear back
    '''
    try:
        data = s.recvfrom(buffer_size)
        received_message = binascii.hexlify(data[0])
        print('Received', received_message)
        data = s.recvfrom(buffer_size)
        received_message = binascii.hexlify(data[0])
        print('Received', received_message)
    except socket.timeout: # s.settimeout(2.0) #above
        received_message = 'No response from camera'
        print(received_message)

    #if received_message == b'01110003000000119051ff':
    if received_message[0:4] == '0111':
        display_message.set('Connected')
    else:
        display_message.set(received_message[0:4])
    #'''
    received_message = 'test'
    return received_message

def reset_sequence_number_function(camId = "1"):  # this should probably be rolled into the send_visca function
    camera_ip = camipDic[camId]
    reset_sequence_number_message = bytearray.fromhex('02 00 00 01 00 00 00 01 01')
    s.sendto(reset_sequence_number_message,(camera_ip, camera_port))
    global sequence_number
    sequence_number = 1
    print('Reset sequence number to', sequence_number)
    try:
        data = s.recvfrom(buffer_size)
        received_message = binascii.hexlify(data[0])
        #print('Received', received_message)
        data = s.recvfrom(buffer_size)
        received_message = binascii.hexlify(data[0])
        #print('Received', received_message)
        send_osc('reset_sequence_number', 1.0)
    except socket.timeout: # s.settimeout(2.0) #above
        received_message = 'No response from camera'
        print(received_message)
        send_osc('reset_sequence_number', 0.0)
    return sequence_number
def send_visca(message_string,camId="1"):
    camera_ip = camipDic[camId]
    global sequence_number
    payload_type = bytearray.fromhex('01 00')
    payload = bytearray.fromhex(message_string)
    payload_length = len(payload).to_bytes(2, 'big')
    visca_message = payload_type + payload_length + sequence_number.to_bytes(4, 'big') + payload
    s.sendto(visca_message, (camera_ip, camera_port))
    print(binascii.hexlify(visca_message), 'sent to', camera_ip, camera_port, sequence_number)
    sequence_number += 1
    '''# wait for acknowledge and completion messages
    try:
        data = s.recvfrom(buffer_size)
        received_message = binascii.hexlify(data[0])
        #print('Received', received_message)
        data = s.recvfrom(buffer_size)
        received_message = binascii.hexlify(data[0])
        if received_message == b'9051ff':
            print('Received okay')
        else:
            print('Error')
        #print('Received', received_message)
    except socket.timeout: # s.settimeout(2.0) #from above
        received_message = 'No response from camera'
        print(received_message)
        send_osc('reset_sequence_number', 0.0)
    #'''
    received_message = 'test'
    #return visca_message
    return received_message

### OSC server and client
osc_receive_port = 8002
touchOSC_ip = '192.168.50.183' # there must be a way to listen for this... maybe osc_address[0]
osc_send_port = 9002

def send_osc(osc_command, osc_send_argument):
    osc_message_to_send = '/1/' + osc_command
    osc_client = udp_client.SimpleUDPClient(touchOSC_ip, osc_send_port)
    osc_client.send_message(osc_message_to_send, osc_send_argument)

### OSC receiving server
def parse_osc_message(osc_address, osc_path, args):
    global touchOSC_ip
    touchOSC_ip = osc_address[0]
    osc_path_list = osc_path.split('/')
    #print (osc_path_list)
    camId = osc_path_list[1]
    osc_command = osc_path_list[2]
    #print("ARGS:")
    #print(args)
    osc_argument = args[0]
    #print (osc_command)
    #print (osc_argument)
    if osc_command == 'camera_on':
        send_visca(camera_on,camId)
    elif osc_command == 'reset_sequence_number':
        reset_sequence_number_function()
    elif 'memory_' in osc_command:
        memory_preset_number = hex(int(osc_argument))[2:]
        if osc_argument > 0:
            if 'recall' in osc_command:
                print('Memory recall', memory_preset_number)
                send_visca(information_display_off,camId) # so that it doesn't display on-screen
                send_visca(memory_recall.replace('p', memory_preset_number),camId)
            elif 'set' in osc_command:
                print('Memory set', memory_preset_number)
                send_visca(memory_set.replace('p', memory_preset_number),camId)
    elif 'zoom' in osc_command:
        if osc_argument > 0:
            zoomSpeed = str(int(min(7,args[0])))
            if osc_command == 'zoom_tele':
                send_visca(zoom_tele,camId)
            elif osc_command == 'zoom_wide':
                send_visca(zoom_wide,camId)
            elif osc_command == 'zoom_tele_variable':
                send_visca(zoom_tele_variable.replace('p', zoomSpeed),camId)
            elif osc_command == 'zoom_wide_variable':
                send_visca(zoom_wide_variable.replace('p', zoomSpeed),camId)
        else: # when the button is released the osc_argument should be 0
            send_visca(zoom_stop,camId)
    elif 'focus' in osc_command:
        if osc_command == 'focus_auto':
            send_visca(focus_auto,camId)
        if osc_argument > 0:
            if osc_command == 'focus_far':
                send_visca(focus_far,camId)
            elif osc_command == 'focus_near':
                send_visca(focus_near,camId)
        else: # when the button is released the osc_argument should be 0
            send_visca(focus_stop,camId)
    elif 'speed' in osc_command: # e.g. speed01 or speed15, from buttons not a slider
        global movement_speed
        movement_speed = osc_command[5:]
        send_osc('MovementSpeedLabel', movement_speed)
        print('set speed to', movement_speed)
    elif 'pan' in osc_command:
        
        # Absolute Position
        if "pan_absolute_position" in osc_command:
            if args[0] > 0 and args[1] >0:
                panSpeed = str(int(args[0])).zfill(2)
                tiltSpeed = str(int(args[1])).zfill(2)
                absP, absT = panToHex(int(args[2]),int(args[3]))
                #print ("ABSOLUTE")
                #print (absP)
                #print (absT)
                    
                convMsg = pan_absolute_position.replace('VV', panSpeed).replace('WW', str(tiltSpeed))
                convMsg = convMsg.replace('Y1',absP[0]).replace('Y2',absP[1]).replace('Y3',absP[2]).replace('Y4',absP[3])
                convMsg = convMsg.replace('Z1',absT[0]).replace('Z2',absT[1]).replace('Z3',absT[2]).replace('Z4',absT[3])
                send_message(convMsg,camId)
                
                
            else: # when the button is released the osc_argument should be 0
                send_visca(pan_stop,camId)
            
        
        elif 'pan_home' in osc_command:
            send_visca(pan_home,camId)
            
        else:  
            if args[0] > 0 or args[1] >0:
                panSpeed = str(int(args[0])).zfill(2)
                tiltSpeed = str(int(args[1])).zfill(2)
                send_message(panDic[osc_command].replace('VV', panSpeed).replace('WW', str(tiltSpeed)),camId)
            else: # when the button is released the osc_argument should be 0
                send_visca(pan_stop,camId)
    else:
        print("I don't know what to do with", osc_command, osc_argument)
    send_osc('SentMessageLabel', osc_command)


## Start off by resetting sequence number
sequence_number = 1 # a global variable that we'll iterate each command, remember 0x0001
reset_sequence_number_function()

## Then start the OSC server to receive messages
def protocol_factory():
    osc = aiosc.OSCProtocol({'//*': lambda osc_address, osc_path, *args: parse_osc_message(osc_address, osc_path, args)})
    return osc
receive_loop = asyncio.get_event_loop()
coro = receive_loop.create_datagram_endpoint(protocol_factory, local_addr=('0.0.0.0', osc_receive_port))
transport, protocol = receive_loop.run_until_complete(coro)
receive_loop.run_forever()