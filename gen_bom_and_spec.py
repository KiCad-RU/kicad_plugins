# coding: utf8
# gen_bom_and_spec.py
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

''' KiCad PCBNew Action Plugin for generating BOM and Specification '''

import complist
import copy
import kicadsch
import os
import pcbnew
import re
import shutil
import sys

from decimal import Decimal
from operator import itemgetter


OUTPUT_DIR = '_generated_files' + os.path.sep + 'bom_and_spec'

EOL = u'\r\n'
SEP = u' '
JSEP = u'_'
EMPTY_FIELD = u'~'

BOM_HEADER = (u'Наименование', u'Стандарт', u'Кол-во', u'Примечание')
SPEC_HEADER = (u'Наименование', u'Кол-во', u'Примечание', u'Примечание из ПЭ')

REF_NUM = 0
REF_TYPE = 1
GROUP = 2
TYPE = 3
NAME = 4
STD = 5
REMARK = 6
SELECT_REG = 7
VAL = 8

REF_FIELD = 0
VALUE_FIELD = 1


class gen_bom_and_spec(pcbnew.ActionPlugin):
    def defaults(self):
        self.name = "Generates BOM and Specification"
        self.category = "Generates files"
        self.description = "Generates BOM and Specification"
        self.icon_file_name = os.path.abspath(os.path.splitext(__file__)[0]) + '.svg'

    def Run(self):
        board = pcbnew.GetBoard()
        BoardProcessor().process_board(board)

