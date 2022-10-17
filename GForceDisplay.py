# 6 elements on screen consisting of speed(mph), verticle acc(m/s^2), lateral acc(m/s^2), long acc(m/s^2), lateral acc max(m/s^2), long acc max(m/s^2)
# max values to be able to be reset
# acceleration data to update ~0.3seconds
# speed data to update ~0.1seconds

# Author: Drihan du Preez #

import gui
import vts
import gnss
import vbox
import ustruct as us
from micropython import const
import vbo
from image import Image_Bank
from picture_button import Picture_Button
from button_utils import LoopingButton
from shape_V2 import Custom_Shape

# Variables that need to be defined
RED = const(0xFF0000)
GREEN = const(0x00FF00)
WHITE = const(0xFFFFFF)
BLACK = const(0x000000)
sats_colour = [gui.DL_COLOR(RED)]
sats = ["0"]
sample = vbox.get_sample_hp()
logging_colour = [gui.DL_COLOR(RED)]
log_toggle_display = [0]
max_lat_acc_colour = [gui.DL_COLOR(BLACK)]
max_long_acc_colour = [gui.DL_COLOR(BLACK)]
gnss_status = False
page = 0
swipe_r = 50
settings = False
speed_mph = const(0)
speed_kmh = const(1)
ms2_accel = const(0)
g_accel = const(1)
speed_list = {
    speed_kmh: ("KM/H", 3.6),
    speed_mph: ("MPH", 2.2369362921),
    }
speed_unit = 'Speed (mph)'
acceleration_list = {
    g_accel: ("G", 9.81),
    ms2_accel: ("M/S^2", 1),
}
accel_unit = '(m/s )'
accel_unit2 = '2'

class Screen_Value:
    """Class `Screen_Value` to determine the string value, multiplier, max value, and format"""
    def __init__(self, formatter="{:.02f}", multiplier=0):
        self.max_value = 0
        self.value = 0
        self.formatter = formatter
        self.string_value = [formatter.format(self.value)]
        self.multiplier = multiplier
        self.max_string_value = [self.formatter.format(self.max_value)]

    def update(self, value):
        self.value = value * self.multiplier
        self.string_value[0] = self.formatter.format(self.value)
    
    def max(self, value):
        self.value = value
        if abs(self.value) > abs(self.max_value):
            self.max_value = self.value
            self.max_string_value[0] = self.formatter.format(self.max_value)

# values to be displayed and update 
speedmph = Screen_Value("{:.02f}", 2.23693629)
speedkph = Screen_Value("{:.02f}", 3.6)
long_acc = Screen_Value("{:.02f}", 1)
lat_acc = Screen_Value("{:.02f}", 1)
max_long = Screen_Value("{:.02f}", 1)
max_lat = Screen_Value("{:.02f}", 1)
vertical_vel = Screen_Value("{:.02f}", 1)
long_acc_g = Screen_Value("{:.02f}", 1/9.80665)
lat_acc_g = Screen_Value("{:.02f}", 1/9.80665)
max_long_g = Screen_Value("{:.02f}", 1/9.80665)
max_lat_g = Screen_Value("{:.02f}", 1/9.80665)
trap_main = Custom_Shape([80, 215], 0, True, gui.RGB(0,0,0), gui.RGB(0, 36, 64), [118, 230], [118, 270], [80, 285])
trap_no_bar = Custom_Shape([0, 215], 0, True, gui.RGB(0,0,0), gui.RGB(0, 36, 64), [38, 230], [38, 270], [0, 285])
speed = speedmph
accel1 = lat_acc
accel2 = long_acc
accel3 = max_lat
accel4 = max_long

# retrieves the picture button name and check if it matches in the list
def get_picture_button(name):
    try:
        pb = next(pb for pb in buttons if pb.name == name)
    except:
        pb = None
    return pb

# Retrieves the logging status and sets the picture button to the relevant colour
def set_logging_status():
    status = vbo.get_status() & 2
    if not status:
        logging_colour[0] = gui.DL_COLOR(WHITE)
        get_picture_button('Record').set_colour((255, 255, 255))
    else:
        logging_colour[0] = gui.DL_COLOR(RED)
        get_picture_button('Record').set_colour((255, 0, 0))

