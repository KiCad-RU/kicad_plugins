# cfp_rus_wizard.py
#
# Copyright (C) 2016,2017 Eldar Khayrullin <eldar.khayrullin@mail.ru>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

''' KiCad PCBNew Footprint Wizard script for creating CFP Russian housings '''

from __future__ import division
import pcbnew

import FootprintWizardBase
import PadArray as PA


class CFPRUSWizard(FootprintWizardBase.FootprintWizard):
    ''' Plugin class '''

    n_v_key = 'n vertical on side'
    n_h_key = 'n horizontal on side'
    pitch_v_key = 'pitch vertical'
    pitch_h_key = 'pitch horizontal'
    pad_width_key = 'pad width'
    pad_length_key = 'pad length'
    install_size_v_key = 'install size vertical'
    install_size_h_key = 'install size horizontal'
    key_left_top_key = 'key left top'

    package_height_key = 'package height'
    package_width_key = 'package width'
    crtyrd_margin_key = 'courtyard margin'

    def GetName(self):
        return "CFP RUS"

    def GetDescription(self):
        return "Ceramic Dual/Quad Flat (CFP) Russia Package footprint wizard"

    def GenerateParameterList(self):
        self.AddParam("Pads", self.n_v_key, self.uInteger, 8, min_value=0)
        self.AddParam("Pads", self.n_h_key, self.uInteger, 0, min_value=0)
        self.AddParam("Pads", self.pitch_v_key, self.uMM, 1.25)
        self.AddParam("Pads", self.pitch_h_key, self.uMM, 1.25)
        self.AddParam("Pads", self.pad_width_key, self.uMM, 0.8)
        self.AddParam("Pads", self.pad_length_key, self.uMM, 2.1)
        self.AddParam("Pads", self.install_size_v_key, self.uMM, 18.3)
        self.AddParam("Pads", self.install_size_h_key, self.uMM, 18.3)
        self.AddParam("Pads", self.key_left_top_key, self.uBool, True)

        self.AddParam("Package", self.package_height_key, self.uMM, 12.0)
        self.AddParam("Package", self.package_width_key, self.uMM, 9.5)
        self.AddParam("Package", self.crtyrd_margin_key, self.uMM, 1.0)

    def CheckParameters(self):
        pass

    def GetValue(self):
        return "CFP-%d" % ((self.parameters["Pads"][self.n_v_key] * 2 +
                            self.parameters["Pads"][self.n_h_key] * 2))

    def BuildThisFootprint(self):
        n_v = self.parameters["Pads"][self.n_v_key]
        n_h = self.parameters["Pads"][self.n_h_key]
        pitch_v = self.parameters["Pads"][self.pitch_v_key]
        pitch_h = self.parameters["Pads"][self.pitch_h_key]
        pad_length = self.parameters["Pads"][self.pad_length_key]
        pad_width = self.parameters["Pads"][self.pad_width_key]
        install_size_v = self.parameters["Pads"][self.install_size_v_key]
        install_size_h = self.parameters["Pads"][self.install_size_h_key]
        key_left_top = self.parameters["Pads"][self.key_left_top_key]

        package_height = self.parameters["Package"][self.package_height_key]
        package_width = self.parameters["Package"][self.package_width_key]
        crtyrd_margin = self.parameters["Package"][self.crtyrd_margin_key]

        v_pad = PA.PadMaker(self.module).SMDPad(pad_width, pad_length,
                                                shape=pcbnew.PAD_SHAPE_RECT)
        h_pad = PA.PadMaker(self.module).SMDPad(pad_width, pad_length,
                                                shape=pcbnew.PAD_SHAPE_RECT,
                                                rot_degree=90.0)

        v_pos = (install_size_v - pad_length) / 2
        h_pos = (install_size_h - pad_length) / 2

        # left row
        if key_left_top:
            pin1_pos = pcbnew.wxPoint(-h_pos, 0)
            array = PA.PadLineArray(v_pad, n_v, pitch_v, True, pin1_pos)
            array.SetFirstPadInArray(1)
            array.AddPadsToModule(self.draw)
            next_pad = n_v + 1
        else:
            n_pads = (n_v + n_h) * 2
            nbot = n_v // 2
            ntop = n_v - nbot
            if ntop > nbot:
                vtop_pos = pitch_v * (ntop - 1) / 2
                vbot_pos = pitch_v * (nbot + 1) / 2
            else:
                vtop_pos = pitch_v * ntop / 2
                vbot_pos = pitch_v * nbot / 2

            pin1_pos = pcbnew.wxPoint(-h_pos, -vtop_pos)
            array = PA.PadLineArray(v_pad, ntop, pitch_v, True, pin1_pos)
            array.SetFirstPadInArray(n_pads - ntop + 1)
            array.AddPadsToModule(self.draw)

            pin1_pos = pcbnew.wxPoint(-h_pos, vbot_pos)
            array = PA.PadLineArray(v_pad, nbot, pitch_v, True, pin1_pos)
            array.SetFirstPadInArray(1)
            array.AddPadsToModule(self.draw)
            next_pad = nbot + 1

        # bottom row
        pin1_pos = pcbnew.wxPoint(0, v_pos)
        array = PA.PadLineArray(h_pad, n_h, pitch_h, False, pin1_pos)
        array.SetFirstPadInArray(next_pad)
        array.AddPadsToModule(self.draw)
        next_pad += n_h

        # right row
        pin1_pos = pcbnew.wxPoint(h_pos, 0)
        array = PA.PadLineArray(v_pad, n_v, -pitch_v, True, pin1_pos)
        array.SetFirstPadInArray(next_pad)
        array.AddPadsToModule(self.draw)
        next_pad += n_v

        # top row
        pin1_pos = pcbnew.wxPoint(0, -v_pos)
        array = PA.PadLineArray(h_pad, n_h, -pitch_h, False, pin1_pos)
        array.SetFirstPadInArray(next_pad)
        array.AddPadsToModule(self.draw)

        # Silk Screen
        thick = self.draw.GetLineThickness()
        silk_margin = thick * 2
        lim_x = package_width / 2
        lim_y = package_height / 2
        inner_x = pitch_h * (n_h - 1) / 2 + pad_width / 2 + silk_margin
        inner_y = pitch_v * (n_v - 1) / 2 + pad_width / 2 + silk_margin
        inst_gap_v = (install_size_v - package_height) / 2
        inst_gap_h = (install_size_h - package_width) / 2

        # top and bottom
        if n_h == 0 or inst_gap_v >= pad_length + silk_margin:
            self.draw.Line(-lim_x, -lim_y, lim_x, -lim_y)
            self.draw.Line(-lim_x, lim_y, lim_x, lim_y)
        else:
            self.draw.Line(-lim_x, -lim_y, -inner_x, -lim_y)
            self.draw.Line(lim_x, -lim_y, inner_x, -lim_y)
            self.draw.Line(-lim_x, lim_y, -inner_x, lim_y)
            self.draw.Line(lim_x, lim_y, inner_x, lim_y)
        # left and right
        if n_v == 0 or inst_gap_h >= pad_length + silk_margin:
            self.draw.Line(-lim_x, -lim_y, -lim_x, lim_y)
            self.draw.Line(lim_x, -lim_y, lim_x, lim_y)
        else:
            self.draw.Line(-lim_x, -lim_y, -lim_x, -inner_y)
            self.draw.Line(-lim_x, lim_y, -lim_x, inner_y)
            self.draw.Line(lim_x, -lim_y, lim_x, -inner_y)
            self.draw.Line(lim_x, lim_y, lim_x, inner_y)

        # pins
        # horizontal
        if n_h != 0 and inst_gap_v >= pad_length + silk_margin * 2:
            top_x = -pitch_h * (n_h - 1) / 2
            lpin = ((install_size_v - package_height) / 2 - pad_length -
                    silk_margin)
            for i in range(0, n_h):
                pin_x = top_x + pitch_h * i
                self.draw.VLine(pin_x, -package_height / 2, -lpin)
                self.draw.VLine(pin_x, package_height / 2, lpin)
        # vertical
        if n_v != 0 and inst_gap_h >= pad_length + silk_margin * 2:
            top_y = -pitch_v * (n_v - 1) / 2
            lpin = ((install_size_h - package_width) / 2 - pad_length -
                    silk_margin)
            for i in range(0, n_v):
                pin_y = top_y + pitch_v * i
                self.draw.HLine(-package_width / 2, pin_y, -lpin)
                self.draw.HLine(package_width / 2, pin_y, lpin)

        # key
        key_thick = thick * 2
        key_len = pcbnew.FromMM(1.5)
        self.draw.SetLineThickness(key_thick)
        if key_left_top:
            key_x = -(lim_x + thick / 2)
            key_y = -(inner_y + key_thick / 2 - thick / 2)
            key_len = -(install_size_h / 2 + key_x - key_thick / 2)
        elif ntop > nbot:
            key_x = -(install_size_h / 2 + key_thick * 2)
            key_y = pitch_v
            key_len = -key_len
        else:
            key_x = -(install_size_h / 2 + key_thick * 2)
            key_y = pitch_v / 2
            key_len = -key_len
        self.draw.HLine(key_x, key_y, key_len)
        self.draw.SetLineThickness(thick)

        # Fabrication
        self.draw.SetLayer(pcbnew.F_Fab)
        thick = pcbnew.FromMM(0.1)
        self.draw.SetLineThickness(thick)
        fab_margin = thick
        lim_x = package_width / 2
        lim_y = package_height / 2
        inner_x = pitch_h * (n_h - 1) / 2 + pad_width / 2 + silk_margin
        inner_y = pitch_v * (n_v - 1) / 2 + pad_width / 2 + silk_margin
        inst_gap_v = (install_size_v - package_height) / 2
        inst_gap_h = (install_size_h - package_width) / 2

        # top and bottom
        self.draw.Line(-lim_x, -lim_y, lim_x, -lim_y)
        self.draw.Line(-lim_x, lim_y, lim_x, lim_y)
        # left and right
        self.draw.Line(-lim_x, -lim_y, -lim_x, lim_y)
        self.draw.Line(lim_x, -lim_y, lim_x, lim_y)

        # key
        key_r = pcbnew.FromMM(0.5)
        key_margin = thick + pcbnew.FromMM(0.5)
        key_x = -(lim_x - key_r - key_margin)
        if key_left_top:
            key_y = -pitch_v * (n_v - 1) / 2
        elif ntop > nbot:
            key_y = pitch_v
        else:
            key_y = pitch_v / 2
        self.draw.Circle(key_x, key_y, key_r)

        self.draw.SetLineThickness(thick)

        # Courtyard
        self.draw.SetLayer(pcbnew.F_CrtYd)
        if n_v == 0:
            size_x = package_width + crtyrd_margin * 2
        else:
            size_x = install_size_h + crtyrd_margin * 2
        if n_h == 0:
            size_y = package_height + crtyrd_margin * 2
        else:
            size_y = install_size_v + crtyrd_margin * 2
        # round size to nearest 0.1mm,
        # rectangle will thus land on a 0.05mm grid
        size_x = pcbnew.PutOnGridMM(size_x, 0.1)
        size_y = pcbnew.PutOnGridMM(size_y, 0.1)
        # set courtyard line thickness to the one defined in KLC
        thick = self.draw.GetLineThickness()
        self.draw.SetLineThickness(pcbnew.FromMM(0.05))
        self.draw.Box(0, 0, size_x, size_y)
        # restore line thickness to previous value
        self.draw.SetLineThickness(thick)

        # Reference and Value
        text_size = self.GetTextSize()  # IPC nominal
        text_y = size_y / 2 + text_size

        self.draw.Value(0, text_y, text_size)
        self.draw.Reference(0, -text_y, text_size)

        # Set module attribute
        self.module.SetAttributes(pcbnew.MOD_DEFAULT)


CFPRUSWizard().register()
