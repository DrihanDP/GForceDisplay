##
# @module    button_utils
# @brief     Basic Buttons
# @version   1.0
##

import gui


class Basic_btn:

    def __init__(self, x, y, width, height, init_value, font=28, cb=None, ignore_cb_response=False, formatting='{}'):
        self.text = [formatting.format(init_value)]
        self.font = [font]
        self.gui_l = [gui.CTRL_FLATBUTTON, x, y, width, height, self.font, self.text, self.btn_cb]
        self.cb = cb
        self.ignore_cb_response = ignore_cb_response
        self.value = init_value
        self.formatting = formatting

    def __call__(self):
        return self.gui_l

    def btn_cb(self, btn):
        if self.cb:
            ret = self.cb(self, btn)
            if (ret is not None) and (not self.ignore_cb_response):
                self.value = ret
                self.text[0] = self.formatting.format(ret)

    def set_value(self, value):
        self.value = value
        self.text[0] = self.formatting.format(value)

    def set_font(self, font):
        self.font[0] = font

    def get_value(self):
        return self.value


class LoopingButton:

    def __init__(self, x, y, width, height, options, font = 7, cb = None):
        self.idx = 0
        self.options = options
        self.current = self.options[self.idx]
        self.len = len(options) - 1
        self.text = [str(self.options[self.idx])]
        self.gui_l = [gui.CTRL_FLATBUTTON, x, y, width, height, font, self.text, self.btn_cb]
        self.cb = cb
        self.set_value = self.set_btn

    def __call__(self):
        return self.gui_l

    def btn_cb(self, btn):
        if self.idx == self.len:
            self.idx = 0
        else:
            self.idx += 1
        self.text[0] = str(self.options[self.idx])
        self.current = self.options[self.idx]
        if self.cb:
            self.cb(self)

    def set_btn(self, var = None, idx = None):
        if var != None:
            self.idx = self.options.index(var)
            self.text[0] = str(self.options[self.idx])
        elif idx != None:
            self.idx = idx
            self.text[0] = str(self.options[self.idx])

    def get_value(self):
        return self.current

    def get_id(self):
        return self.idx


class Outline_Btn(Basic_btn):

    def __init__(self, x, y, width, height, init_value, font=30, cb=None, ignore_cb_response=False,
                        formatting='{}', line_width=4, outline_colour=0x555555, fill_colour=0x0, text_colour=0xFFFFFF):

        super().__init__(x, y, width, height, init_value, font, cb, ignore_cb_response, formatting)
        self.outline_colour = [gui.DL_COLOR(outline_colour)]
        self.fill_colour = [0xffffff0a, gui.DL_COLOR(fill_colour)] if (fill_colour != None) else [gui.DL_NOP()]*2
        self.default_colour = [0xffffff0a, gui.DL_COLOR(0x003870)] if (fill_colour != None) else [gui.DL_NOP()]*2



        self.gui_l = [  gui.SUBLIST,
                        [gui.DL_SAVE_CONTEXT(),
                        gui.DL_LINE_WIDTH(line_width),
                        gui.DL_COLOR(outline_colour),
                        gui.DL_BEGIN(gui.PRIM_RECTS),
                        gui.DL_VERTEX2F(x, y),
                        gui.DL_VERTEX2F(x+width, y+height),
                        gui.DL_END(),
                        gui.DL_COLOR(text_colour)],
                        self.fill_colour,
                        [gui.CTRL_FLATBUTTON, x, y, width, height, self.font, self.text, self.btn_cb],
                        self.default_colour,
                        [gui.DL_RESTORE_CONTEXT()],
                        ]

    def set_outline_colour(self, colour):
        self.outline_colour[0] = gui.DL_COLOR(colour)

    def set_fill_colour(self, colour):
        if colour is None:
            self.fill_colour[0], self.fill_colour[1] = gui.DL_NOP(), gui.DL_NOP()
            self.default_colour[0], self.default_colour[1] = gui.DL_NOP(), gui.DL_NOP()
        else:
            self.fill_colour[0], self.fill_colour[1] = 0xffffff0a, gui.DL_COLOR(colour)
            self.default_colour[0], self.default_colour[1] = 0xffffff0a, gui.DL_COLOR(0x003870)  