# toggles the logging which starts and stops the vbo file
def toggle_logging(l):
    if vts.sd_present() == True:
        log_toggle_display[0] = 0 if log_toggle_display[0] else 0xffff
        if log_toggle_display[0]:
            vbo.start()
        else:
            vbo.stop()
    else:
        print("SD card not present")


def wrap_callback(callback):
    def cb(*args, **kwargs):
        callback(*args, **kwargs)
    return cb


def pass_cb(a):
    pass


def rerun_main_screen(l):
    main_screen()


# creating picture buttons and assigning callbacks
def create_buttons(*args):
    global buttons
    buttons = []
    if 'Reset' in args:
        buttons.append(Picture_Button(5, 400, bank.get('Reset'), 'Reset', reset_max_values))
    if 'GNSS' in args:
        buttons.append(Picture_Button(15, 10, bank.get('GNSS'), 'GNSS', pass_cb))
    if 'Settings' in args:
        buttons.append(Picture_Button(-15, 280, bank.get('Settings'), 'Settings', settings_page))
    if 'Record' in args:
        buttons.append(Picture_Button(5, 140, bank.get('Record'), 'Record', toggle_logging))
    if 'Exit' in args:
        buttons.append(Picture_Button(-10, 400, bank.get('Exit'), 'Exit', rerun_main_screen))

    button_cbs_l = []
    button_icons_l = [gui.DL_BEGIN(gui.PRIM_BITMAPS)]
    for i, button in enumerate(buttons):
        button_cb_l = [
            gui.PARAM_TAG_REGISTER,
            wrap_callback(button.get_callback()),
        ]
        button_cb_l.append(button.name)
        button_cbs_l.append(button_cb_l)
        button.set_gui_l_index(len(button_icons_l))
        button_icons_l.extend(button.generate_gui_l(i + 1))
    return button_cbs_l, button_icons_l

# defining the swipe function and setting a callback for the relevant page
def swipe_cb(gui_l, start):
    global page
    if start:
        pass
    else:
        si = gui.swipe_info()
        if si.dx <= -50:
            if page == 0:
                page += 1
        elif si.dx >= 50:
            if page > 0:
                page -= 1
        drawPage()

# Draws the relevant page pending on the swipe
def drawPage():
    if page == 0:
        return main_screen()
    else:
        return no_bar_screen()

# creates button list
def init_buttons():
    global button_layouts
    button_layouts = {}
    button_layouts['settings'] = create_buttons('Exit', 'GNSS')
    button_layouts['main'] = create_buttons('Reset', 'GNSS', 'Settings', 'Record')


def button_options():
    global button_layouts
    gui_buttons = []

    if settings == False:
        gui_buttons.extend(button_layouts['main'][0])
        gui_buttons.append(button_layouts['main'][1])
    elif settings == True:
        gui_buttons.extend(button_layouts['settings'][0])
        gui_buttons.append(button_layouts['settings'][1])

    return gui_buttons
    
# optains a new GNSS sample and updates the display elements and sets the max values
def gnss_callback():
    global sample
    sample = vbox.get_sample_hp()
    sats[0] = "{}".format(sample.sats_used)
    speedmph.update(sample.speed_gnd_mps)
    speedkph.update(sample.speed_gnd_mps)
    lat_acc.update(sample.latacc_smooth_mps2)
    long_acc.update(sample.lngacc_smooth_mps2)
    long_acc_g.update(sample.lngacc_smooth_mps2)
    lat_acc_g.update(sample.latacc_smooth_mps2)
    vertical_vel.update(sample.speed_up_mps)
    set_sats_status(gnss_status)
    set_max_values()

# handles the max values and updates the colour when appropriate
def set_max_values():
    if speedmph.value < 0.5 or speedkph.value < 0.5 or sample.sats_used == 0:
        speedmph.string_value[0] = "0.00"
        speedkph.string_value[0] = "0.00"
    max_long.max(long_acc.value)
    max_lat.max(lat_acc.value)
    max_lat_g.max(lat_acc_g.value)
    max_long_g.max(long_acc_g.value)
    if abs(max_lat.max_value) > 9.81 or abs(max_lat_g.max_value) > 1:
        max_lat_acc_colour[0] = gui.DL_COLOR(RED)
    if abs(max_long.max_value) > 9.81 or abs(max_long_g.max_value) > 1:
        max_long_acc_colour[0] = gui.DL_COLOR(RED)