class BoardProcessor():
    def process_board(self, board):
        self.board = board
        self.get_lists(self.get_components())
        self.clean_output(self.get_output_abs_path())
        self.save_lists()

    def get_components(self):
        name = self.get_board_file_name_without_ext() + u'.sch'
        return self.get_components_from_sch(name)

    def get_board_file_name_without_ext(self):
        return os.path.splitext(self.board.GetFileName())[0]

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

    def get_lists(self, components):
        comp_list = []

        cl = complist.CompList()
        cl.add_units = True
        cl.space_before_units = True

        for comp in components:
            if comp:
                if comp.unit != 1:
                    continue
                ref_str = comp.fields[REF_FIELD].text
                value_str = comp.fields[VALUE_FIELD].text
                group_str = self.get_user_field(comp, u'Группа')
                type_str = self.get_user_field(comp, u'Марка')
                type_str = type_str.replace('\\"', '"')
                accuracy_str = self.get_user_field(comp, u'Класс точности')
                var_str = self.get_user_field(comp, u'Тип')
                std_str = self.get_user_field(comp, u'Стандарт')
                remark_str = self.get_user_field(comp, u'Примечание')
                remark_str = remark_str.replace('\\"', '"')
                select_reg = (self.get_user_field(comp, u'Подбирают при регулировании') == '*')

                value_str = cl._get_value_with_units(ref_str, value_str)
                name_str = type_str + value_str + accuracy_str + var_str
                name_str = name_str.replace('\\"', '"')

                if type_str == '':
                    type_str = value_str
                    value_str = ''

                if self.is_passive_element_value(value_str):
                    value = self.string_to_value(value_str)
                else:
                    value = 0

                ref_type = re.search(complist.REF_REGEXP, ref_str).group(1)
                ref_num = re.search(complist.REF_REGEXP, ref_str).group(2)
                comp_list.append([[int(ref_num)], ref_type, group_str, type_str, name_str, std_str, remark_str, select_reg, value])

        comp_list.sort(key=itemgetter(NAME))
        comp_list.sort(key=itemgetter(SELECT_REG))

        comp_list_copy = copy.deepcopy(comp_list)

        self.bom_list = []
        last_name = ''
        for comp in comp_list:
            if last_name != comp[NAME] + comp[STD]:
                last_name = comp[NAME] + comp[STD]
                self.bom_list.append(comp + [1])
            else:
                self.bom_list[-1][REF_NUM].append(comp[REF_NUM][0])
                self.bom_list[-1][-1] += 1

        self.spec_list = []
        last_name = ''
        for comp in comp_list_copy:
            if comp[SELECT_REG]:
                last_name = ''
                self.spec_list.append(comp + [1])
            elif last_name != comp[NAME] + comp[STD]:
                last_name = comp[NAME] + comp[STD]
                self.spec_list.append(comp + [1])
            else:
                self.spec_list[-1][REF_NUM].append(comp[REF_NUM][0])
                self.spec_list[-1][-1] += 1

        for item in self.bom_list:
            item[REF_NUM] = self.simplify_ref(item[REF_NUM], item[REF_TYPE])

        for item in self.spec_list:
            item[REF_NUM] = self.simplify_ref(item[REF_NUM], item[REF_TYPE])

        self.bom_list.sort(key=itemgetter(VAL))
        self.bom_list.sort(key=itemgetter(TYPE))
        self.bom_list.sort(key=itemgetter(GROUP))

        last_group = ''
        i = 0
        for n in range(len(self.bom_list)):
            item = self.bom_list[i]
            if last_group != item[GROUP]:
                last_group = item[GROUP]
                new_item = [''] * len(item)
                new_item[NAME] = last_group
                new_item[REF_NUM] = ['']
                self.bom_list.insert(i, new_item)
                i = i + 1
            i = i + 1

        for i in range(len(self.bom_list)):
            item = self.bom_list[i]
            self.bom_list[i] = [item[NAME], item[STD], str(item[-1]), item[REMARK]]

        self.spec_list.sort(key=itemgetter(REF_NUM))
        self.spec_list.sort(key=itemgetter(NAME))
        self.spec_list.sort(key=itemgetter(VAL))
        self.spec_list.sort(key=itemgetter(TYPE))
        self.spec_list.sort(key=itemgetter(GROUP))

        last_group = ''
        i = 0
        for n in range(len(self.spec_list)):
            item = self.spec_list[i]
            if last_group != item[GROUP] + ' ' + item[STD]:
                last_group = item[GROUP] + ' ' + item[STD]
                new_item = [''] * len(item)
                new_item[NAME] = last_group
                new_item[REF_NUM] = ['']
                self.spec_list.insert(i, new_item)
                i = i + 1
            i = i + 1

        for i in range(len(self.spec_list)):
            item = self.spec_list[i]
            self.spec_list[i] = [item[NAME], str(item[-1]), item[REF_NUM][0], item[REMARK]]

    def get_user_field(self, comp, name):
        for field in comp.fields:
            if hasattr(field, u'name'):
                if field.name == name:
                    return field.text
        return u''

    def is_passive_element_value(self, val):
        return val[-2:] == 'Ом' or val[-1:] == 'Ф' or val[-2:] == 'Гн'

    def string_to_value(self, s):
        v = s.split()
        value = Decimal(v[0].replace(',', '.'))

        if v[1].startswith('Г'):
            value *= Decimal('10') ** 9
        elif v[1].startswith('М'):
            value *= Decimal('10') ** 6
        elif v[1].startswith('к'):
            value *= Decimal('10') ** 3
        elif v[1].startswith('мк'):
            value *= Decimal('10') ** -6
        elif v[1].startswith('м'):
            value *= Decimal('10') ** -3
        elif v[1].startswith('н'):
            value *= Decimal('10') ** -9
        elif v[1].startswith('п'):
            value *= Decimal('10') ** -12

        return value

    def simplify_ref(self, ref_num, ref_type):
        values = []

        # Reference
        ref = u''
        if len(ref_num) > 1:
            # Reference: 'VD1, VD2'; 'C8-C11', 'R7, R9-R14'; 'C8*-C11*' etc.
            ref_num = sorted(ref_num)
            prev_num = ref_num[0]
            counter = 0
            separator = ', '
            ref = ref_type + str(prev_num)
            for num in ref_num[1:]:
                if num == (prev_num + 1):
                    prev_num = num
                    counter += 1
                    if counter > 1:
                        separator = '-'
                    continue
                else:
                    if counter > 0:
                        ref += separator + ref_type + str(prev_num)
                    separator = ', '
                    ref += separator + ref_type + str(num)
                    prev_num = num
                    counter = 0
            if counter > 0:
                ref += separator + ref_type + str(prev_num)
        else:
            # Reference: 'R5'; 'VT13' etc.
            ref = ref_type + str(ref_num[0])
        values.append(ref)

        return values

    def save_lists(self):
        path = self.get_output_abs_path()

        fields_len_stat = self.collect_fields_length_statistic(BOM_HEADER, self.bom_list)
        bom_file = open(path + os.path.sep + u'bom.csv', mode='w')
        s = self.get_header_str(BOM_HEADER, fields_len_stat)
        bom_file.write(s)
        self.write_bom(bom_file, self.bom_list, fields_len_stat)
        bom_file.close()

        fields_len_stat = self.collect_fields_length_statistic(SPEC_HEADER, self.spec_list)
        spec_file = open(path + os.path.sep + u'spec.csv', mode='w')
        s = self.get_header_str(SPEC_HEADER, fields_len_stat)
        spec_file.write(s)
        self.write_bom(spec_file, self.spec_list, fields_len_stat)
        spec_file.close()

    def get_output_abs_path(self):
        return os.path.dirname(self.board.GetFileName()) + os.path.sep + OUTPUT_DIR

    def get_board_name(self):
        return os.path.splitext(os.path.basename(self.board.GetFileName()))[0]

    def collect_fields_length_statistic(self, header, lst):
        fields_len_stat = []

        for entry in header:
            fields_len_stat.append(len(entry) + 2)

        for item in lst:
            for field in range(len(item)):
                cur_len = len(str(item[field])) + 2
                if fields_len_stat[field] < cur_len:
                    fields_len_stat[field] = cur_len

        return fields_len_stat

    def get_header_str(self, header, fields_len_stat):
        s = ''

        for i in range(len(header)):
            s += "'" + header[i]
            if i != len(header)-1:
                num_sep = fields_len_stat[i] - len(header[i]) - 1
                s += "'" + num_sep * SEP
            else:
                s += "'" + EOL

        return s

    def write_bom(self, ofile, lst, fields_len_stat):
        for item in lst:
            for i in range(len(item)):
                ofile.write("'" + item[i] + "'")
                if i != len(item) - 1:
                    num_sep = fields_len_stat[i] - len(item[i]) - 1
                    ofile.write(num_sep * SEP)
                else:
                    ofile.write(EOL)

    def clean_output(self, path):
        if os.path.exists(path):
            shutil.rmtree(path, ignore_errors=False, onerror=None)
        os.makedirs(path)


if __name__ == '__main__':
    board = pcbnew.LoadBoard(sys.argv[1])
    BoardProcessor().process_board(board)
else:
    gen_bom_and_spec().register()
