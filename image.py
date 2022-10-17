##
# @module    image
# @brief     Image object
# @version   1.0
#

import ft8xx as ft
import gui
import ustruct as us

class Image:
    # Maximum image dimensions: 1023 x 511
    def __init__(self, file_name, mem_start):
        self.start = mem_start

        with open(file_name, 'rb') as f:
            img = f.read()
        bmp_dl, self.end, self.width, self.height = \
            self.decompress_PNG(img, self.start)

        # Check if first command is PALETTE_SOURCE
        if self.is_CMD_PALETTE_SOURCE(bmp_dl[0]):
            self.plt_source = self.get_source_from_PALETTE_SOURCE(bmp_dl[0])
        else:
            self.plt_source = None
        # We do not need the first command anymore
        bmp_dl = bmp_dl[1:]

        self.bmp_source = self.get_source_from_BITMAP_SOURCE(bmp_dl[0])
        self.format = self.get_format_from_BITMAP_LAYOUT(bmp_dl[2])
        self.stride = self.get_stride_from_BITMAP_LAYOUT(bmp_dl[2])

    def generate_gui_l(self, tag=None, pos=None):
        self.gui_l = []
        if tag is not None:
            self.gui_l.append(gui.DL_TAG(tag))
        if self.plt_source is not None:
            self.gui_l.append(gui.DL_PALETTE_SOURCE(self.plt_source))
        self.gui_l.extend([
            gui.DL_BITMAP_SOURCE(self.bmp_source),
            gui.DL_BITMAP_LAYOUT(
                self.format,
                self.stride & 1023,
                self.height & 511
            ),
            gui.DL_BITMAP_SIZE(
                0, 0, 0, self.width & 511, self.height & 511),
        ])
        if pos is not None:
            self.gui_l.append([gui.DL_VERTEX2F(pos[0], pos[1])])
        return self.gui_l

    def get_end(self):
        return self.end

    def is_CMD_PALETTE_SOURCE(self, cmd):
        return (cmd >> 24) == 0x2a

    def get_source_from_PALETTE_SOURCE(self, cmd):
        return cmd & 0x3fffff

    def get_source_from_BITMAP_SOURCE(self, cmd):
        return cmd & 0x3fffff

    def get_format_from_BITMAP_LAYOUT(self, cmd):
        return (cmd >> 19) & 0x1f

    def get_stride_from_BITMAP_LAYOUT(self, cmd):
        return (cmd >> 9) & 0x3ff

    def decompress_PNG(self, img, ptr):
        props = bytes(12)
        bmp_dl_b = bytes(24)

        gui.pause(True)
        ft.cp_start()
        ft.cp_cmd(gui.DL_CLEAR(1, 1, 1))
        ft.cpcmd_text(400, 240, 30, gui.OPT_CENTER, 'Loading...')
        # On executing CMD_LOADIMAGE the FT81x will create 5 or 6 display list
        # commands, in this order:
        # - PALETTE_SOURCE (only if image has a palette)
        # - BITMAP_SOURCE
        # - BITMAP_LAYOUT_H
        # - BITMAP_LAYOUT
        # - BITMAP_SIZE_H
        # - BITMAP_SIZE
        ft.cpcmd_loadimage(ptr, 0, len(img), ft.addressof(img))
        ft.cpcmd_getprops(ft.addressof(props))
        ft.rdbuf(ft.RAM_DL + ft.rd32(ft.REG_CMD_DL) - 24, bmp_dl_b)
        ft.cp_finish()
        gui.pause(False)

        end, width, height = us.unpack('LLL', props)
        bmp_dl = us.unpack('LLLLLL', bmp_dl_b)

        return bmp_dl, end, width, height


class Image_Bank:
    def __init__(self, img_descriptions, ptr=ft.RAM_G):
        self.start = ptr
        self.bank = {}
        for file_name, image_name in img_descriptions:
            new_image = Image(file_name, self.start)
            self.bank[image_name] = new_image
            self.start = new_image.get_end()

    def get(self, name):
        return self.bank[name]