#sets the gnss button colour
def set_gnss_btn_state(state):
    if state:
        get_picture_button('GNSS').set_colour((0, 255, 0))
    else:
        get_picture_button('GNSS').set_colour((255, 0,  0))

# sets the satellite counter colour
def set_sats_status(state):
    global gnss_status
    if sample.sats_used > 3:
        sats_colour[0] = gui.DL_COLOR(GREEN)
        gnss_status = True
    else:
        sats_colour[0] = gui.DL_COLOR(RED)
        gnss_status = False

# resets the max values when the reset button is pressed
def reset_max_values(a):
    max_long.max_value = 0
    max_lat.max_value = 0
    max_long_g.max_value = 0
    max_lat_g.max_value = 0
    max_long.max_string_value[0] = "0.00"
    max_lat.max_string_value[0] = "0.00"
    max_long_g.max_string_value[0] = "0.00"
    max_lat_g.max_string_value[0] = "0.00"
    max_long_acc_colour[0] = gui.DL_COLOR(BLACK)
    max_lat_acc_colour[0] = gui.DL_COLOR(BLACK)

# sends command to the gnss engine to do a gps coldstart
def gnss_coldstart(engine):
    gnss.command(b'\xb5\x62\x06\x04\x04\x00\xff\xff\x02\x00\x0e\x61')


def vsync_cb(b):
    global gnss_status
    set_gnss_btn_state(gnss_status)
    set_logging_status()
    gui.redraw()


def set_speed(btn):
    global speed_unit, speed
    if btn.current == 'MPH':
        speed_unit = 'Speed (mph)'
        speed = speedmph
    else:
        speed_unit = 'Speed (km/h)'
        speed = speedkph


def set_accel(btn):
    global accel_unit, accel_unit2, accel1, accel2, accel3, accel4
    if btn.current == 'M/S^2':
        accel_unit = '(m/s )'
        accel_unit2 = '2'
        accel1 = lat_acc
        accel2 = long_acc
        accel3 = max_long
        accel4 = max_lat
    else:
        accel_unit = '(g)'
        accel_unit2 = ''
        accel1 = lat_acc_g
        accel2 = long_acc_g
        accel3 = max_long_g
        accel4 = max_lat_g


def bar_press(press):
    global page
    if page == 0:
        if press[3] > 85 and press[3] < 120 and press[4] > 220 and press[4] < 280:
            page = 1
            no_bar_screen()
    elif page == 1:
        if press[3] > 0 and press[3] < 40 and press[4] > 200 and press[4] < 280:
            page = 0
            main_screen()
    else:
        pass

# Settings page gui list
def settings_page(a):
    global settings
    settings = True
    settings_gui = [
        [gui.EVT_VSYNC, vsync_cb],
        [gui.PARAM_CLRCOLOR, gui.RGB(255, 255, 255)],
        [gui.DL_COLOR_RGB(0, 36, 64)],
        [gui.PRIM_RECTS, [
            gui.DL_VERTEX2F(0, 0),
            gui.DL_VERTEX2F(80, 480)
        ]],
        [gui.DL_COLOR_RGB(0, 0, 0)],
        [gui.PRIM_LINE_STRIP, [
            gui.DL_LINE_WIDTH(2),
            gui.DL_VERTEX2F(80, 0),
            gui.DL_VERTEX2F(80, 480),
        ]],
        [gui.CTRL_TEXT, 120, 120, 31, 0, "Speed"],
        [gui.CTRL_TEXT, 120, 240, 31, 0, "Acceleration"],
        [gui.CTRL_TEXT, 120, 360, 31, 0, "Coldstart"],
        [gui.DL_COLOR_RGB(200, 0, 0)],
        [gui.CTRL_TEXT, 440, 10, 33, gui.OPT_CENTERX, "Settings"],
        [gui.DL_COLOR_RGB(255, 255, 255)],
        sats_colour,
        [gui.CTRL_TEXT, 65, 40, 23, gui.OPT_CENTERX, sats],
        ]
    settings_gui.extend(button_options())
    settings_gui.extend([
        speed_loopbutton(),
        acceleration_loopbutton(),
        [gui.CTRL_BUTTON, 500, 360, 200, 60, 30, 'Coldstart', gnss_coldstart],
        ])
    gui.show(settings_gui)

