####

import gui
import math
import vts
import vbox
import vbo
import gnss
import backlight
import json
from os import getcwd
from screenshot import screenshot_cb
from picture_button import Picture_Button
from image import Image_Bank
from gui_utils import ScreenFilter, Reduc_Filter, Colours, LoopingButton
from screen_utils import Screen, ScreenManager, LiveDisplayParameter, LiveDisplayValue
from sounds import Speaker
from coldstart import coldstart
from unit_info import Unit
from micropython import const



class Application:
    '''Use like a Singleton to store application information'''
    version             = '1.0.0.16'
    unit_info           = vts.unit_info()
    image_bank          = None
    buttons             = None
    gnss_valid          = False
    vehicle_static      = True
    min_speed_threshold = 0.1389
    state_period_ms     = 0
    last_sample         = None
    get_sample          = vbox.get_sample_hp if Unit.supports_hp_sample() else vbox.get_sample
    rtc_mask            = vbox.VBOX_FLG_VALID_DATE | vbox.VBOX_FLG_VALID_TIME
    rtc_validated       = False
    header_colour_rgb   = (0, 41, 66)
    batt_pack           = None

    class Data:
        sats = 0
        speed_ms = 0.0
        lat_ms2 = 0.0
        lng_ms2 = 0.0
        peak_acc = 0.0
        peak_dec = 0.0
        peak_lat = 0.0
        lat_acc_smoother = Reduc_Filter(length=4)
        lng_acc_smoother = Reduc_Filter(length=4)

        @classmethod
        def reset_peaks(cls):
            cls.peak_acc = 0.0
            cls.peak_dec = 0.0
            cls.peak_lat = 0.0

    class UserSettings:
        LOG_CONTINUOUS  = const(0)
        LOG_WHEN_MOVING = const(1)
        LOG_MANUAL      = const(-1) #Not a settings option

        SPEED_UNITS_KMH = const(0)
        SPD_UNITS_MPH   = const(1)
        SPD_UNITS_MS    = const(2)

        ACCEL_UNITS_MS2 = const(0)
        ACCEL_UNITS_G   = const(1)

        BRIGHTNESS_AUTO = const(0)

        speed_units_dict = {
            SPEED_UNITS_KMH: ('KM/H', 3.6),
            SPD_UNITS_MPH: ('MPH', 2.2369362921),
            # SPD_UNITS_MS: ('M/S', 1.0),
        }
        accel_units_dict = {
            ACCEL_UNITS_MS2: ('M/S2', 1.0),
            ACCEL_UNITS_G: ('G', 0.1019716213),
        }
        log_mode_dict = {
            LOG_CONTINUOUS: ("CONTINUOUS", 0),
            LOG_WHEN_MOVING: ("MOVING", 1),
        }
        screen_brightness_dict = {
            BRIGHTNESS_AUTO: ('AUTO', 0),
            1: ('1', (1 * 20)**2),
            2: ('2', (2 * 20)**2),
            3: ('3', (3 * 20)**2),
            4: ('4', (4 * 20)**2),
            5: ('5', (5 * 20)**2),
        }
        if Unit.info['Light Sensor'] == 'NONE':
            screen_brightness_dict[BRIGHTNESS_AUTO] = ('0', 200)

        _speed_units_index = SPEED_UNITS_KMH
        _accel_units_index = ACCEL_UNITS_MS2
        _log_mode_index = LOG_CONTINUOUS
        _screen_brightness_index = BRIGHTNESS_AUTO

        ##### SETTINGS #####
        speed_units = speed_units_dict[_speed_units_index][1]
        accel_units = accel_units_dict[_accel_units_index][1]
        log_mode = log_mode_dict[_log_mode_index][1]
        screen_brightness = screen_brightness_dict[_screen_brightness_index][1]

        @classmethod
        def set_user_speed_units(cls, index):
            try:
                cls.speed_units = cls.speed_units_dict[index][1]
                cls._speed_units_index = index

            except IndexError:
                cls.speed_units = cls.speed_units_dict[cls.SPEED_UNITS_KMH][1]
                cls._speed_units_index = cls.SPEED_UNITS_KMH

        @classmethod
        def set_user_accel_units(cls, index):
            try:
                cls.accel_units = cls.accel_units_dict[index][1]
                cls._accel_units_index = index
            except IndexError:
                cls.accel_units = cls.accel_units_dict[cls.ACCEL_UNITS_MS2][1]
                cls._accel_units_index = cls.ACCEL_UNITS_MS2

        @classmethod
        def set_log_mode(cls, index):
            try:
                cls.log_mode = cls.log_mode_dict[index][1]
                cls._log_mode_index = index
            except IndexError:
                cls.log_mode = cls._log_mode_index = cls.LOG_CONTINUOUS

        @classmethod
        def set_brightness(cls, index):
            try:
                if index == cls.BRIGHTNESS_AUTO and cls.screen_brightness_dict[index][1] == cls.BRIGHTNESS_AUTO:
                        backlight.set_auto(25, 1000, 400)
                else:
                    backlight.set(cls.screen_brightness_dict[index][1])
                cls.screen_brightness = cls._screen_brightness_index = index
            except IndexError:
                backlight.set_auto(25, 1000, 400)
                cls.screen_brightness = cls._screen_brightness_index = cls.BRIGHTNESS_AUTO

        @classmethod
        def load_from_file(cls):
            try:
                with open('/sd/g_force_settings.json') as file:
                    settings_file = json.load(file)

                cls.set_user_speed_units(settings_file['speed_units'])
                cls.set_user_accel_units(settings_file['accel_units'])
                cls.set_log_mode(settings_file['log_mode'])
                cls.set_brightness(settings_file['screen_brightness'])

            except OSError:
                pass #No SD Card or file not yet created

            except Exception as e:
                #Unknown Settings error, remove the file
                print("Settings File Error: ", str(e))
                try:
                    from os import unlink
                    unlink('/sd/g_force_settings.json')
                except Exception as e:
                    print("Unable to remove Settings File: ", str(e))

        @classmethod
        def save_settings(cls):
            file_to_save = {
                "speed_units": cls._speed_units_index,
                "accel_units": cls._accel_units_index,
                "log_mode": cls._log_mode_index,
                "screen_brightness": cls._screen_brightness_index
            }
            try:
                with open('/sd/g_force_settings.json', 'w+') as file:
                    json.dump(file_to_save, file)
            except OSError:
                pass #No SD Card

    @classmethod
    def get_picture_button(cls, name):
        try:
            pb = next(pb for pb in cls.buttons if pb.name == name)
        except:
            pb = None
        return pb

    @classmethod
    def run_loop(cls):
        pass
        # while True:
        #     animation_manager.run()

    @classmethod
    def set_rtc(cls, sample):
        time = tod_to_hmsm(sample.tod_ms)
        rtc = vts.clock_get()
        rtc['year'] = sample.year
        rtc['month'] = sample.month
        rtc['day of month'] = sample.day
        rtc['hours'] = time[0]
        rtc['minutes'] = time[1]
        rtc['seconds'] = time[2]
        rtc['day of week'] = 0
        try:
            vts.clock_set(rtc)
            Application.rtc_validated = True
        except RuntimeError:
            pass

    @classmethod
    def sd_callback(cls, state):
        cls.update_logging_status()

    @classmethod
    def sd_card_ok(cls):
        return (vts.get_sdcard_state() == 2)

    @classmethod
    def start_logging(cls):
        try:
            if not (cls.logging_active()) and cls.sd_card_ok():
                vbo.start()
        except OSError:
            #Should never get here!
            print("OS ERROR - LOGGING ABORTED")

    @classmethod
    def pause_logging(cls, pause):
        vbo.pause(pause)

    @classmethod
    def stop_logging(cls):
        vbo.stop()

    @classmethod
    def logging_active(cls):
        from vbo import get_status, VBO_STATUS_OPENING, VBO_STATUS_READY, VBO_STATUS_PAUSED
        status = get_status()
        if (status & (VBO_STATUS_OPENING | VBO_STATUS_READY) != 0):
            if (status & VBO_STATUS_PAUSED == 0):
                return True
        return False

    @classmethod
    def logging_paused(cls):
        from vbo import get_status, VBO_STATUS_PAUSED
        return True if (get_status() & (VBO_STATUS_PAUSED)==(VBO_STATUS_PAUSED)) else False

    @classmethod
    def logging_file_open(cls):
        from vbo import get_status, VBO_STATUS_READY
        return True if (get_status() & (VBO_STATUS_READY) == VBO_STATUS_READY) else False

    @classmethod
    def toggle_logging(cls, l=None):
        cls.UserSettings.log_mode = cls.UserSettings.LOG_MANUAL
        if (cls.logging_active()):
            # Currently logging is active so close the current file and stop logging
            cls.stop_logging()
        elif (cls.logging_file_open()):
            # Currently logging is paused so close the current file and restart logging
            cls.stop_logging()
            vts.delay_ms(100) #safety to allow for closing and reopening file
            cls.start_logging()
        else:
            # Not currently logging so start if media is available
            cls.start_logging()

    @classmethod
    def update_logging_status(cls):
        if not cls.sd_card_ok():
            if cls.logging_file_open():
                cls.stop_logging()
            return

        log_mode = cls.UserSettings.log_mode
        if log_mode == cls.UserSettings.LOG_WHEN_MOVING:

            if cls.gnss_valid:
                if not cls.logging_active() and not (cls.vehicle_static):
                    cls.start_logging() if (not cls.logging_paused()) else cls.pause_logging(False)

                elif cls.logging_active() and not cls.sd_card_ok():
                    cls.stop_logging()

                else:
                    if (cls.logging_active()) and (abs(cls.state_period_ms) > 3000):
                        #check logging active and stationary for more than 3 seconds
                        cls.pause_logging(True)

        elif log_mode == cls.UserSettings.LOG_CONTINUOUS:
            if not cls.logging_file_open() and cls.gnss_valid:
                cls.start_logging()

        elif log_mode == cls.UserSettings.LOG_MANUAL:
            pass #Don't try to control logging when in manual mode

        else: #Unknown logging mode, set to default
            print("ERROR: Unknown Logging mode, set to default (CONTINUOUS)")
            cls.UserSettings.set_log_mode(cls.UserSettings.LOG_CONTINUOUS)

