# cdfp_rus_wizard.py
#
# Copyright (C) 2015 Eldar Khayrullin <eldar.khayrullin@mail.ru>
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


class RowedGridArray(PA.PadGridArray):
    def NamingFunction(self, x, y):
        pad_cnt = self.nx * self.ny

        if (x % 2) == 0:
            return y + 1
        else:
            return pad_cnt - y


class CDFPWizard(HFPW.HelpfulFootprintWizardPlugin):

    pad_count_key = 'pad count'
    pad_install_size_key = 'pad install size (ly)'
    pad_length_key = 'pad length'
    pad_width_key = 'pad width'
    pad_pitch_key = 'pad pitch'

    outline_height_key = 'outline height'
    outline_width_key = 'outline width'
    coutyard_margin_key = 'courtyard margin'

    def GetName(self):
        return "CDFP RUS"

    def GetDescription(self):
        return "CDFP rus footprint wizard"

    def GetValue(self):
        pad_count = self.parameters["Pads"]['*' + self.pad_count_key]
        return "%s-%d" % ("CDFP", pad_count)

    def GenerateParameterList(self):
        self.AddParam("Pads", self.pad_count_key, self.uNatural, 16)
        self.AddParam("Pads", self.pad_pitch_key, self.uMM, 1.25)
        self.AddParam("Pads", self.pad_width_key, self.uMM, 0.8)
        self.AddParam("Pads", self.pad_length_key, self.uMM, 2.1)
        self.AddParam("Pads", self.pad_install_size_key, self.uMM, 18.3)

        self.AddParam("Body", self.outline_height_key, self.uMM, 11.65)
        self.AddParam("Body", self.outline_width_key, self.uMM, 9.45)
        self.AddParam("Body", self.coutyard_margin_key, self.uMM, 1.0)

    def GetPad(self):
        pad_length = self.parameters["Pads"][self.pad_length_key]
        pad_width = self.parameters["Pads"][self.pad_width_key]
        return PA.PadMaker(self.module).SMDPad(pad_width, pad_length,
                                               shape=pcbnew.PAD_SHAPE_RECT)

    def BuildThisFootprint(self):
        pads = self.parameters["Pads"]
        body = self.parameters["Body"]
        num_pads = pads['*' + self.pad_count_key]
        pad_length = pads[self.pad_length_key]
        pad_width = pads[self.pad_width_key]
        pad_install_size = pads[self.pad_install_size_key]
        pad_pitch = pads[self.pad_pitch_key]
        outline_height = body[self.outline_height_key]
        outline_width = body[self.outline_width_key]
        courtyard_margin = body[self.coutyard_margin_key]
        num_cols = 2

        pads_per_col = num_pads // num_cols

        # Pads
        pad = self.GetPad()
        array = RowedGridArray(pad, num_cols, pads_per_col,
                               pad_install_size - pad_length, pad_pitch)
        array.AddPadsToModule(self.draw)

        # Silk Screen
        # outline
        self.draw.Box(0, 0, outline_width, outline_height)
        # pins
        mask_margin = pcbnew.FromMM(0.2)
        topy = -pad_pitch * (pads_per_col - 1) / 2
        lpin = ((pad_install_size - outline_width) / 2 - pad_length -
                mask_margin)
        for i in range(0, pads_per_col):
            py = topy + pad_pitch * i
            self.draw.HLine(-outline_width / 2, py, -lpin)
            self.draw.HLine(outline_width / 2, py, lpin)
        # key
        tmp = self.draw.GetLineThickness()
        keyt = tmp * 2
        self.draw.SetLineThickness(keyt)
        self.draw.HLine(-pad_install_size / 2,
                        topy - pad_width / 2 - mask_margin - keyt / 2,
                        (pad_install_size - outline_width - tmp) / 2)
        # restore line thickness to previous value
        self.draw.SetLineThickness(pcbnew.FromMM(tmp))

        # Courtyard
        tmp = self.draw.GetLineThickness()
        self.draw.SetLayer(pcbnew.F_CrtYd)
        sizex = pad_install_size + courtyard_margin * 2
        sizey = outline_height + courtyard_margin * 2
        # set courtyard line thickness to the one defined in KLC
        self.draw.SetLineThickness(pcbnew.FromMM(0.05))
        self.draw.Box(0, 0, sizex, sizey)
        # restore line thickness to previous value
        self.draw.SetLineThickness(pcbnew.FromMM(tmp))

        # Reference and Value
        text_size = self.GetTextSize()  # IPC nominal
        text_py = sizey / 2 + text_size
        self.draw.Value(0, text_py, text_size)
        self.draw.Reference(0, -text_py, text_size)


CDFPWizard().register()