# gui list for the no bar page
def no_bar_screen():
    no_bar_list = [
        trap_no_bar(),
        [gui.EVT_VSYNC, vsync_cb],
        [gui.EVT_SWIPE, swipe_r, swipe_cb],
        [gui.EVT_PRESS, bar_press],
        [gui.PARAM_CLRCOLOR, gui.RGB(255, 255, 255)],
        [gui.DL_COLOR_RGB(200, 200, 200)],
        [gui.PRIM_RECTS, [
            gui.DL_VERTEX2F(0, 0),
            gui.DL_VERTEX2F(800, 50)
        ]],
        [gui.PRIM_RECTS, [
            gui.DL_VERTEX2F(0, 160),
            gui.DL_VERTEX2F(800, 210)
        ]],
        [gui.PRIM_RECTS, [
            gui.DL_VERTEX2F(0, 320),
            gui.DL_VERTEX2F(800, 370)
        ]],
        [gui.DL_COLOR_RGB(0, 0, 0)],
        [gui.PRIM_LINE_STRIP, [
            gui.DL_LINE_WIDTH(2),
            gui.DL_VERTEX2F(400, 0),
            gui.DL_VERTEX2F(800, 0),
            gui.DL_VERTEX2F(800, 480),
            gui.DL_VERTEX2F(0, 480),
            gui.DL_VERTEX2F(0, 0),
            gui.DL_VERTEX2F(400, 0),
            gui.DL_VERTEX2F(400, 480),
        ]],
        [gui.PRIM_LINE_STRIP, [
            gui.DL_LINE_WIDTH(1),
            gui.DL_VERTEX2F(0, 50),
            gui.DL_VERTEX2F(800, 50),
        ]],
        [gui.PRIM_LINE_STRIP, [
            gui.DL_LINE_WIDTH(1),
            gui.DL_VERTEX2F(0, 210),
            gui.DL_VERTEX2F(800, 210),
        ]],
        [gui.PRIM_LINE_STRIP, [
            gui.DL_LINE_WIDTH(1),
            gui.DL_VERTEX2F(0, 370),
            gui.DL_VERTEX2F(800, 370),
        ]],
        [gui.PRIM_LINE_STRIP, [
            gui.DL_LINE_WIDTH(2),
            gui.DL_VERTEX2F(0, 160),
            gui.DL_VERTEX2F(800, 160),
        ]],
        [gui.PRIM_LINE_STRIP, [
            gui.DL_LINE_WIDTH(2),
            gui.DL_VERTEX2F(0, 320),
            gui.DL_VERTEX2F(800, 320),
        ]],
        [gui.DL_COLOR_RGB(0, 0, 0)],
        [gui.PRIM_LINE_STRIP, [
            gui.DL_LINE_WIDTH(1.5),
            gui.DL_VERTEX2F(0, 215),
            gui.DL_VERTEX2F(38, 230),
            gui.DL_VERTEX2F(38, 270),
            gui.DL_VERTEX2F(0, 285),
        ]],
        [gui.DL_COLOR_RGB(255, 255, 255)],
        [gui.PRIM_LINE_STRIP, [
            gui.DL_LINE_WIDTH(2),
            gui.DL_VERTEX2F(10, 240),
            gui.DL_VERTEX2F(20, 250),
            gui.DL_VERTEX2F(10, 260),
        ]],
        [gui.PRIM_LINE_STRIP, [
            gui.DL_LINE_WIDTH(2),
            gui.DL_VERTEX2F(20, 240),
            gui.DL_VERTEX2F(30, 250),
            gui.DL_VERTEX2F(20, 260),
        ]],
        [gui.DL_COLOR_RGB(0, 0, 0)],
        [gui.CTRL_TEXT, 10, 10, 30, 0, speed_unit],
        [gui.CTRL_TEXT, 10, 170, 30, 0, "Lateral Accel " + accel_unit],
        [gui.CTRL_TEXT, 269, 170, 23, gui.OPT_CENTERX, accel_unit2],
        [gui.CTRL_TEXT, 10, 330, 30, 0, "Max Lateral Accel " + accel_unit],
        [gui.CTRL_TEXT, 335, 330, 23, gui.OPT_CENTERX, accel_unit2],
        [gui.CTRL_TEXT, 410, 10, 30, 0, "Vertical Velocity (m/s)"],
        [gui.CTRL_TEXT, 410, 170, 30, 0, "Long Accel " + accel_unit],
        [gui.CTRL_TEXT, 642, 170, 23, gui.OPT_CENTERX, accel_unit2],
        [gui.CTRL_TEXT, 410, 330, 30, 0, "Max Long Accel " + accel_unit],
        [gui.CTRL_TEXT, 709, 330, 23, gui.OPT_CENTERX, accel_unit2],
        [gui.CTRL_TEXT, 200, 50, 34, gui.OPT_CENTERX, speed.string_value],
        [gui.CTRL_TEXT, 600, 50, 34, gui.OPT_CENTERX, vertical_vel.string_value],
        [gui.CTRL_TEXT, 200, 210, 34, gui.OPT_CENTERX, accel1.string_value],
        [gui.CTRL_TEXT, 600, 210, 34, gui.OPT_CENTERX, accel2.string_value],
        max_lat_acc_colour,
        [gui.CTRL_TEXT, 200, 370, 34, gui.OPT_CENTERX, accel4.max_string_value],
        max_long_acc_colour,
        [gui.CTRL_TEXT, 600, 370, 34, gui.OPT_CENTERX, accel3.max_string_value],
    ]
    gui.show(no_bar_list)