class GDisplay:
    def __init__(self, x, y, r):
        self.x      = x
        self.y      = y
        self.r      = r
        self.val    = (0, 0)
        self.filter = (ScreenFilter(), ScreenFilter())
        self.gui_l  = [
            gui.SUBLIST,
            [
                gui.DL_SAVE_CONTEXT(),
                gui.DL_SCISSOR_SIZE(2 * self.r, 2 * self.r),
                gui.DL_SCISSOR_XY(self.x - self.r, self.y - self.r),
                gui.DL_COLOR_RGB(*Application.header_colour_rgb),
                gui.DL_POINT_SIZE(self.r),
                gui.DL_BEGIN(gui.PRIM_POINTS),
                gui.DL_VERTEX2F(self.x, self.y),
                gui.DL_END(),
                gui.DL_COLOR(Colours.white),
                gui.DL_POINT_SIZE(self.r*.66),
                gui.DL_BEGIN(gui.PRIM_POINTS),
                gui.DL_VERTEX2F(self.x, self.y),
                gui.DL_END(),
                gui.DL_COLOR_RGB(*Application.header_colour_rgb),
                gui.DL_POINT_SIZE(self.r*.66-3),
                gui.DL_BEGIN(gui.PRIM_POINTS),
                gui.DL_VERTEX2F(self.x, self.y),
                gui.DL_END(),
                gui.DL_COLOR(Colours.white),
                gui.DL_POINT_SIZE(self.r*.33),
                gui.DL_BEGIN(gui.PRIM_POINTS),
                gui.DL_VERTEX2F(self.x, self.y),
                gui.DL_END(),
                gui.DL_COLOR_RGB(*Application.header_colour_rgb),
                gui.DL_POINT_SIZE(self.r*.33-3),
                gui.DL_BEGIN(gui.PRIM_POINTS),
                gui.DL_VERTEX2F(self.x, self.y),
                gui.DL_END(),
                gui.DL_COLOR_RGB(*Application.header_colour_rgb),
                gui.DL_COLOR_A(255),
                gui.DL_RESTORE_CONTEXT(),
                gui.DL_COLOR(Colours.white),
                gui.DL_LINE_WIDTH(2),
                gui.DL_BEGIN(gui.PRIM_LINES),
                gui.DL_VERTEX2F(self.x - self.r + 2, self.y),
                gui.DL_VERTEX2F(self.x + self.r - 2, self.y),
                gui.DL_VERTEX2F(self.x, self.y - self.r + 2),
                gui.DL_VERTEX2F(self.x, self.y + self.r - 2),
                gui.DL_END(),
                gui.DL_COLOR(Colours.red),
                gui.DL_POINT_SIZE(self.r * .1),
            ],
            [gui.PRIM_POINTS, [gui.DL_VERTEX2F(*self.val)]],
        ]

    def draw(self):
        return self.gui_l

    def update_vals(self, lat,lon):
        if lat > 1.5:
            lat = 1.5
        elif lat < -1.5:
            lat = -1.5
        if lon > 1.5:
            lon = 1.5
        elif lon < -1.5:
            lon = -1.5
        self.val = ((lat*(self.r*.66)),(lon*(self.r*.66)))

    def update(self):
        a = gui.DL_VERTEX2F(
            self.x + self.filter[0](self.val[0]),
            self.y + self.filter[1](self.val[1]),
            )
        self.gui_l[2][1][0] = a

