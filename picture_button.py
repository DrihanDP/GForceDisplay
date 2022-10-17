##
# @module    picture_button
# @brief     Button object with a picture
# @version   1.1
##

import gui

class Picture_Button:

    def __init__(self, x, y, image, name, callback=None, colour=(255,255,255)):
        self.pos = (x, y)
        self.image = image
        self.name = name
        self.callback = callback
        self.gui_l_index = None
        self.gui_col = [gui.DL_COLOR_RGB(*colour)]

    def generate_gui_l(self, tag):
        gui_l = [gui.DL_NOP(), self.gui_col] #first item in list can't be another list
        gui_l.extend(self.image.generate_gui_l(tag, self.pos))
        return gui_l

    def get_callback(self):
        return self.callback

    def set_callback(self, callback):
        self.callback = callback

    def set_gui_l_index(self, index):
        self.gui_l_index = index

    def set_pos(self, pos):
        self.image.set_pos(pos)

    def set_colour(self, colour):
        self.gui_col[0] = gui.DL_COLOR_RGB(*colour) if isinstance(colour, tuple) else colour

