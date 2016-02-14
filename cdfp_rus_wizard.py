# cdfp_rus_wizard.py
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


class RowedGridArray(PA.PadGridArray):

    def NamingFunction(self, x, y):
        pad_cnt = self.nx * self.ny

        if (x % 2) == 0:
            return y + 1
        else:
            return pad_cnt - y


class CDFPRUSWizard(HFPW.HelpfulFootprintWizardPlugin):

    pad_count_key = 'pad count'
    pad_install_size_key = 'pad install size (ly)'
    pad_length_key = 'pad length'
    pad_width_key = 'pad width'
    pad_pitch_key = 'pad pitch'

    package_height_key = 'package height'
    package_width_key = 'package width'
    coutyard_margin_key = 'courtyard margin'

    def GetName(self):
        return "CDFP RUS"

    def GetDescription(self):
        return "Ceramic Dual Flat Russia Package footprint wizard"

    def GetValue(self):
        pad_count = self.parameters["Pads"]['*' + self.pad_count_key]
        return "%s-%d" % ("CDFP", pad_count)

    def GenerateParameterList(self):
        self.AddParam("Pads", self.pad_count_key, self.uNatural, 16)
        self.AddParam("Pads", self.pad_pitch_key, self.uMM, 1.25)
        self.AddParam("Pads", self.pad_width_key, self.uMM, 0.8)
        self.AddParam("Pads", self.pad_length_key, self.uMM, 2.1)
        self.AddParam("Pads", self.pad_install_size_key, self.uMM, 18.3)

        self.AddParam("Package", self.package_height_key, self.uMM, 11.65)
        self.AddParam("Package", self.package_width_key, self.uMM, 9.45)
        self.AddParam("Package", self.coutyard_margin_key, self.uMM, 1.0)

    def GetPad(self):
        pad_length = self.parameters["Pads"][self.pad_length_key]
        pad_width = self.parameters["Pads"][self.pad_width_key]
        return PA.PadMaker(self.module).SMDPad(pad_width, pad_length,
                                               shape=pcbnew.PAD_SHAPE_RECT)

    def BuildThisFootprint(self):
        pads = self.parameters["Pads"]
        body = self.parameters["Package"]
        num_pads = pads['*' + self.pad_count_key]
        pad_length = pads[self.pad_length_key]
        pad_width = pads[self.pad_width_key]
        pad_install_size = pads[self.pad_install_size_key]
        pad_pitch = pads[self.pad_pitch_key]
        package_height = body[self.package_height_key]
        package_width = body[self.package_width_key]
        courtyard_margin = body[self.coutyard_margin_key]
        num_cols = 2

        pads_per_col = num_pads // num_cols

        # Pads
        pad = self.GetPad()
        array = RowedGridArray(pad, num_cols, pads_per_col,
                               pad_install_size - pad_length, pad_pitch)
        array.AddPadsToModule(self.draw)

        # Silk Screen
        # package
        self.draw.Box(0, 0, package_width, package_height)
        # pins
        thick = self.draw.GetLineThickness()
        topy = -pad_pitch * (pads_per_col - 1) / 2
        lpin = ((pad_install_size - package_width) / 2 - pad_length -
                thick * 4)
        for i in range(0, pads_per_col):
            py = topy + pad_pitch * i
            self.draw.HLine(-package_width / 2, py, -lpin)
            self.draw.HLine(package_width / 2, py, lpin)
        # key
        keyt = thick * 2
        self.draw.SetLineThickness(keyt)
        self.draw.HLine(-(package_width + thick) / 2,
                        topy - pad_width / 2 - thick * 3,
                        -((pad_install_size - package_width) / 2 - keyt / 2 -
                           thick / 2))

        # Courtyard
        self.draw.SetLayer(pcbnew.F_CrtYd)
        sizex = pad_install_size + courtyard_margin * 2
        sizey = package_height + courtyard_margin * 2
        # set courtyard line thickness to the one defined in KLC
        self.draw.SetLineThickness(pcbnew.FromMM(0.05))
        self.draw.Box(0, 0, sizex, sizey)
        # restore line thickness to previous value
        self.draw.SetLineThickness(thick)

        # Reference and Value
        text_size = self.GetTextSize()  # IPC nominal
        text_py = sizey / 2 + text_size
        self.draw.Value(0, text_py, text_size)
        self.draw.Reference(0, -text_py, text_size)


CDFPRUSWizard().register()