############# SCREENS ##############
class ScreenBase(Screen):

    def __init__(self):
        super().__init__()
        self.title_left       = ['G-FORCE METER']
        self.title_right      = ['']
        self.press_sound_func = speaker.play_sound
        self.press_sound      = speaker.snd_click
        if Application.batt_pack:
            self.battery_icon_l   = Application.batt_pack.graphic.list
            self.gui_title_r_xpos = 700
        else:
            self.battery_icon_l   = [gui.DL_NOP()]
            self.gui_title_r_xpos = 750
            self.filter           = (ScreenFilter(), ScreenFilter()) #Shared between Lat/Lng Screens

    def setup(self):
        super().setup()

        self.gui_list.append([
		    gui.DL_SAVE_CONTEXT(),
            gui.DL_CLEAR_COLOR_RGB(*Application.header_colour_rgb),
            gui.DL_CLEAR(1, 1, 1),
            gui.DL_SCISSOR_SIZE(800, 350),
            gui.DL_SCISSOR_XY(0, 65),
            gui.DL_CLEAR_COLOR_RGB(255, 255, 255),
            gui.DL_CLEAR(1, 1, 1),
            gui.DL_RESTORE_CONTEXT(),
            gui.DL_COLOR_RGB(255, 255, 255),
        ])

        self.gui_list.append(self.battery_icon_l)

        self.add_button_icons()

        self.gui_list.append([gui.DL_COLOR_RGB(255, 255, 255)])
        self.gui_list.append([gui.CTRL_TEXT, 30, 7, 8, 0, self.title_left])
        self.gui_list.append([gui.CTRL_TEXT, self.gui_title_r_xpos, 7, 8, gui.OPT_RIGHTX, self.title_right])

    def vsync_cb(self, l):
        set_media_btn_state(Application.sd_card_ok())
        set_gnss_btn_state(Application.gnss_valid)
        set_logging_btn_state(Application.logging_active())
        g_disp.update() #not needed on settings screen but here for simplicity
        super().vsync_cb(l)

