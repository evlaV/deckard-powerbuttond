#!/usr/bin/python3
import struct, select, subprocess

# This extremely cut-down version of `buttonledcontrol` is a stopgap to start SteamVR when a
# deckard unit without the u-boot charger capability gets plugged in.  Ideally, we plug in the
# unit and it starts charging but doesn't boot the system.  If we don't have u-boot charging,
# then we actually boot the system but inhibit SteamVR from starting.  If this happens, we start
# this script as a service so that if the user presses the power button again, we can start
# SteamVR.  Once SteamVR is started, this script is not used (and in particular, if they press
# the power button again, powerbuttond will suspend the unit).

class InputPoller:
    def __init__( self ):
        self.__inputStructFormat = 'llHHI'
        self.__eventSize = struct.calcsize( self.__inputStructFormat )
        self.__in_file = None
    
    def open(self):
        self.__in_file = open( "/dev/input/event0", "rb" )
        assert( self.__in_file )
        self.pollobj = select.poll()
        assert( self.pollobj )
        self.pollobj.register( self.__in_file, select.POLLIN )

    def poll( self, maxDelayMs ):
        events = []
        available = self.pollobj.poll( maxDelayMs )
        for (fd, event) in available:
            if event & select.POLLIN:
                event = self.__in_file.read( self.__eventSize )
                (tv_sec, tv_usec, evtype, code, value) = struct.unpack(self.__inputStructFormat, event)
                tval = float( tv_sec + tv_usec * 1e-6 )
                events.append( (tval, evtype, code, value ) )
        return events

def ScanForEvents():
    POLL_DELAY_MS = 500
    EV_SYN = 0 # event type
    EV_KEY = 1 # event type
    KEY_POWER = 116
    previouslyPressed = False

    poller = InputPoller()
    poller.open()

    while True:
        for (tval, evtype, code, value) in poller.poll( POLL_DELAY_MS ):
            if evtype == EV_KEY and code == KEY_POWER:
                if value == 1:
                    previouslyPressed = True
                elif value == 0:
                    # Trigger on a release but only if we observed a press-down previously
                    if previouslyPressed:
                        print("Starting SteamVR...")
                        subprocess.run( ["/bin/systemctl", "start", "steamvr-session@tty1"] )
                    previouslyPressed = False

if __name__ == "__main__":
    ScanForEvents()
