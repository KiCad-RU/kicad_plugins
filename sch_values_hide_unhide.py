# coding: utf8
# sch_values_hide_unhide.py
#
# Copyright (C) 2019 Eldar Khayrullin <eldar.khayrullin@mail.ru>
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

''' KiCad PCBNew Action Plugin for hide and unhide of sch values '''

import kicadsch
import os
import pcbnew
import re
import sys


VALUE_FIELD_NUM = 1
HIDDEN_VALUE_MARK = 'Hidden Value'


class sch_values_hide_unhide(pcbnew.ActionPlugin):
    def defaults(self):
        self.name = "Hide/unhide values in sch files"
        self.category = "Modify files"
        self.description = "Hide/unhide values in sch files"
        self.icon_file_name = self.get_icon_file_name()

    def Run(self):
        board = pcbnew.GetBoard()
        process_board(board)

    def get_icon_file_name(self):
        dirname = os.path.dirname(os.path.abspath(__file__))
        filename = os.path.splitext(os.path.basename(__file__))[0]

        return dirname + os.path.sep + 'bitmaps' + os.path.sep + filename + '.png'


def process_board(board):
    name = get_board_file_name_without_ext(board) + u'.sch'
    process_sch(name)

def get_board_file_name_without_ext(board):
    return os.path.splitext(board.GetFileName())[0]

def process_sch(name):
    sch = kicadsch.Schematic(name)

    for item in sch.items:
        if item.__class__.__name__ == u'Comp':
            # Skip power symbols
            if not item.fields[0].text.startswith(u'#'):
                toggle_visibility(item)
        elif item.__class__.__name__ == u'Sheet':
            sheet_name = get_sheet_name(name, item)
            process_sch(sheet_name)

    sch.save()

def get_sheet_name(sch_name, sheet):
    dir_name = os.path.dirname(sch_name)
    return os.path.join(dir_name, sheet.file_name)

# Don't touch originally hidden value field
def toggle_visibility(item):
    if is_value_early_hidden(item):
        unhide_value(item)
        unmark_item_as_hidden(item)
    elif is_value_visible(item):
        hide_value(item)
        mark_item_as_hidden(item)

def is_value_visible(item):
    return item.fields[VALUE_FIELD_NUM].flags[-1] == '0'

def is_value_early_hidden(item):
    for field in item.fields:
        if is_field_name_eq(field, HIDDEN_VALUE_MARK):
            return True
    return False

def is_field_name_eq(field, name):
    return hasattr(field, u'name') and field.name == name

def hide_value(item, set=True):
    if set:
        flag = '1'
    else:
        flag = '0'

    item.fields[VALUE_FIELD_NUM].flags = item.fields[VALUE_FIELD_NUM].flags[:-1] + flag

def unhide_value(item):
    hide_value(item, set=False)

def mark_item_as_hidden(item):
    field_str = 'F {number} "{text}" {orient} {pos_x:<3} {pos_y:<3} {size:<3} {flags} {hjustify} {vjustify}{italic}{bold} "{name}"'.format(
        number = get_last_field_number(item) + 1,
        text = '~', orient = 'H', pos_x = 0, pos_y = 0, size = 60, flags = '0001',
        hjustify = 'C', vjustify = 'C', italic = 'N', bold = 'N',
        name = HIDDEN_VALUE_MARK
    )

    item.fields.append(kicadsch.Schematic.Comp.Field(item, field_str))

def unmark_item_as_hidden(item):
    for i in range(len(item.fields)):
        if is_field_name_eq(item.fields[i], HIDDEN_VALUE_MARK):
            item.fields.pop(i)
            break

def get_last_field_number(item):
    return item.fields[-1].number


if __name__ == '__main__':
    board = pcbnew.LoadBoard(sys.argv[1])
    process_board(board)
else:
    sch_values_hide_unhide().register()