class PeakScreen(ScreenBase):
    def __init__(self):
        super().__init__()
        self.title_right[0]     = 'PEAK'
        self.units              = LiveDisplayParameter()
        self.picture_buttons    = [ Application.get_picture_button('Reset'),
                                    Application.get_picture_button('Screenshot'),
                                    Application.get_picture_button('GNSS'),
                                    Application.get_picture_button('Media'),
                                    Application.get_picture_button('Back'),
                                    Application.get_picture_button('Forward'),
                                    Application.get_picture_button('Settings'),
                                    Application.get_picture_button('Record'),
                                ]
        self.peak_lat_acc       = LiveDisplayValue(0, '{:+.2f}', max=99.9)
        self.peak_lng_accel     = LiveDisplayValue(0, '{:+.2f}', max=99.9)
        self.peak_lng_decel     = LiveDisplayValue(0, '{:+.2f}', max=99.9)
        self.combo_g            = LiveDisplayValue(0, '{:.2f} G', max=99.9, scale=
                        Application.UserSettings.accel_units_dict[Application.UserSettings.ACCEL_UNITS_G][1])

    def setup(self):
        Application.get_picture_button('Forward').set_colour(gui.DL_COLOR(Colours.grey))
        Application.get_picture_button('Back').set_colour(gui.DL_COLOR(Colours.white))
        Application.get_picture_button('Back').set_callback(self.previous_screen)
        Application.get_picture_button('Reset').set_callback(self.reset)

        self.units.update(Application.UserSettings.accel_units_dict[Application.UserSettings._accel_units_index][0])

        for parameter in (self.peak_lat_acc, self.peak_lng_accel, self.peak_lng_decel):
            parameter.set_scale(Application.UserSettings.accel_units)
            parameter.set_format("{:+.2f}" if
                                (Application.UserSettings._accel_units_index == Application.UserSettings.ACCEL_UNITS_G)
                                else "{:+05.1f}")
            parameter.update()


        super().setup()
        self.gui_list.extend([
            g_disp.draw(),
            [gui.DL_COLOR(Colours.black)],
            [gui.CTRL_TEXT, 470, 100, 8, gui.OPT_RIGHTX
            
            ,'PEAK LAT'],
            [gui.CTRL_TEXT, 470, 145, 7, gui.OPT_RIGHTX, self.units.display_val],
            [gui.CTRL_TEXT, 470, 220, 8, gui.OPT_RIGHTX
            
            ,'PEAK ACC'],
            [gui.CTRL_TEXT, 470, 265, 7, gui.OPT_RIGHTX, self.units.display_val],
            [gui.CTRL_TEXT, 470, 340, 8, gui.OPT_RIGHTX
            
            ,'PEAK DEC'],
            [gui.CTRL_TEXT, 470, 385, 7, gui.OPT_RIGHTX, self.units.display_val],
            [gui.DL_COLOR_RGB(0, 128, 255)],
            [gui.CTRL_TEXT, 780, 65, 9, gui.OPT_RIGHTX, self.peak_lat_acc.display_val],
            [gui.DL_COLOR_RGB(0, 128, 0)],
            [gui.CTRL_TEXT, 780, 185, 9, gui.OPT_RIGHTX, self.peak_lng_accel.display_val],
            [gui.DL_COLOR(Colours.red)],
            [gui.CTRL_TEXT, 780, 305, 9, gui.OPT_RIGHTX, self.peak_lng_decel.display_val],
            [gui.DL_COLOR(Colours.black)],
            [gui.CTRL_TEXT, 150, 330, 8, gui.OPT_CENTERX, self.combo_g.display_val],
        ])

    def previous_screen(self, gui_l):
        ScreenManager.Set_Screen('Live')

    def teardown(self):
        Application.get_picture_button('Back').set_callback(default_cb)
        super().teardown()

    def swipe_cb(self, l, start):
        if not start:
            swipe = gui.swipe_info()
            if swipe.dx >= self.swipe_r:
                self.previous_screen(None)

    def reset(self, l):
        Application.Data.reset_peaks()
        self.combo_g.update(0.0)

    def new_data_cb(self):
        lat = Application.Data.lat_ms2
        lon = Application.Data.lng_ms2

        self.peak_lng_accel.update(Application.Data.peak_acc)
        self.peak_lng_decel.update(Application.Data.peak_dec)
        self.peak_lat_acc.update(Application.Data.peak_lat)

        lat = self.filter[0](lat)
        lon = self.filter[1](lon)
        self.combo_g.update(math.sqrt(lat**2 + lon**2))

