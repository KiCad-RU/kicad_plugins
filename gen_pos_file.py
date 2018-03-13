# coding=utf8
# gen_pos_file.py
#
# Copyright (C) 2018 Eldar Khayrullin <eldar.khayrullin@mail.ru>
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

''' KiCad PCBNew Action Plugin for generating Pos files'''

import os
import pcbnew
import re


EOL = '\r\n'
SEP = ' '
HEADER = ('Ref', 'Val', 'Package', 'PosX', 'PosY', 'Rot', 'Side')

REF = 0
VAL = 1
PACKAGE = 2
POSX = 3
POSY = 4
ROT = 5

TRANSLATE_TABLE = {
    ord(u' ') : u'_',
    ord(u'"') : u'_',
    ord(u',') : u'.',
    ord(u'¹') : u'^1_',
    ord(u'²') : u'^2_',
    ord(u'³') : u'^3_',
    ord(u'±') : u'+-',

    # russian chars
    ord(u'ё') : u'e',
    ord(u'а') : u'a',
    ord(u'б') : u'b',
    ord(u'в') : u'v',
    ord(u'г') : u'g',
    ord(u'д') : u'd',
    ord(u'е') : u'e',
    ord(u'ж') : u'g',
    ord(u'з') : u'z',
    ord(u'и') : u'i',
    ord(u'й') : u'i',
    ord(u'к') : u'k',
    ord(u'л') : u'l',
    ord(u'м') : u'm',
    ord(u'н') : u'n',
    ord(u'о') : u'o',
    ord(u'п') : u'p',
    ord(u'р') : u'r',
    ord(u'с') : u's',
    ord(u'т') : u't',
    ord(u'у') : u'u',
    ord(u'ф') : u'f',
    ord(u'х') : u'h',
    ord(u'ц') : u'c',
    ord(u'ч') : u'ch',
    ord(u'ш') : u'sh',
    ord(u'щ') : u'ch',
    ord(u'ъ') : u'',
    ord(u'ы') : u'i',
    ord(u'ь') : u'',
    ord(u'э') : u'e',
    ord(u'ю') : u'y',
    ord(u'я') : u'ya',

    ord(u'Ё') : u'E',
    ord(u'А') : u'A',
    ord(u'Б') : u'B',
    ord(u'В') : u'V',
    ord(u'Г') : u'G',
    ord(u'Д') : u'D',
    ord(u'Е') : u'E',
    ord(u'Ж') : u'G',
    ord(u'З') : u'Z',
    ord(u'И') : u'I',
    ord(u'Й') : u'I',
    ord(u'К') : u'K',
    ord(u'Л') : u'L',
    ord(u'М') : u'M',
    ord(u'Н') : u'N',
    ord(u'О') : u'O',
    ord(u'П') : u'P',
    ord(u'Р') : u'R',
    ord(u'С') : u'S',
    ord(u'Т') : u'T',
    ord(u'У') : u'U',
    ord(u'Ф') : u'F',
    ord(u'Х') : u'H',
    ord(u'Ц') : u'C',
    ord(u'Ч') : u'CH',
    ord(u'Ш') : u'SH',
    ord(u'Щ') : u'CH',
    ord(u'Ъ') : u'',
    ord(u'Ы') : u'I',
    ord(u'Ь') : u'',
    ord(u'Э') : u'E',
    ord(u'Ю') : u'Y',
    ord(u'Я') : u'YA',
}


class gen_pos_file(pcbnew.ActionPlugin):
    def Run(self):
        self.update_placement_info()
        self.append_user_fields_to_placement_info()
        self.conform_fields_to_restrictions()
        self.save_placement_info()

    def update_placement_info(self):
        self.placement_info_top = []
        self.placement_info_bottom = []

        board = pcbnew.GetBoard()
        origin = board.GetAuxOrigin()

        for module in board.GetModules():
            if not self.needs_include(module):
                continue

            reference = module.GetReference()
            value = module.GetValue().encode('utf8')
            package = str(module.GetFPID().GetLibItemName())

            pos = module.GetPosition() - origin
            pos_x = pcbnew.ToMM(pos.x)
            pos_y = -pcbnew.ToMM(pos.y)

            rotation = module.GetOrientationDegrees()

            if module.IsFlipped():
                placement_info = self.placement_info_bottom
            else:
                placement_info = self.placement_info_top

            placement_info.append(
                    [reference, value, package, pos_x, pos_y, rotation])

        self.sort_placement_info_by_ref()

    def sort_placement_info_by_ref(self):
        for placement_info in (self.placement_info_top,
                               self.placement_info_bottom):
            placement_info.sort(key=self.get_ref_num)
            placement_info.sort(key=self.get_ref_group)

    def get_ref_group(self, comp):
        return re.sub('[0-9]*$', '', comp[REF])

    def get_ref_num(self, comp):
        try:
            return int(re.findall('[0-9]*$', comp[REF])[0])
        except:
            return 0

    def append_user_fields_to_placement_info(self):
        #TODO read user fields from SCH. '~' as ''.
        #TODO merge user fields with value
        pass

    def conform_fields_to_restrictions(self):
        for placement_info in (self.placement_info_top,
                               self.placement_info_bottom):
            for comp in placement_info:
                comp[VAL] = self.translate_field(comp[VAL])
                comp[PACKAGE] = self.translate_field(comp[PACKAGE])

    def translate_field(self, field):
        return field.decode('utf8').translate(TRANSLATE_TABLE).encode('utf8')

    def save_placement_info(self):
        board = pcbnew.GetBoard()

        name = os.path.splitext(board.GetFileName())[0] + '.pos'
        pos_file = open(name, mode='wb')

        s = self.get_header_str()
        pos_file.write(s + EOL)

        for placement_info in (self.placement_info_top,
                               self.placement_info_bottom):
            is_top = (placement_info is self.placement_info_top)
            if is_top:
                side = 'top'
            else:
                side = 'bottom'

            for comp in placement_info:
                pos_file.write(comp[REF])
                pos_file.write(SEP + comp[VAL])
                pos_file.write(SEP + comp[PACKAGE])
                pos_file.write(SEP + str(comp[POSX]))
                pos_file.write(SEP + str(comp[POSY]))
                pos_file.write(SEP + str(comp[ROT]))
                pos_file.write(SEP + side)
                pos_file.write(EOL)

        pos_file.close()

    def get_header_str(self):
        hlen = len(HEADER)

        hstr = '#'
        for i in range(0, hlen):
            hstr += HEADER[i]
            if i != hlen - 1:
                hstr += SEP

        return hstr


class gen_pos_file_smd(gen_pos_file):
    def defaults(self):
        self.name = "Generate pos file (SMD+Virtual)"
        self.category = "Generates file"
        self.description = "Generates SMD+Virtual components pos file"

    def needs_include(self, module):
        attr = module.GetAttributes()
        return (attr == pcbnew.MOD_CMS) or (attr == pcbnew.MOD_VIRTUAL)


class gen_pos_file_all(gen_pos_file):
    def defaults(self):
        self.name = "Generate pos file (ALL)"
        self.category = "Generates file"
        self.description = "Generates all components pos file"

    def needs_include(self, module):
        return True


gen_pos_file_smd().register()
gen_pos_file_all().register()
