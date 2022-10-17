##
# @module    coldstart
# @brief     GNSS engine coldstart
# @version   1.0
##

import gnss
import vts

class GNSS_Coldstart:
    def __init__(self):
        gnss_engine = vts.unit_info()["GNSS Engine"]
        if gnss_engine == 'TOPCON B111':
            self.coldstart = self._coldstart_B11x
        elif gnss_engine.startswith('UBLOX'):
            self.coldstart = self._coldstart_ublox
        else:
            self.coldstart = lambda: None
            print('Coldstart disabled')

    def _coldstart_ublox(self):
        gnss.command(b'\xb5\x62\x06\x04\x04\x00\xff\xff\x02\x00\x0e\x61')

    def _coldstart_B11x(self):
        # Reset settings
        gnss.command('init,/dev/nvm/a')
        vts.delay_ms(2500)
        # Use 5V antenna input
        gnss.command('set,/par/ant/rcv/inp,ext')
        vts.delay_ms(100)
        # Set precision to 5 decimal places
        gnss.command('set,/par/nmea/frac/min,5')
        vts.delay_ms(100)
        # Set elevation mask
        gnss.command('set,/par/lock/elm,5')
        vts.delay_ms(100)
        # Do not use unhealthy/below mask satellites
        gnss.command('set,/par/lock/notvis,off')
        vts.delay_ms(100)
        # 20 Hz measurement update rate
        gnss.command('set,/par/raw/msint,50')
        vts.delay_ms(100)
        # 20 Hz position update rate
        gnss.command('set,/par/pos/msint,50')
        vts.delay_ms(100)
        # Turn on GGA and VTG messages at 20 Hz
        gnss.command('em,,/msg/nmea/{GGA,VTG}:0.05')
        vts.delay_ms(100)


# Convenience definition
cstart_obj = GNSS_Coldstart()
def coldstart():
    cstart_obj.coldstart()

