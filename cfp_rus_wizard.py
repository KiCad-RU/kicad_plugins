# cfp_rus_wizard.py
#
# Copyright (C) 2016 Eldar Khayrullin <eldar.khayrullin@mail.ru>
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

from __future__ import division
import pcbnew

import HelpfulFootprintWizardPlugin as HFPW
import PadArray as PA


class CFPRUSWizard(HFPW.HelpfulFootprintWizardPlugin):

    n_V_key = 'n vertical'
    n_H_key = 'n horizontal'
    pitch_V_key = 'pitch vertical'
    pitch_H_key = 'pitch horizontal'
    pad_width_key = 'pad width'
    pad_length_key = 'pad length'
    install_size_V_key = 'install size vertical'
    install_size_H_key = 'install size horizontal'
    key_left_top_key = 'key left top'

    package_height_key = "package height"
    package_width_key = "package width"
    courtyard_margin_key = "courtyard margin"

    def GetName(self):
        return "CFP RUS"

    def GetDescription(self):
        return "Ceramic Dual/Quad Flat Russia Package footprint wizard"

    def GenerateParameterList(self):
        self.AddParam("Pads", self.n_V_key, self.uNatural, 16)
        self.AddParam("Pads", self.n_H_key, self.uNatural, 16)
        self.AddParam("Pads", self.pitch_V_key, self.uMM, 1.0)
        self.AddParam("Pads", self.pitch_H_key, self.uMM, 1.0)
        self.AddParam("Pads", self.pad_width_key, self.uMM, 0.6)
        self.AddParam("Pads", self.pad_length_key, self.uMM, 2.0)
        self.AddParam("Pads", self.install_size_V_key, self.uMM, 21.5)
        self.AddParam("Pads", self.install_size_H_key, self.uMM, 21.5)
        self.AddParam("Pads", self.key_left_top_key, self.uBool, False)

        self.AddParam("Package", self.package_height_key, self.uMM, 18.6)
        self.AddParam("Package", self.package_width_key, self.uMM, 18.6)
        self.AddParam("Package", self.courtyard_margin_key, self.uMM, 1.0)

    def CheckParameters(self):
        self.CheckParamBool("Pads", '*' + self.key_left_top_key)

    def GetValue(self):
        return "CFP-%d" % ((self.parameters["Pads"]["*" + self.n_V_key] * 2 +
                             self.parameters["Pads"]["*" + self.n_H_key] * 2))

    def BuildThisFootprint(self):
        n_V = self.parameters["Pads"]['*' + self.n_V_key]
        n_H = self.parameters["Pads"]['*' + self.n_H_key]
        pitch_V = self.parameters["Pads"][self.pitch_V_key]
        pitch_H = self.parameters["Pads"][self.pitch_H_key]
        pad_length = self.parameters["Pads"][self.pad_length_key]
        pad_width = self.parameters["Pads"][self.pad_width_key]
        install_size_V = self.parameters["Pads"][self.install_size_V_key]
        install_size_H = self.parameters["Pads"][self.install_size_H_key]
        key_left_top = self.parameters["Pads"]['*' + self.key_left_top_key]

        package_height = self.parameters["Package"][self.package_height_key]
        package_width = self.parameters["Package"][self.package_width_key]
        courtyard_margin = self.parameters["Package"][self.courtyard_margin_key]

        v_pad = PA.PadMaker(self.module).SMDPad(pad_width, pad_length,
                                                shape=pcbnew.PAD_SHAPE_RECT)
        h_pad = PA.PadMaker(self.module).SMDPad(pad_width, pad_length,
                                                shape=pcbnew.PAD_SHAPE_RECT,
                                                rot_degree=90.0)

        v_pos = (install_size_V - pad_length) / 2
        h_pos = (install_size_H - pad_length) / 2

        #left row
        if key_left_top:
            pin1Pos = pcbnew.wxPoint(-h_pos, 0)
            array = PA.PadLineArray(v_pad, n_V, pitch_V, True, pin1Pos)
            array.SetFirstPadInArray(1)
            array.AddPadsToModule(self.draw)
            next_pad = n_V + 1
        else:
            n_pads = (n_V + n_H) * 2
            nbot = n_V // 2
            ntop = n_V - nbot
            if ntop > nbot:
                vtop_pos = pitch_V * (ntop - 1) / 2
                vbot_pos = pitch_V * (nbot + 1) / 2
            else:
                vtop_pos = pitch_V * ntop / 2
                vbot_pos = pitch_V * nbot / 2

            pin1Pos = pcbnew.wxPoint(-h_pos, -vtop_pos)
            array = PA.PadLineArray(v_pad, ntop, pitch_V, True, pin1Pos)
            array.SetFirstPadInArray(n_pads - ntop + 1)
            array.AddPadsToModule(self.draw)

            pin1Pos = pcbnew.wxPoint(-h_pos, vbot_pos)
            array = PA.PadLineArray(v_pad, nbot, pitch_V, True, pin1Pos)
            array.SetFirstPadInArray(1)
            array.AddPadsToModule(self.draw)
            next_pad = nbot + 1

        #bottom row
        pin1Pos = pcbnew.wxPoint(0, v_pos)
        array = PA.PadLineArray(h_pad, n_H, pitch_H, False, pin1Pos)
        array.SetFirstPadInArray(next_pad)
        array.AddPadsToModule(self.draw)
        next_pad += n_H

        #right row
        pin1Pos = pcbnew.wxPoint(h_pos, 0)
        array = PA.PadLineArray(v_pad, n_V, -pitch_V, True, pin1Pos)
        array.SetFirstPadInArray(next_pad)
        array.AddPadsToModule(self.draw)
        next_pad += n_V

        #top row
        pin1Pos = pcbnew.wxPoint(0, -v_pos)
        array = PA.PadLineArray(h_pad, n_H, -pitch_H, False, pin1Pos)
        array.SetFirstPadInArray(next_pad)
        array.AddPadsToModule(self.draw)

        thick = self.draw.GetLineThickness()
        lim_x = package_width / 2
        lim_y = package_height / 2
        inner_x = pitch_H * (n_H - 1) / 2 + thick * 4
        inner_y = pitch_V * (n_V - 1) / 2 + thick * 4

        # Silk Screen
        # top and bottom
        if n_H == 0:
            self.draw.Line(-lim_x, -lim_y, lim_x, -lim_y)
            self.draw.Line(-lim_x, lim_y, lim_x, lim_y)
        else:
            self.draw.Line(-lim_x, -lim_y, -inner_x, -lim_y)
            self.draw.Line(lim_x, -lim_y, inner_x, -lim_y)
            self.draw.Line(-lim_x, lim_y, -inner_x, lim_y)
            self.draw.Line(lim_x, lim_y, inner_x, lim_y)
        # left and right
        if n_V == 0:
            self.draw.Line(-lim_x, -lim_y, -lim_x, lim_y)
            self.draw.Line(lim_x, -lim_y, lim_x, lim_y)
        else:
            self.draw.Line(-lim_x, -lim_y, -lim_x, -inner_y)
            self.draw.Line(-lim_x, lim_y, -lim_x, inner_y)
            self.draw.Line(lim_x, -lim_y, lim_x, -inner_y)
            self.draw.Line(lim_x, lim_y, lim_x, inner_y)

        # key
        keyt = thick * 2
        self.draw.SetLineThickness(keyt)
        if key_left_top:
            key_x = -(lim_x + thick / 2)
            key_y = -(inner_y + keyt / 2)
            key_len = -(install_size_H / 2 + key_x - keyt / 2)
        elif ntop > nbot:
            key_x = -(install_size_H / 2 + keyt * 2)
            key_y = pitch_V
            key_len = -pcbnew.FromMM(1.5)
        else:
            key_x = -(install_size_H / 2 + keyt * 2)
            key_y = pitch_V / 2
            key_len = -pcbnew.FromMM(1.5)
        self.draw.HLine(key_x, key_y, key_len)
        self.draw.SetLineThickness(thick)

        # Courtyard
        self.draw.SetLayer(pcbnew.F_CrtYd)
        sizex = install_size_H + courtyard_margin * 2
        sizey = install_size_V + courtyard_margin * 2
        # set courtyard line thickness to the one defined in KLC
        thick = self.draw.GetLineThickness()
        self.draw.SetLineThickness(pcbnew.FromMM(0.05))
        self.draw.Box(0, 0, sizex, sizey)
        # restore line thickness to previous value
        self.draw.SetLineThickness(thick)

        # Reference and Value
        text_size = self.GetTextSize()  # IPC nominal
        text_py = install_size_V / 2 + courtyard_margin + text_size

        self.draw.Value(0, text_py, text_size)
        self.draw.Reference(0, -text_py, text_size)


CFPRUSWizard().register()