# gui list for the page with a side bar
def main_screen():
    global main_display, settings
    settings = False
    vts.leds(* ([0] * 12))
    main_display = [
        [gui.EVT_VSYNC, vsync_cb],
        [gui.EVT_SWIPE, swipe_r, swipe_cb],
        [gui.EVT_PRESS, bar_press],
        ]
    main_display.extend([
        trap_main(),
        [gui.PARAM_CLRCOLOR, gui.RGB(255, 255, 255)],
        [gui.DL_COLOR_RGB(0, 36, 64)],
        [gui.PRIM_RECTS, [
            gui.DL_VERTEX2F(0, 0),
            gui.DL_VERTEX2F(80, 480)
        ]],
        [gui.DL_COLOR_RGB(200, 200, 200)],
        [gui.PRIM_RECTS, [
            gui.DL_VERTEX2F(80, 0),
            gui.DL_VERTEX2F(800, 50)
        ]],
        [gui.PRIM_RECTS, [
            gui.DL_VERTEX2F(80, 160),
            gui.DL_VERTEX2F(800, 210)
        ]],
        [gui.PRIM_RECTS, [
            gui.DL_VERTEX2F(80, 320),
            gui.DL_VERTEX2F(800, 370)
        ]],
        [gui.DL_COLOR_RGB(0, 0, 0)],
        [gui.PRIM_LINE_STRIP, [
            gui.DL_LINE_WIDTH(2),
            gui.DL_VERTEX2F(440, 0),
            gui.DL_VERTEX2F(800, 0),
            gui.DL_VERTEX2F(800, 480),
            gui.DL_VERTEX2F(80, 480),
            gui.DL_VERTEX2F(80, 0),
            gui.DL_VERTEX2F(440, 0),
            gui.DL_VERTEX2F(440, 480),
        ]],
        [gui.PRIM_LINE_STRIP, [
            gui.DL_LINE_WIDTH(1),
            gui.DL_VERTEX2F(80, 50),
            gui.DL_VERTEX2F(800, 50),
        ]],
        [gui.PRIM_LINE_STRIP, [
            gui.DL_LINE_WIDTH(1),
            gui.DL_VERTEX2F(80, 210),
            gui.DL_VERTEX2F(800, 210),
        ]],
        [gui.PRIM_LINE_STRIP, [
            gui.DL_LINE_WIDTH(1),
            gui.DL_VERTEX2F(80, 370),
            gui.DL_VERTEX2F(800, 370),
        ]],
        [gui.PRIM_LINE_STRIP, [
            gui.DL_LINE_WIDTH(2),
            gui.DL_VERTEX2F(80, 160),
            gui.DL_VERTEX2F(800, 160),
        ]],
        [gui.PRIM_LINE_STRIP, [
            gui.DL_LINE_WIDTH(2),
            gui.DL_VERTEX2F(80, 320),
            gui.DL_VERTEX2F(800, 320),
        ]],
        [gui.PRIM_LINE_STRIP, [
            gui.DL_LINE_WIDTH(1.5),
            gui.DL_VERTEX2F(80, 215),
            gui.DL_VERTEX2F(118, 230),
            gui.DL_VERTEX2F(118, 270),
            gui.DL_VERTEX2F(80, 285),
        ]],
        [gui.DL_COLOR_RGB(255, 255, 255)],
        [gui.PRIM_LINE_STRIP, [
            gui.DL_LINE_WIDTH(2),
            gui.DL_VERTEX2F(110, 240),
            gui.DL_VERTEX2F(100, 250),
            gui.DL_VERTEX2F(110, 260),
        ]],
        [gui.PRIM_LINE_STRIP, [
            gui.DL_LINE_WIDTH(2),
            gui.DL_VERTEX2F(100, 240),
            gui.DL_VERTEX2F(90, 250),
            gui.DL_VERTEX2F(100, 260),
        ]],
        [gui.DL_COLOR_RGB(0, 0, 0)],
        [gui.CTRL_TEXT, 90, 10, 30, 0, speed_unit],
        [gui.CTRL_TEXT, 90, 170, 30, 0, "Lateral Velocity " + accel_unit],
        [gui.CTRL_TEXT, 382, 170, 23, gui.OPT_CENTERX, accel_unit2],
        [gui.CTRL_TEXT, 90, 330, 30, 0, "Max Lateral Accel " + accel_unit],
        [gui.CTRL_TEXT, 415, 330, 23, gui.OPT_CENTERX, accel_unit2],
        [gui.CTRL_TEXT, 450, 10, 30, 0, "Vertical Velocity (m/s)"],
        [gui.CTRL_TEXT, 450, 170, 30, 0, "Long Accel " + accel_unit],
        [gui.CTRL_TEXT, 680, 170, 23, gui.OPT_CENTERX, accel_unit2],
        [gui.CTRL_TEXT, 450, 330, 30, 0, "Max Long Accel " + accel_unit],
        [gui.CTRL_TEXT, 748, 330, 23, gui.OPT_CENTERX, accel_unit2],
        [gui.CTRL_TEXT, 260, 50, 34, gui.OPT_CENTERX, speed.string_value],
        [gui.CTRL_TEXT, 620, 50, 34, gui.OPT_CENTERX, vertical_vel.string_value],
        [gui.CTRL_TEXT, 260, 210, 34, gui.OPT_CENTERX, accel1.string_value],
        [gui.CTRL_TEXT, 620, 210, 34, gui.OPT_CENTERX, accel2.string_value],
        max_lat_acc_colour,
        [gui.CTRL_TEXT, 260, 370, 34, gui.OPT_CENTERX, accel4.max_string_value],
        max_long_acc_colour,
        [gui.CTRL_TEXT, 620, 370, 34, gui.OPT_CENTERX, accel3.max_string_value],
        [gui.DL_COLOR_RGB(255, 255, 255)],
        sats_colour,
        [gui.CTRL_TEXT, 65, 40, 23, gui.OPT_CENTERX, sats],
        logging_colour,
        [gui.CTRL_TEXT, 15, 120, 30, 0, "REC"],
    ]) 
    main_display.extend(button_options())
    gui.show(main_display)

# main application that loads in the images, runs the functions, and checking for GPS signal
def main():
    global bank, speed_loopbutton, acceleration_loopbutton
    speed_loopbutton = LoopingButton(500, 120, 200, 50, [x[0] for x in speed_list.values()], 30, set_speed)
    acceleration_loopbutton = LoopingButton(500, 240, 200, 50, [x[0] for x in acceleration_list.values()], 30, set_accel)
    bank = Image_Bank((
        ('/sd/icon-reset.png', 'Reset'),
        ('/sd/icons8-gnss-50.png', 'GNSS'),
        ('/sd/icon-settings.png', 'Settings'),
        ('/sd/icon-record.png', 'Record'),
        ('/sd/icon-exit.png', 'Exit'),
    ))
    init_buttons()
    main_screen()
    while (gnss.init_status() > 0):
        pass
    try:
        vbox.init(vbox.VBOX_SRC_GNSS_BASIC)
    except Exception as e:
        if str(e) == "VBox source already configured":
            pass
        else:
            print(e)
    vbox.set_new_data_callback(gnss_callback)

if __name__ == '__main__':
    main()
else:
    main()