class LiveScreen(ScreenBase):
    def __init__(self):
        super().__init__()
        self.title_right[0]  = 'LIVE'
        self.accel_units     = LiveDisplayParameter()
        self.speed_units     = LiveDisplayParameter()
        self.picture_buttons = [Application.get_picture_button('Screenshot'),
                                Application.get_picture_button('GNSS'),
                                Application.get_picture_button('Media'),
                                Application.get_picture_button('Back'),
                                Application.get_picture_button('Forward'),
                                Application.get_picture_button('Settings'),
                                Application.get_picture_button('Record'),
        ]
        self.speed           = LiveDisplayValue(0, '{:05.1f}', max=999.9, min=0)
        self.lat_acc         = LiveDisplayValue(0, '{:+.2f}', max=99.9)
        self.lng_acc         = LiveDisplayValue(0, '{:+.2f}', max=99.9)
        self.combo_g         = LiveDisplayValue(0, '{:.2f} G', max=99.9, scale=
                        Application.UserSettings.accel_units_dict[Application.UserSettings.ACCEL_UNITS_G][1])

    def setup(self):
        Application.get_picture_button('Forward').set_callback(self.next_screen)
        Application.get_picture_button('Forward').set_colour(gui.DL_COLOR(Colours.white))
        Application.get_picture_button('Back').set_colour(gui.DL_COLOR(Colours.grey))

        self.accel_units.update(Application.UserSettings.accel_units_dict[Application.UserSettings._accel_units_index][0])
        self.speed_units.update(Application.UserSettings.speed_units_dict[Application.UserSettings._speed_units_index][0])

        for parameter in (self.lat_acc, self.lng_acc):
            parameter.set_scale(Application.UserSettings.accel_units)
            parameter.set_format("{:+.2f}" if
                                (Application.UserSettings._accel_units_index == Application.UserSettings.ACCEL_UNITS_G)
                                else "{:+05.1f}")
            parameter.update()


        self.speed.set_scale(Application.UserSettings.speed_units)

        super().setup()
        self.gui_list.extend([
            g_disp.draw(),
            [gui.DL_COLOR(Colours.black)],
            [gui.CTRL_TEXT, 470, 100, 8, gui.OPT_RIGHTX,'LAT ACC'], #310
            [gui.CTRL_TEXT, 470, 145, 7, gui.OPT_RIGHTX, self.accel_units.display_val],
            [gui.CTRL_TEXT, 470, 220, 8, gui.OPT_RIGHTX,'LNG ACC'],
            [gui.CTRL_TEXT, 470, 265, 7, gui.OPT_RIGHTX, self.accel_units.display_val],
            [gui.CTRL_TEXT, 470, 340, 8, gui.OPT_RIGHTX,'SPEED'],
            [gui.CTRL_TEXT, 470, 385, 7, gui.OPT_RIGHTX, self.speed_units.display_val],
            [gui.DL_COLOR_RGB(0, 128, 255)],
            [gui.CTRL_TEXT, 780, 65, 9, gui.OPT_RIGHTX, self.lat_acc.display_val ],
            [gui.DL_COLOR_RGB(0, 128, 0)],
            [gui.CTRL_TEXT, 780, 185, 9, gui.OPT_RIGHTX, self.lng_acc.display_val],
            [gui.DL_COLOR(Colours.red)],
            [gui.CTRL_TEXT, 780, 305, 9, gui.OPT_RIGHTX, self.speed.display_val],
            [gui.DL_COLOR(Colours.black)],
            [gui.CTRL_TEXT, 150, 330, 8, gui.OPT_CENTERX, self.combo_g.display_val],
        ])

    def next_screen(self, gui_l):
        ScreenManager.Set_Screen('Peak')

    def swipe_cb(self, l, start):
        if not start:
            swipe = gui.swipe_info()
            if swipe.dx <= -self.swipe_r:
                self.next_screen(None)

    def teardown(self):
        Application.get_picture_button('Forward').set_callback(default_cb)
        super().teardown()

    def new_data_cb(self):
        lat = Application.Data.lat_ms2
        lon = Application.Data.lng_ms2

        self.lat_acc.update(lat)
        self.lng_acc.update(lon)
        self.speed.update(Application.Data.speed_ms)

        lat = self.filter[0](lat)
        lon = self.filter[1](lon)
        self.combo_g.update(math.sqrt(lat**2 + lon**2))

