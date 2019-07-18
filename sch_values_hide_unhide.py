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

import os
import pcbnew
import re

import kicadsch


VALUE_FIELD_NUM = 1
HIDDEN_VALUE_MARK = 'Hidden Value'


class sch_values_hide_unhide(pcbnew.ActionPlugin):
    def defaults(self):
        self.name = "Hide/unhide values in sch files"
        self.category = "Modify files"
        self.description = "Hide/unhide values in sch files"
        self.icon_file_name = os.path.abspath(os.path.splitext(__file__)[0]) + '.svg'

    def Run(self):
        name = self.get_board_file_name_without_ext() + u'.sch'
        self.process_sch(name)

    def get_board_file_name_without_ext(self):
        board = pcbnew.GetBoard()
        return os.path.splitext(board.GetFileName())[0]

    def process_sch(self, name):
        sch = kicadsch.Schematic(name)

        for item in sch.items:
            if item.__class__.__name__ == u'Comp':
                # Skip power symbols
                if not item.fields[0].text.startswith(u'#'):
                    self.toggle_visibility(item)
            elif item.__class__.__name__ == u'Sheet':
                sheet_name = self.get_sheet_name(name, item)
                self.process_sch(sheet_name)

        sch.save()

    def get_sheet_name(self, sch_name, sheet):
        dir_name = os.path.dirname(sch_name)
        return os.path.join(dir_name, sheet.file_name)

    # Don't touch originally hidden value field
    def toggle_visibility(self, item):
        if self.is_value_early_hidden(item):
            self.unhide_value(item)
            self.unmark_item_as_hidden(item)
        elif self.is_value_visible(item):
            self.hide_value(item)
            self.mark_item_as_hidden(item)

    def is_value_visible(self, item):
        return item.fields[VALUE_FIELD_NUM].flags[-1] == '0'

    def is_value_early_hidden(self, item):
        for field in item.fields:
            if self.is_field_name_eq(field, HIDDEN_VALUE_MARK):
                return True
        return False

    def is_field_name_eq(self, field, name):
        return hasattr(field, u'name') and field.name == name

    def hide_value(self, item, set=True):
        if set:
            flag = '1'
        else:
            flag = '0'

        item.fields[VALUE_FIELD_NUM].flags = item.fields[VALUE_FIELD_NUM].flags[:-1] + flag

    def unhide_value(self, item):
        self.hide_value(item, set=False)

    def mark_item_as_hidden(self, item):
        field_str = 'F {number} "{text}" {orient} {pos_x:<3} {pos_y:<3} {size:<3} {flags} {hjustify} {vjustify}{italic}{bold} "{name}"'.format(
            number = self.get_last_field_number(item) + 1,
            text = '~', orient = 'H', pos_x = 0, pos_y = 0, size = 60, flags = '0001',
            hjustify = 'C', vjustify = 'C', italic = 'N', bold = 'N',
            name = HIDDEN_VALUE_MARK
        )

        item.fields.append(kicadsch.Schematic.Comp.Field(item, field_str))

    def unmark_item_as_hidden(self, item):
        for i in range(len(item.fields)):
            if self.is_field_name_eq(item.fields[i], HIDDEN_VALUE_MARK):
                item.fields.pop(i)
                break

    def get_last_field_number(self, item):
        return item.fields[-1].number


sch_values_hide_unhide().register()
