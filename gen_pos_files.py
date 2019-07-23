# coding: utf8
# gen_pos_files.py
#
# Copyright (C) 2018, 2019 Eldar Khayrullin <eldar.khayrullin@mail.ru>
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

''' KiCad PCBNew Action Plugin for generating pos files'''

import kicadsch
import os
import pcbnew
import re
import shutil
import sys


OUTPUT_NAME = 'pos'

EOL = u'\r\n'
SEP = u' '
JSEP = u'_'
EMPTY_FIELD = u'~'
HEADER = (u'Ref', u'Type', u'Val', u'Type_Val', u'Package', u'PosX', u'PosY',
          u'Rot', u'Side')

REF = 0
TYPE = 1
VAL = 2
PACKAGE = 3
POSX = 4
POSY = 5
ROT = 6
IS_SMD = 7

TRANSLATE_TABLE = {
    ord(u' ') : u'_',
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
    def defaults(self):
        self.name = "Generate pos files (SMD+ALL)"
        self.category = "Generates files"
        self.description = "Generates SMD+ALL components pos files"
        self.icon_file_name = os.path.abspath(os.path.splitext(__file__)[0]) + '.svg'

    def Run(self):
        board = pcbnew.GetBoard()
        BoardProcessor().process_board(board)

class BoardProcessor():
    def process_board(self, board):
        self.board = board
        self.get_placement_info()
        self.append_user_fields_to_placement_info()
        self.conform_fields_to_restrictions()
        self.clean_output(self.get_output_abs_path())
        self.save_placement_info()

    def get_placement_info(self):
        self.placement_info_top = []
        self.placement_info_bottom = []

        origin = self.board.GetAuxOrigin()

        for module in self.board.GetModules():
            reference = module.GetReference()
            if self.is_non_annotated_ref(reference):
                continue

            value = module.GetValue()
            package = str(module.GetFPID().GetLibItemName())

            pos = module.GetPosition() - origin

            pos_x = pcbnew.ToMM(pos.x)
            if module.IsFlipped():
                pos_x = -pos_x

            pos_y = -pcbnew.ToMM(pos.y)

            rotation = module.GetOrientationDegrees()

            if module.IsFlipped():
                placement_info = self.placement_info_bottom
            else:
                placement_info = self.placement_info_top

            is_smd = self.is_smd_module(module)

            placement_info.append([reference, u'', value, package, pos_x, pos_y, rotation, is_smd])

        self.sort_placement_info_by_ref()

    def is_non_annotated_ref(self, ref):
        return ref[-1] == u'*'

    def is_smd_module(self, module):
        attr = module.GetAttributes()
        return (attr == pcbnew.MOD_CMS) or (attr == pcbnew.MOD_VIRTUAL)

    def sort_placement_info_by_ref(self):
        for placement_info in (self.placement_info_top,
                               self.placement_info_bottom):
            placement_info.sort(key=self.get_ref_num)
            placement_info.sort(key=self.get_ref_group)

    def get_ref_group(self, item):
        return re.sub('[0-9]*$', u'', item[REF])

    def get_ref_num(self, item):
        try:
            return int(re.findall('[0-9]*$', item[REF])[0])
        except:
            return 0

    def append_user_fields_to_placement_info(self):
        components = self.get_components()
        for placement_info in (self.placement_info_top,
                               self.placement_info_bottom):
            for item in placement_info:
                comp = self.get_component_by_ref(components, item[REF])
                if comp:
                    type_str = self.get_user_field(comp, u'Марка')
                    if type_str == '':
                        type_str = item[VAL]
                        item[VAL] = ''

                    var_str = self.get_user_field(comp, u'Тип')
                    if var_str != '':
                        type_str += JSEP + var_str

                    type_str = type_str.replace('\\"', '"')

                    item[VAL] += self.get_user_field(comp, u'Класс точности')
                else:
                    type_str = item[VAL]
                    item[VAL] = ''

                item[TYPE] = type_str

    def get_components(self):
        name = self.get_board_file_name_without_ext() + u'.sch'
        return self.get_components_from_sch(name)

    def get_components_from_sch(self, name):
        components = []
        sch = kicadsch.Schematic(name)

        for item in sch.items:
            if item.__class__.__name__ == u'Comp':
                # Skip power symbols
                if not item.fields[0].text.startswith(u'#'):
                    components.append(item)
            elif item.__class__.__name__ == u'Sheet':
                dirname = os.path.dirname(name)
                filename = os.path.join(dirname, item.file_name)
                components.extend(self.get_components_from_sch(filename))

        return components

    def get_component_by_ref(self, components, ref):
       for comp in components:
           if self.get_ref_field(comp) == ref:
               return comp
       return None

    def get_ref_field(self, comp):
        return comp.fields[0].text

    def get_user_field(self, comp, name):
        for field in comp.fields:
            if hasattr(field, u'name'):
                if field.name == name:
                    return field.text
        return u''

    def get_board_file_name_without_ext(self):
        return os.path.splitext(self.board.GetFileName())[0]

    def conform_fields_to_restrictions(self):
        for placement_info in (self.placement_info_top,
                               self.placement_info_bottom):
            for item in placement_info:
                item[TYPE] = self.translate_field(item[TYPE])
                item[VAL] = self.translate_field(item[VAL])
                item[PACKAGE] = self.translate_field(item[PACKAGE])

    def translate_field(self, field):
        if field == '':
            return ''
        else:
            return field.translate(TRANSLATE_TABLE)

    def clean_output(self, path):
        if os.path.exists(path):
            shutil.rmtree(path, ignore_errors=False, onerror=None)
        os.mkdir(path)

    def save_placement_info(self):
        self.collect_fields_length_statistic()

        path = self.get_output_abs_path()
        name = path + os.path.sep + self.get_board_name()

        pos_file_all = open(name + u'-ALL.pos', mode='w')
        pos_file_smd = open(name + u'-SMD.pos', mode='w')

        s = self.get_header_str() + EOL
        pos_file_all.write(s)
        pos_file_smd.write(s)

        self.write_placement_info(pos_file_all, pos_file_smd)

        pos_file_all.close()
        pos_file_smd.close()

    def collect_fields_length_statistic(self):
        self.fields_max_length = []
        for i in range(0, 3):
            self.fields_max_length.append(len(HEADER[i]))
        for i in range(4, 8):
            self.fields_max_length.append(len(HEADER[i]))
        self.fields_max_length[0] += 1

        for placement_info in (self.placement_info_top,
                               self.placement_info_bottom):
            for item in placement_info:
                for field in range(0, len(placement_info[0]) - 1):
                    cur_len = len(str(item[field]))
                    if self.fields_max_length[field] < cur_len:
                        self.fields_max_length[field] = cur_len

    def get_output_abs_path(self):
        return os.path.dirname(self.board.GetFileName()) + os.path.sep + OUTPUT_NAME

    def get_board_name(self):
        return os.path.splitext(os.path.basename(self.board.GetFileName()))[0]

    def get_header_str(self):
        hlen = len(HEADER)
        sep_fills = []
        sep_fills.append(self.fields_max_length[REF] - 1 - len(HEADER[0]) + 1)
        sep_fills.append(self.fields_max_length[TYPE] - len(HEADER[1]) + 1)
        sep_fills.append(self.fields_max_length[VAL] - len(HEADER[2]) + 1)
        sep_fills.append(self.fields_max_length[TYPE] + self.fields_max_length[VAL] + \
                         len(JSEP) + 1 - len(HEADER[3]))
        sep_fills.append(self.fields_max_length[PACKAGE] - len(HEADER[4]) + 1)
        sep_fills.append(self.fields_max_length[POSX] - len(HEADER[5]) + 1)
        sep_fills.append(self.fields_max_length[POSY] - len(HEADER[6]) + 1)
        sep_fills.append(self.fields_max_length[ROT] - len(HEADER[7]) + 1)
        sep_fills.append(0)

        hstr = u'#'
        for i in range(0, hlen):
            hstr += HEADER[i]
            hstr += self.get_separators_str(sep_fills[i])

        return hstr

    def get_separators_str(self, n):
        separators = ''
        for i in range(0, n):
            separators += SEP
        return separators

    def write_placement_info(self, ofile_all, ofile_smd):
        for placement_info in (self.placement_info_top,
                               self.placement_info_bottom):
            is_top = (placement_info is self.placement_info_top)
            if is_top:
                side = u'top'
            else:
                side = u'bottom'

            for item in placement_info:
                self.write_item(item, ofile_all, side)
                if item[IS_SMD]:
                    self.write_item(item, ofile_smd, side)

    def write_item(self, item, ofile, side):
        ofile.write(item[REF])
        num_sep = self.fields_max_length[REF] - len(item[REF]) + 1
        ofile.write(self.get_separators_str(num_sep))

        ofile.write(item[TYPE])
        num_sep = self.fields_max_length[TYPE] - len(item[TYPE]) + 1
        ofile.write(self.get_separators_str(num_sep))

        num_sep = self.fields_max_length[VAL] + 1
        if item[VAL] == '':
            ofile.write(EMPTY_FIELD)
            num_sep -= 1
        else:
            ofile.write(item[VAL])
            num_sep -= len(item[VAL])
        ofile.write(self.get_separators_str(num_sep))

        ofile.write(item[TYPE])
        num_sep = self.fields_max_length[TYPE] - len(item[TYPE]) + \
                  self.fields_max_length[VAL] + len(JSEP) + 1
        if item[VAL] != '':
            ofile.write(JSEP + item[VAL])
            num_sep -= len(item[VAL]) + 1
        ofile.write(self.get_separators_str(num_sep))

        ofile.write(item[PACKAGE])
        num_sep = self.fields_max_length[PACKAGE] - len(item[PACKAGE]) + 1
        ofile.write(self.get_separators_str(num_sep))

        ofile.write(str(item[POSX]))
        num_sep = self.fields_max_length[POSX] - len(str(item[POSX])) + 1
        ofile.write(self.get_separators_str(num_sep))

        ofile.write(str(item[POSY]))
        num_sep = self.fields_max_length[POSY] - len(str(item[POSY])) + 1
        ofile.write(self.get_separators_str(num_sep))

        ofile.write(str(item[ROT]))
        num_sep = self.fields_max_length[ROT] - len(str(item[ROT])) + 1
        ofile.write(self.get_separators_str(num_sep))

        ofile.write(side + EOL)


if __name__ == '__main__':
    board = pcbnew.LoadBoard(sys.argv[1])
    BoardProcessor().process_board(board)
else:
    gen_pos_file().register()