class SettingsScreen(ScreenBase):

    @classmethod
    def open_settings(cls, l):
        ScreenManager.Set_Screen('Settings')

    def __init__(self):
        super().__init__()
        self.title_right[0]     = 'SETTINGS'
        self.picture_buttons    = [ Application.get_picture_button('Exit'),
                                    Application.get_picture_button('Screenshot'),
                                    Application.get_picture_button('GNSS'),
                                    Application.get_picture_button('Media'),
                                    Application.get_picture_button('Record'),
        ]
        self.sats_used          = LiveDisplayValue(format='{:02}')
        self.speed_units_btn    = LoopingButton(200,  90, 150, 50,
                                    [x[0] for x in Application.UserSettings.speed_units_dict.values()], 7, self.speed_unit_cb)
        self.accel_units_btn    = LoopingButton(200, 170, 150, 50,
                                [x[0] for x in Application.UserSettings.accel_units_dict.values()], 7, self.accel_unit_cb)
        self.logging_type_btn   = LoopingButton(200, 250, 150, 50,
                                [x[0] for x in Application.UserSettings.log_mode_dict.values()], 7, self.log_mode_cb)
        self.brightness_btn     = LoopingButton(200, 330, 150, 50,
                                [x[0] for x in Application.UserSettings.screen_brightness_dict.values()], 7, self.brightness_cb)


    def setup(self):
        super().setup()
        self.speed_units_btn.set_btn(idx=Application.UserSettings._speed_units_index)
        self.accel_units_btn.set_btn(idx=Application.UserSettings._accel_units_index)
        self.logging_type_btn.set_btn(idx=Application.UserSettings._log_mode_index)
        self.brightness_btn.set_btn(idx=Application.UserSettings._screen_brightness_index)

        self.gui_list.extend([
            [gui.DL_COLOR_RGB(0, 0, 0)],
            [gui.CTRL_TEXT,  10, 100, 7, 0, 'SPEED'],
            [gui.CTRL_TEXT,  10, 180, 7, 0, 'ACCELERATION'],
            [gui.CTRL_TEXT,  10, 260, 7, 0, 'LOGGING'],
            [gui.CTRL_TEXT, 10,  330, 7, 0, 'SCREEN'],
            [gui.CTRL_TEXT, 10, 355, 7, 0, 'BRIGHTNESS'],
            [gui.CTRL_TEXT, 410, 90, 7, 0, 'VBOX INFORMATION'],
            [gui.CTRL_TEXT, 420, 130, 7, 0, 'SERIAL NUMBER'],
                [gui.CTRL_TEXT, 620, 130, 29, 0, str(Unit.info['Serial Number'])],
            [gui.CTRL_TEXT, 420, 160, 7, 0, 'HARDWARE'],
                [gui.CTRL_TEXT, 620, 160, 29, 0, Unit.info['PCB Info']],
            [gui.CTRL_TEXT, 420, 190, 7, 0, 'APP VERSION'],
                [gui.CTRL_TEXT, 620, 190, 29, 0, Application.version],
            [gui.CTRL_TEXT, 420, 220, 7, 0, 'SYS VERSION'],
                [gui.CTRL_TEXT, 620, 220, 29, 0, Unit.info['Firmware Version']],
            [gui.CTRL_TEXT,  420, 280, 7, 0, 'SATELLITES:'],
                [gui.CTRL_TEXT, 600, 280, 7, 0, self.sats_used.display_val],
            [
                gui.DL_LINE_WIDTH(1),
                gui.DL_BEGIN(gui.PRIM_LINES),
                gui.DL_VERTEX2F(400, 65),
                gui.DL_VERTEX2F(400, 415),
                gui.DL_VERTEX2F(400, 260),
                gui.DL_VERTEX2F(800, 260),
            ],
            [gui.DL_COLOR_RGB(255, 255, 255)],
            self.speed_units_btn(),
            self.accel_units_btn(),
            self.logging_type_btn(),
            self.brightness_btn(),
            [gui.CTRL_FLATBUTTON, 475, 320, 250, 80, 8, 'COLDSTART', coldstart_cb],
        ])

    def speed_unit_cb(self, btn):
        Application.UserSettings.set_user_speed_units(btn.get_id())

    def accel_unit_cb(self, btn):
        Application.UserSettings.set_user_accel_units(btn.get_id())

    def log_mode_cb(self, btn):
        pass #set log mode when leaving settings

    def brightness_cb(self, btn):
        Application.UserSettings.set_brightness(btn.get_id())

    def teardown(self):
        super().teardown()
        if (Application.UserSettings.log_mode != Application.UserSettings.LOG_MANUAL) or (not Application.logging_active()):
            Application.UserSettings.set_log_mode(self.logging_type_btn.get_id())
        Application.UserSettings.save_settings()

    def new_data_cb(self):
        self.sats_used.update(Application.Data.sats)


############# Misc Functions ##############

def load_fonts():
    from font import load_font
    path = getcwd() + '/'
    start, end = load_font(path + 'BebasNeue_0-28.rft',     7)
    start, end = load_font(path + 'BebasNeue Bold-56.rft',  8, mempos_end=start)
    start, end = load_font(path + 'BebasNeue Bold-140.rft', 9, mempos_end=start)
    start, end = load_font(path + 'BebasNeue Bold-200.rft', 10, mempos_end=start)

def set_gnss_btn_state(state):
    if state:
        Application.get_picture_button('GNSS').set_colour(gui.DL_COLOR(Colours.green))
    else:
        Application.get_picture_button('GNSS').set_colour(gui.DL_COLOR(Colours.red))

def set_media_btn_state(media):
    if media:
        Application.get_picture_button('Media').set_colour(gui.DL_COLOR(Colours.green))
    else:
        Application.get_picture_button('Media').set_colour(gui.DL_COLOR(Colours.red))

def set_logging_btn_state(logging):
    if logging:
        Application.get_picture_button('Record').set_colour(gui.DL_COLOR(Colours.red))
    else:
        Application.get_picture_button('Record').set_colour(gui.DL_COLOR_RGB(*Application.header_colour_rgb))

def default_cb(*args, **kwargs):
    pass

def coldstart_cb(l):
    vts.leds(*[0,20,0]*4)
    vbo.set_coldstart()
    coldstart()
    vts.delay_ms(250)
    vts.leds(*[0]*12)

def tod_to_hmsm(ms):
    hmsm = 4 * [None]
    hmsm[0] = ms // 3600000
    ms -= (hmsm[0] * 3600000)
    hmsm[1] = ms // 60000
    ms -= (hmsm[1] * 60000)
    hmsm[2] = ms // 1000
    ms -= (hmsm[2] * 1000)
    hmsm[3] = ms
    return hmsm

def sample_cb():
    sample = Application.get_sample()
    Application.Data.sats = sample.sats_used

    if sample.sats_used >= 3 and 2 <= sample.fix_type:
        Application.gnss_valid = True
        smooth_speed = 0.0 if (sample.flags & vbox.VBOX_FLG_STATIONARY) else sample.speed_gnd_smooth_mps


        if (Application.last_sample is not None) and (smooth_speed > Application.min_speed_threshold):

            Application.vehicle_static = False
            Application.state_period_ms = 0
            
            if Unit.supports_hp_sample():
                latacc = sample.latacc_smooth_mps2 # Smoothing set to off in setup
            else:
                #Older Version of Code did not pass smoothed_latacc to python level
                roc_heading = sample.heading_deg - Application.last_sample.heading_deg
                if roc_heading > 300:
                    roc_heading = -360 + roc_heading
                if roc_heading < -300:
                    roc_heading = 360 + roc_heading
                if roc_heading == 0:
                    roc_heading = 0.00001

                roc_heading = roc_heading / (sample.update_period_ms/1000)

                latacc = -1 * sample.speed_gnd_mps * roc_heading * (math.pi / 180)

            MPS_to_G = Application.UserSettings.accel_units_dict[Application.UserSettings.ACCEL_UNITS_G][1]
            g_disp.update_vals(latacc*MPS_to_G, sample.lngacc_smooth_mps2*MPS_to_G)


            #low-level smoothing disabled to '*_smooth' values are not really smoothed
            Application.Data.lat_acc_smoother.push(latacc)
            Application.Data.lng_acc_smoother.push(sample.lngacc_smooth_mps2)

            smth_lat = Application.Data.lat_ms2 = Application.Data.lat_acc_smoother.get()
            smth_lng = Application.Data.lng_ms2 = Application.Data.lng_acc_smoother.get()
            Application.Data.speed_ms = sample.speed_gnd_disp_mps

            if smth_lng > Application.Data.peak_acc:
                Application.Data.peak_acc = smth_lng
            if smth_lng < Application.Data.peak_dec:
                Application.Data.peak_dec = smth_lng
            if abs(smth_lat) > abs(Application.Data.peak_lat):
                Application.Data.peak_lat = smth_lat


        else:
            Application.vehicle_static = True
            Application.state_period_ms += sample.state_period_ms
            g_disp.update_vals(0,0)
            Application.Data.lat_ms2 = Application.Data.lng_ms2 = Application.Data.speed_ms = 0.0

        Application.last_sample = sample
    else:
        Application.gnss_valid = False

    if (not Application.rtc_validated) and (not Application.logging_active()) and ((sample.flags & Application.rtc_mask) == Application.rtc_mask):
        Application.set_rtc(sample)

    ScreenManager.Current_Screen.new_data_cb()
    Application.update_logging_status()

# Main #########################################################################
def main():
    vts.upy_callbacks(False)
    global speaker
    speaker = Speaker(255)
    vts.config({'uPyIntChar': 3})

    global g_disp
    g_disp = GDisplay(150, 200, 120)

    path = getcwd() + '/'

    Application.image_bank = Image_Bank((
        (path + 'icon-reset.png',              'Reset'),
        (path + 'icon-screenshot.png',         'Screenshot'),
        (path + 'icons8-gnss-50.png',          'GNSS'),
        (path + 'icons8-sdcard-50.png',        'Media'),
        (path + 'icon-backwards.png',          'Back'),
        (path + 'icon-forwards.png',           'Forward'),
        (path + 'icon-settings.png',           'Settings'),
        (path + 'icon-record.png',             'Record'),
        (path + 'icon-exit.png',               'Exit'),
        (path + 'icon-battery-charging.png',	'BatCharging'),
        (path + 'icon-battery-empty.png',	    'BatEmpty'),
        (path + 'icon-battery-outline-thin.png','BatOutline'),
    ))
    load_fonts()
    Application.UserSettings.load_from_file()

    Application.buttons = [
        Picture_Button(468, 410, Application.image_bank.get('Screenshot'),'Screenshot',screenshot_cb),
        Picture_Button(183, 410, Application.image_bank.get('Reset'),'Reset', None),
        Picture_Button(420,  10, Application.image_bank.get('Media'), 'Media', Application.toggle_logging),
        Picture_Button(340,  10, Application.image_bank.get('GNSS'), 'GNSS', default_cb),
        Picture_Button(620,  410, Application.image_bank.get('Back'), 'Back', default_cb),
        Picture_Button(720,  410, Application.image_bank.get('Forward'), 'Forward', default_cb),
        Picture_Button(480,  -12, Application.image_bank.get('Record'), 'Record', default_cb, Application.header_colour_rgb),
        Picture_Button(0,  410, Application.image_bank.get('Settings'), 'Settings', SettingsScreen.open_settings),
        Picture_Button(0,  410, Application.image_bank.get('Exit'), 'Exit', ScreenManager.switch_to_last_screen),
    ]

    if (Unit.is_pbox()):
        from extpack import Battery_Pack
        from digitalio import set_callback
        Application.batt_pack = Battery_Pack(Application.image_bank.get('BatEmpty'),
                                            Application.image_bank.get('BatCharging'),
                                            Application.image_bank.get('BatOutline'))

        set_callback(Application.batt_pack.event_cb)

    while (gnss.init_status() > 0):
        pass # Waiting for GNSS Engine to Initialise
    try:
        vbox.init(vbox.VBOX_SRC_GNSS_BASIC)
    except Exception as e:
        if str(e) == 'VBox source already configured':
            pass
        else:
            raise Exception(str(e))

    try:
        vbox.set_config({   'StationarySpeed': Application.min_speed_threshold,
                            'SmoothLevelSpdDisp': 4,
                            'SmoothLevelLngAccData': 1, #handle smoothing in python level instead
                            'SmoothLevelLatAccData':1, #see above
                        })
    except Exception as e:
        print(e)
        #Older code does not support this, rely on screen smoothing
        pass

    vbo.set_appinfo('G-Force Meter {}.{}.{}.{}'.format(0,0,0,0))
    vbox.set_new_data_callback(sample_cb)
    vts.set_sd_callback(Application.sd_callback)

    ScreenManager.Add_Screen(SettingsScreen(), 'Settings')
    ScreenManager.Add_Screen(PeakScreen(), 'Peak')
    ScreenManager.Add_Screen(LiveScreen(), 'Live', start=True)

    vts.upy_callbacks(True)


if __name__ == '__main__':
    main()