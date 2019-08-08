#!/usr/bin/env python2
# -*-    Mode: Python; coding: utf-8; indent-tabs-mode: nil; tab-width: 4    -*-
### BEGIN LICENSE
# Copyright (C) 2018 Baranovskiy Konstantin (baranovskiykonstantin@gmail.com)
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License version 3, as published
# by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranties of
# MERCHANTABILITY, SATISFACTORY QUALITY, or FITNESS FOR A PARTICULAR
# PURPOSE.  See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program.  If not, see <http://www.gnu.org/licenses/>.
### END LICENSE

"""
Module for generating formatted list of components
as *.odf, *.ods or *.csv file for KiCad Schematics.

"""

import csv
import codecs
import os
import re
import time
from copy import deepcopy
from operator import itemgetter

'''
import odf.opendocument
from odf.draw import Frame
from odf.style import ParagraphProperties, TextProperties
from odf.table import Table, TableRow, TableColumn, TableCell
from odf.text import P
from odf import meta
'''

from kicadsch import Schematic

REF_REGEXP = re.compile('([^0-9]+)([0-9]+)', re.U)
NUM_REGEXP = re.compile('([А-ЯA-Z0-9]+(?:[^А-ЯA-Z0-9][0-9\.\-\s]+)?)(Э[1-7])?', re.U)
CHAR_WIDTH_MM = {
    u" ":{12:1.58565153734, 14:1.84992679356},
    u"!":{12:0.792825768668, 14:0.792825768668},
    u"\"":{12:1.05710102489, 14:1.32137628111},
    u"#":{12:2.11420204978, 14:2.64275256223},
    u"$":{12:2.11420204978, 14:2.378477306},
    u"%":{12:3.69985358712, 14:4.22840409956},
    u"&":{12:2.11420204978, 14:2.64275256223},
    u"'":{12:0.528550512445, 14:0.792825768668},
    u"(":{12:1.05710102489, 14:1.05710102489},
    u")":{12:1.05710102489, 14:1.05710102489},
    u"*":{12:1.32137628111, 14:1.32137628111},
    u"+":{12:1.84992679356, 14:2.11420204978},
    u",":{12:0.792825768668, 14:0.792825768668},
    u"-":{12:1.84992679356, 14:2.11420204978},
    u".":{12:0.792825768668, 14:0.792825768668},
    u"/":{12:2.11420204978, 14:2.378477306},
    u"0":{12:1.84992679356, 14:2.11420204978},
    u"1":{12:1.05710102489, 14:1.32137628111},
    u"2":{12:1.84992679356, 14:2.11420204978},
    u"3":{12:1.84992679356, 14:2.11420204978},
    u"4":{12:1.84992679356, 14:2.11420204978},
    u"5":{12:1.84992679356, 14:2.11420204978},
    u"6":{12:1.84992679356, 14:2.11420204978},
    u"7":{12:1.84992679356, 14:2.11420204978},
    u"8":{12:1.84992679356, 14:2.11420204978},
    u"9":{12:1.84992679356, 14:2.11420204978},
    u":":{12:0.792825768668, 14:0.792825768668},
    u";":{12:0.792825768668, 14:0.792825768668},
    u"<":{12:1.84992679356, 14:2.11420204978},
    u"=":{12:1.84992679356, 14:2.11420204978},
    u">":{12:1.84992679356, 14:2.11420204978},
    u"?":{12:1.84992679356, 14:2.11420204978},
    u"@":{12:3.17130307467, 14:3.69985358712},
    u"A":{12:2.11420204978, 14:2.378477306},
    u"B":{12:1.84992679356, 14:2.378477306},
    u"C":{12:1.58565153734, 14:1.84992679356},
    u"D":{12:1.84992679356, 14:2.378477306},
    u"E":{12:1.58565153734, 14:1.84992679356},
    u"F":{12:1.58565153734, 14:1.84992679356},
    u"G":{12:1.84992679356, 14:2.378477306},
    u"H":{12:2.11420204978, 14:2.378477306},
    u"I":{12:0.792825768668, 14:0.792825768668},
    u"J":{12:1.32137628111, 14:1.58565153734},
    u"K":{12:1.84992679356, 14:2.378477306},
    u"L":{12:1.58565153734, 14:1.84992679356},
    u"M":{12:2.11420204978, 14:2.64275256223},
    u"N":{12:2.11420204978, 14:2.378477306},
    u"O":{12:1.84992679356, 14:2.378477306},
    u"P":{12:1.84992679356, 14:2.378477306},
    u"Q":{12:1.84992679356, 14:2.378477306},
    u"R":{12:1.84992679356, 14:2.378477306},
    u"S":{12:1.84992679356, 14:2.11420204978},
    u"T":{12:1.84992679356, 14:2.11420204978},
    u"U":{12:2.11420204978, 14:2.378477306},
    u"V":{12:2.11420204978, 14:2.378477306},
    u"W":{12:2.378477306, 14:2.90702781845},
    u"X":{12:2.11420204978, 14:2.378477306},
    u"Y":{12:2.11420204978, 14:2.378477306},
    u"Z":{12:1.84992679356, 14:2.11420204978},
    u"[":{12:1.05710102489, 14:1.05710102489},
    u"\\":{12:2.11420204978, 14:2.378477306},
    u"]":{12:1.05710102489, 14:1.05710102489},
    u"^":{12:1.32137628111, 14:1.32137628111},
    u"_":{12:2.11420204978, 14:2.64275256223},
    u"`":{12:0.528550512445, 14:0.792825768668},
    u"a":{12:1.84992679356, 14:2.11420204978},
    u"b":{12:1.84992679356, 14:2.11420204978},
    u"c":{12:1.32137628111, 14:1.58565153734},
    u"d":{12:1.84992679356, 14:2.11420204978},
    u"e":{12:1.58565153734, 14:1.84992679356},
    u"f":{12:1.05710102489, 14:1.32137628111},
    u"g":{12:1.84992679356, 14:2.11420204978},
    u"h":{12:1.84992679356, 14:2.11420204978},
    u"i":{12:0.792825768668, 14:0.792825768668},
    u"j":{12:0.792825768668, 14:0.792825768668},
    u"k":{12:1.58565153734, 14:1.84992679356},
    u"l":{12:1.05710102489, 14:1.05710102489},
    u"m":{12:2.11420204978, 14:2.64275256223},
    u"n":{12:1.84992679356, 14:2.11420204978},
    u"o":{12:1.58565153734, 14:1.84992679356},
    u"p":{12:1.84992679356, 14:2.11420204978},
    u"q":{12:1.84992679356, 14:2.11420204978},
    u"r":{12:1.32137628111, 14:1.58565153734},
    u"s":{12:1.58565153734, 14:1.84992679356},
    u"t":{12:1.05710102489, 14:1.32137628111},
    u"u":{12:1.84992679356, 14:2.11420204978},
    u"v":{12:1.58565153734, 14:1.84992679356},
    u"w":{12:2.11420204978, 14:2.378477306},
    u"x":{12:1.58565153734, 14:1.84992679356},
    u"y":{12:1.58565153734, 14:1.84992679356},
    u"z":{12:1.58565153734, 14:1.84992679356},
    u"{":{12:1.32137628111, 14:1.32137628111},
    u"|":{12:0.792825768668, 14:0.792825768668},
    u"}":{12:1.32137628111, 14:1.32137628111},
    u"~":{12:2.11420204978, 14:2.378477306},
    u"«":{12:1.84992679356, 14:2.11420204978},
    u"°":{12:1.58565153734, 14:1.84992679356},
    u"±":{12:1.84992679356, 14:2.11420204978},
    u"µ":{12:1.84992679356, 14:2.11420204978},
    u"·":{12:0.792825768668, 14:0.792825768668},
    u"»":{12:1.84992679356, 14:2.11420204978},
    u"А":{12:2.11420204978, 14:2.378477306},
    u"Б":{12:1.84992679356, 14:2.378477306},
    u"В":{12:1.84992679356, 14:2.378477306},
    u"Г":{12:1.58565153734, 14:1.84992679356},
    u"Д":{12:1.84992679356, 14:2.11420204978},
    u"Е":{12:1.58565153734, 14:1.84992679356},
    u"Ж":{12:2.378477306, 14:2.64275256223},
    u"З":{12:1.58565153734, 14:1.84992679356},
    u"И":{12:2.11420204978, 14:2.378477306},
    u"Й":{12:2.11420204978, 14:2.378477306},
    u"К":{12:1.84992679356, 14:2.378477306},
    u"Л":{12:1.84992679356, 14:2.11420204978},
    u"М":{12:2.11420204978, 14:2.64275256223},
    u"Н":{12:2.11420204978, 14:2.378477306},
    u"О":{12:1.84992679356, 14:2.378477306},
    u"П":{12:2.11420204978, 14:2.378477306},
    u"Р":{12:1.84992679356, 14:2.378477306},
    u"С":{12:1.58565153734, 14:1.84992679356},
    u"Т":{12:1.84992679356, 14:2.11420204978},
    u"У":{12:1.84992679356, 14:2.378477306},
    u"Ф":{12:2.11420204978, 14:2.64275256223},
    u"Х":{12:2.11420204978, 14:2.378477306},
    u"Ц":{12:2.11420204978, 14:2.378477306},
    u"Ч":{12:1.84992679356, 14:2.378477306},
    u"Ш":{12:2.378477306, 14:2.90702781845},
    u"Щ":{12:2.64275256223, 14:2.90702781845},
    u"Ъ":{12:2.378477306, 14:2.64275256223},
    u"Ы":{12:2.11420204978, 14:2.64275256223},
    u"Ь":{12:1.84992679356, 14:2.378477306},
    u"Э":{12:1.84992679356, 14:2.11420204978},
    u"Ю":{12:2.11420204978, 14:2.64275256223},
    u"Я":{12:1.84992679356, 14:2.378477306},
    u"а":{12:1.84992679356, 14:2.11420204978},
    u"б":{12:1.58565153734, 14:1.84992679356},
    u"в":{12:1.84992679356, 14:2.11420204978},
    u"г":{12:1.58565153734, 14:1.84992679356},
    u"д":{12:1.84992679356, 14:2.11420204978},
    u"е":{12:1.58565153734, 14:1.84992679356},
    u"ж":{12:2.11420204978, 14:2.378477306},
    u"з":{12:1.32137628111, 14:1.58565153734},
    u"и":{12:1.84992679356, 14:2.11420204978},
    u"й":{12:1.84992679356, 14:2.11420204978},
    u"к":{12:1.58565153734, 14:1.84992679356},
    u"л":{12:1.58565153734, 14:1.84992679356},
    u"м":{12:2.11420204978, 14:2.378477306},
    u"н":{12:1.84992679356, 14:2.11420204978},
    u"о":{12:1.58565153734, 14:1.84992679356},
    u"п":{12:1.84992679356, 14:2.11420204978},
    u"р":{12:1.84992679356, 14:2.11420204978},
    u"с":{12:1.32137628111, 14:1.58565153734},
    u"т":{12:2.11420204978, 14:2.64275256223},
    u"у":{12:1.84992679356, 14:2.11420204978},
    u"ф":{12:2.11420204978, 14:2.378477306},
    u"х":{12:1.58565153734, 14:1.84992679356},
    u"ц":{12:1.84992679356, 14:2.11420204978},
    u"ч":{12:1.84992679356, 14:2.11420204978},
    u"ш":{12:2.11420204978, 14:2.64275256223},
    u"щ":{12:2.378477306, 14:2.64275256223},
    u"ъ":{12:1.84992679356, 14:2.11420204978},
    u"ы":{12:2.11420204978, 14:2.378477306},
    u"ь":{12:1.58565153734, 14:1.84992679356},
    u"э":{12:1.58565153734, 14:1.84992679356},
    u"ю":{12:1.84992679356, 14:2.378477306},
    u"я":{12:1.84992679356, 14:2.11420204978},
    u"Ё":{12:1.58565153734, 14:1.84992679356},
    u"Є":{12:1.84992679356, 14:2.11420204978},
    u"І":{12:0.792825768668, 14:0.792825768668},
    u"Ї":{12:1.05710102489, 14:1.05710102489},
    u"ё":{12:1.58565153734, 14:1.84992679356},
    u"є":{12:1.58565153734, 14:1.84992679356},
    u"і":{12:0.792825768668, 14:0.792825768668},
    u"ї":{12:1.05710102489, 14:1.05710102489},
    u"℃":{12:2.90702781845, 14:3.43557833089},
    u"℉":{12:2.90702781845, 14:3.43557833089},
    u"№":{12:2.90702781845, 14:3.43557833089},
    u"max":{12:3.69985358712, 14:4.22840409956},
    }

class CompList(object):  # pylint: disable=too-many-instance-attributes
    """
    Generating list of the components from KiCad Schematic
    and save it to *.ods file.

    """

    def __init__(self):

        # Variables for filling the list
        self.complist = None
        self.components_array = None
        self.complist_pages = []

        # Callback
        # This will be called for getting group name in singular
        self.get_singular_group_name = None

        # Stamp fields
        self.developer = u''
        self.verifier = u''
        self.inspector = u''
        self.approver = u''
        self.decimal_num = u''
        self.title = u''
        self.company = u''

        # Options
        self.file_format = u'.ods' # u'.odt', u'.csv'
        self.all_components = False
        self.add_units = False
        self.space_before_units = False
        self.empty_row_after_name = False
        self.empty_rows_after_group = 1
        self.empty_rows_everywhere = False
        self.prohibit_empty_rows_on_top = False
        self.gost_in_group_name = False
        self.singular_group_name = True
        self.join_same_name_groups = False
        self.prohibit_group_name_at_bottom = False
        self.add_first_usage = False
        self.fill_first_usage = False
        self.add_customer_fields = False
        self.add_changes_sheet = False
        self.count_for_changes_sheet = 0
        self.italic = False
        self.underline_group_name = False
        self.center_group_name = False
        self.center_reference = False
        self.extremal_width_factor = 80

        # Additional data
        self.separators_dict = {
            u'марка':['', ''],
            u'значение':['', ''],
            u'класс точности':['', ''],
            u'тип':['', ''],
            u'стандарт':['', '']
            }
        self.aliases_dict = {
            u'группа':u'Группа',
            u'марка':u'Марка',
            u'значение':u'Значение',
            u'класс точности':u'Класс точности',
            u'тип':u'Тип',
            u'стандарт':u'Стандарт',
            u'примечание':u'Примечание'
            }
        self.multipliers_dict = {
            u'G': u'Г',
            u'M': u'М',
            u'k': u'к',
            u'm': u'м',
            u'μ': u'мк',
            u'u': u'мк',
            u'U': u'мк',
            u'n': u'н',
            u'p': u'п'
            }

        # Current state of filling the list of components
        self._cur_row = 1
        self._cur_page_num = 1
        self._cur_page = None
        self._rows_per_page = 0
        # Patterns for first page
        self._first_page_pattern_v1 = None
        self._first_page_pattern_v2 = None
        self._first_page_pattern_v3 = None
        self._first_page_pattern_v4 = None
        # Pattern for other pages
        self._other_pages_pattern = None
        # Pattern for last pages (the changes sheet)
        self._last_page_pattern = None

    @staticmethod
    def _get_width_factor(label, text):  # pylint: disable=too-many-return-statements, too-many-branches
        """
        Returns width factor in % if text is not fit in table column.

        """
        if not text:
            return 100
        elif label.startswith('#1:'):
            # Size of text that fits in any case
            if len(text) <= 6:
                return 100
            font_size = 14 # pt
            column_width = 17.5 # mm
        elif label.startswith('#2:'):
            # Size of text that fits in any case
            if len(text) <= 37:
                return 100
            font_size = 14 # pt
            column_width = 108 # mm
        elif label.startswith('#3:'):
            # Size of text that fits in any case
            if len(text) <= 3:
                return 100
            font_size = 14 # pt
            column_width = 9 # mm
        elif label.startswith('#4:'):
            # Size of text that fits in any case
            if len(text) <= 14:
                return 100
            font_size = 14 # pt
            column_width = 41.5 # mm
        elif label in ('#5:1', '#5:2', '#5:3', '#5:4'):
            # Size of text that fits in any case
            if len(text) <= 8:
                return 100
            font_size = 12 # pt
            column_width = 20.5 # mm
        else:
            return 100

        text_width = 0
        for char in text:
            char_width = 0
            try:
                char_width = CHAR_WIDTH_MM[char][font_size]
            except KeyError:
                char_width = CHAR_WIDTH_MM[u'max'][font_size]
            text_width += char_width

        width_factor_float = (100 * column_width) / text_width
        width_factor_int = int(width_factor_float)
        if (width_factor_float % 1) > 0 \
                and width_factor_int > 1:
            width_factor_int -= 1

        return width_factor_int

    @staticmethod
    def _get_unescaped_text(text):
        """
        Remove any escapes in text.

        """
        # Decoding internal escapes
        pure_text = text.decode('string_escape')
        # Decoding escapes from KiCad
        pure_text = pure_text.decode('string_escape')
        return unicode(pure_text)

    def _get_value_with_units(self, ref, value):
        """
        Automatic units addition.

        """
        if self.add_units:
            num_value = u''
            multiplier = u''
            units = u''
            mult_keys, mult_values = zip(*self.multipliers_dict.items())
            multipliers = mult_keys + mult_values
            multipliers = list(set(multipliers))
            # 2u7, 2н7, 4m7, 5k1 etc.
            regexp_1 = re.compile(
                '^(\d+)({})(\d+)$'.format(u'|'.join(multipliers)),
                re.U
                )
            # 2.7 u, 2700p, 4.7 m, 470u, 5.1 k, 510 etc.
            regexp_2 = re.compile(
                '^(\d+(?:[\.,]\d+)?)\s*({})?$'.format(u'|'.join(multipliers)),
                re.U
                )
            if ref.startswith(u'C') and not value.endswith(u'Ф'):
                units = u'Ф'
                if re.match('^\d+$', value):
                    num_value = value
                    multiplier = u'п'
                elif re.match('^\d+[\.,]\d+$', value):
                    num_value = value
                    multiplier = u'мк'
                else:
                    num_value = value.rstrip(u'F')
                    num_value = num_value.strip()
                    if re.match(regexp_1, num_value):
                        search_res = re.search(regexp_1, num_value).groups()
                        num_value = search_res[0] + ',' + search_res[2]
                        multiplier = search_res[1]
                    elif re.match(regexp_2, num_value):
                        search_res = re.search(regexp_2, num_value).groups()
                        num_value = search_res[0]
                        multiplier = search_res[1]
                    else:
                        num_value = u''
            elif ref.startswith(u'L') and not value.endswith(u'Гн'):
                units = u'Гн'
                num_value = value.rstrip(u'H')
                num_value = num_value.strip()
                if re.match(regexp_1, num_value):
                    search_res = re.search(regexp_1, num_value).groups()
                    num_value = search_res[0] + ',' + search_res[2]
                    multiplier = search_res[1]
                elif re.match(regexp_2, num_value):
                    search_res = re.search(regexp_2, num_value).groups()
                    num_value = search_res[0]
                    if search_res[1] is None:
                        multiplier = u'мк'
                    else:
                        multiplier = search_res[1]
                else:
                    num_value = u''
            elif ref.startswith(u'R') and not value.endswith(u'Ом'):
                units = u'Ом'
                num_value = value.rstrip(u'Ω')
                if num_value.endswith(u'Ohm') or num_value.endswith(u'ohm'):
                    num_value = num_value[:-3]
                num_value = num_value.strip()
                if re.match('R\d+', num_value):
                    num_value = num_value.replace(u'R', u'0,')
                elif re.match('\d+R\d+', num_value):
                    num_value = num_value.replace(u'R', u',')
                elif re.match(regexp_1, num_value):
                    search_res = re.search(regexp_1, num_value).groups()
                    num_value = search_res[0] + ',' + search_res[2]
                    multiplier = search_res[1]
                elif re.match(regexp_2, num_value):
                    search_res = re.search(regexp_2, num_value).groups()
                    num_value = search_res[0]
                    if search_res[1] is not None:
                        multiplier = search_res[1]
                else:
                    num_value = u''
            if num_value:
                # Translate multiplier
                if multiplier in self.multipliers_dict:
                    multiplier = self.multipliers_dict[multiplier]
                value = num_value.replace(u'.', u',')
                if self.space_before_units:
                    value += u' '
                value += multiplier
                value += units
        return value

    def _replace_text(self, page, label, text, center=False, underline=False):  # pylint: disable=too-many-arguments
        """
        Replace 'label' (like #1:1) to 'text' in every table on 'page'.
        If 'center' is set to 'True' text will be aligned by center of the cell.
        If 'underline' is set to 'True' text will be underlined.

        """
        if self.file_format == u'.ods':
            self._replace_text_in_table(page, label, text, center, underline)
        elif self.file_format == u'.odt':
            for table in page.body.getElementsByType(Table):
                self._replace_text_in_table(table, label, text, center, underline)

    def _replace_text_in_table(self, table, label, text, center=False, underline=False):  # pylint: disable=too-many-arguments, too-many-locals, too-many-branches, too-many-statements
        """
        Replace 'label' (like #1:1) to 'text' in 'table'.
        If 'center' is set to 'True' text will be aligned by center of the cell.
        If 'underline' is set to 'True' text will be underlined.

        """
        for row in table.getElementsByType(TableRow):  # pylint: disable=too-many-nested-blocks
            for cell in row.getElementsByType(TableCell):
                for paragraph in cell.getElementsByType(P):
                    for p_data in paragraph.childNodes:
                        if p_data.tagName == u'Text':
                            if p_data.data == label:
                                text = self._get_unescaped_text(text)
                                text_lines = text.split(u'\n')
                                p_data.data = text_lines[0]
                                # Line breaks
                                if len(text_lines) > 1:
                                    p_style = paragraph.getAttribute(u'stylename')
                                    for line in text_lines[1:]:
                                        new_p = P(text=line)
                                        if self.file_format == u'.odt':
                                            new_p.setAttribute(u'stylename', p_style)
                                        cell.addElement(new_p)
                                if center or underline:
                                    suffix = u''
                                    if center:
                                        suffix += u'_c'
                                    if underline:
                                        suffix += u'_u'
                                    # Set center align and/or underline
                                    if self.file_format == u'.ods':
                                        # If used ODS format the text properties stored
                                        # in cell style.
                                        group_style_name = cell.getAttribute(u'stylename') + suffix
                                    elif self.file_format == u'.odt':
                                        # But if used ODT format the text properties stored
                                        # in paragraph style inside cell.
                                        group_style_name = suffix
                                    try:
                                        group_style = self.complist.getStyleByName(group_style_name)
                                    except AssertionError:
                                        group_style = None
                                    if group_style is None:
                                        if self.file_format == u'.ods':
                                            group_style_name = cell.getAttribute(u'stylename')
                                        elif self.file_format == u'.odt':
                                            group_style_name = paragraph.getAttribute(u'stylename')
                                        group_style = deepcopy(
                                            self.complist.getStyleByName(group_style_name)
                                            )
                                        if self.file_format == u'.ods':
                                            group_style_name += suffix
                                            group_style.setAttribute(u'name', group_style_name)
                                        elif self.file_format == u'.odt':
                                            group_style.setAttribute(u'name', suffix)
                                        if center:
                                            group_style.addElement(
                                                ParagraphProperties(
                                                    textalign=u'center'
                                                    )
                                                )
                                        if underline:
                                            group_style.addElement(
                                                TextProperties(
                                                    textunderlinetype=u'single',
                                                    textunderlinestyle=u'solid'
                                                    )
                                                )
                                        self.complist.automaticstyles.addElement(group_style)
                                    if self.file_format == u'.ods':
                                        cell.setAttribute(u'stylename', group_style_name)
                                    elif self.file_format == u'.odt':
                                        paragraph.setAttribute(u'stylename', suffix)

                                # Fit text to cell in *.odt (*.ods does it automatically)
                                if self.file_format == u'.odt':
                                    width_factor = self._get_width_factor(label, text)

                                    if width_factor < 100:
                                        suffix = u'_%d' % width_factor
                                        cur_style_name = paragraph.getAttribute(u'stylename')
                                        new_style_name = cur_style_name + suffix
                                        try:
                                            new_style = self.complist.getStyleByName(new_style_name)
                                        except AssertionError:
                                            new_style = None
                                        if new_style is None:
                                            new_style = deepcopy(
                                                self.complist.getStyleByName(cur_style_name)
                                                )
                                            new_style.setAttribute(u'name', new_style_name)
                                            new_style.addElement(
                                                TextProperties(
                                                    textscale=u'%d%%' % width_factor
                                                    )
                                                )
                                            self.complist.automaticstyles.addElement(new_style)
                                        paragraph.setAttribute(u'stylename', new_style_name)

                                return

    def _clear_page(self, page):
        """
        Clear every table on 'page' of labels.

        """
        if self.file_format == u'.ods':
            self._clear_table(page)
        elif self.file_format == u'.odt':
            for table in page.body.getElementsByType(Table):
                self._clear_table(table)

    @staticmethod
    def _clear_table(table):
        """
        Clear 'table' of labels.

        """
        rows = table.getElementsByType(TableRow)
        for row in rows:  # pylint: disable=too-many-nested-blocks
            cells = row.getElementsByType(TableCell)
            for cell in cells:
                for paragraph in cell.getElementsByType(P):
                    for p_data in paragraph.childNodes:
                        if p_data.tagName == u'Text':
                            if re.search('#\d+:\d+', p_data.data) is not None:
                                p_data.data = u''

    def _next_row(self):
        """
        Moving to next row.
        If table is full, save it in list object and create a new one.

        """
        # Increase row counter
        self._cur_row += 1

        # First page of the list has 29 or 26 lines, other pages has 32 lines
        if self._cur_row > self._rows_per_page:
            # Table is full
            if self.file_format == u'.ods':
                self._cur_page.setAttribute(u'name', u'стр. %d' % self._cur_page_num)
            self.complist_pages.append(self._cur_page)

            self._cur_page = deepcopy(self._other_pages_pattern)
            if self.file_format == u'.odt':
                # Needed for getting styles in _replace_text_in_table
                self.complist = self._cur_page
            self._cur_page_num += 1
            self._cur_row = 1
            self._rows_per_page = 32

    def _get_final_values(self, element, with_group=False):  # pylint: disable=too-many-locals, too-many-branches, too-many-statements
        """
        Get list with final fields values of component.
        """
        values = []

        group, \
        ref_type, \
        ref_num, \
        need_adjust_flag, \
        mark, \
        value, \
        accuracy, \
        type_, \
        gost, \
        comment, \
        count = element

        # Reference
        ref = u''
        if int(count) > 1:
            # Reference: 'VD1, VD2'; 'C8-C11', 'R7, R9-R14'; 'C8*-C11*' etc.
            prev_num = ref_num[0]
            counter = 0
            separator = ', '
            ref = ref_type + str(prev_num)
            if need_adjust_flag:
                ref += u'*'
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
                        if need_adjust_flag:
                            ref += u'*'
                    separator = ', '
                    ref += separator + ref_type + str(num)
                    if need_adjust_flag:
                        ref += u'*'
                    prev_num = num
                    counter = 0
            if counter > 0:
                ref += separator + ref_type + str(prev_num)
                if need_adjust_flag:
                    ref += u'*'
        else:
            # Reference: 'R5'; 'VT13' etc.
            ref = ref_type + ref_num
            # Add "*" mark if component "needs adjusting"
            if need_adjust_flag:
                ref = ref + u'*'
        values.append(ref)

        # Name
        name = u''
        # Adding separators
        if mark:
            name += "{prefix}{value}{suffix}".format(
                prefix=self.separators_dict[u'марка'][0],
                value=mark,
                suffix=self.separators_dict[u'марка'][1]
                )
        if value:
            name += "{prefix}{value}{suffix}".format(
                prefix=self.separators_dict[u'значение'][0],
                value=self._get_value_with_units(ref_type, value),
                suffix=self.separators_dict[u'значение'][1]
                )
        if accuracy:
            name += "{prefix}{value}{suffix}".format(
                prefix=self.separators_dict[u'класс точности'][0],
                value=accuracy,
                suffix=self.separators_dict[u'класс точности'][1]
                )
        if type_:
            name += "{prefix}{value}{suffix}".format(
                prefix=self.separators_dict[u'тип'][0],
                value=type_,
                suffix=self.separators_dict[u'тип'][1]
                )
        if gost:
            name += "{prefix}{value}{suffix}".format(
                prefix=self.separators_dict[u'стандарт'][0],
                value=gost,
                suffix=self.separators_dict[u'стандарт'][1]
                )
        if with_group:
            try:
                singular_group_name = self.get_singular_group_name(group)  # pylint: disable=not-callable
            except TypeError:
                singular_group_name = group
            name = singular_group_name + u' ' + name
        values.append(name)

        # Count
        values.append(count)

        # Comment
        values.append(comment)

        return values

    @staticmethod
    def _get_group_names_with_gost(group):  # pylint: disable=too-many-locals, too-many-branches, too-many-statements
        """
        Get list of group names with GOST for every mark of components
        and prepared components (without GOST).
        """
        group_name = group[0][0]
        gost = group[0][8]
        components = deepcopy(group)

        # Check if GOST is equal in components
        for comp in components:
            if comp[8] != gost:
                break
        else:
            # All components with same GOST
            if not gost:
                # If GOST is empty in every component:
                # group title is just Groupname
                return [group_name], components
            # Clear GOST in every component
            for comp in components:
                comp[8] = u''
            # Group title is Groupname + GOST (without Mark)
            return [' '.join([group_name, gost])], components

        # Create collection of unique set of groupname, mark and gost
        group_names_parts_with_gost = []
        multi_components_in_group = False
        for comp in components:
            mark = comp[4]
            if not mark:
                # If Mark field is empty to use Value instead
                mark = comp[5]
            gost = comp[8]
            if mark and gost:
                group_name_parts = [group_name, mark, gost]
                if group_name_parts not in group_names_parts_with_gost:
                    group_names_parts_with_gost.append(group_name_parts)
                else:
                    multi_components_in_group = True

        if multi_components_in_group:
            for comp in components:
                comp[8] = u''

        # Split mark into parts by non-alphabetical chars
        for group_name_parts in group_names_parts_with_gost:
            mark_string = group_name_parts[1]
            mark_parts = []
            # First part without prefix
            res = re.search(
                '[^A-Za-zА-Яа-я0-9]*([A-Za-zА-Яа-я0-9]+)($|[^A-Za-zА-Яа-я0-9].*)',
                mark_string
                )
            if res is None:
                group_name_parts[1] = [mark_string]
                continue
            mark_parts.append(res.groups()[0])
            mark_string = res.groups()[1]
            # Other parts with delimiters as prefix
            while True:
                res = re.search(
                    '([^A-Za-zА-Яа-я0-9]+[A-Za-zА-Яа-я0-9_\.,]+)($|[^A-Za-zА-Яа-я0-9].*)',
                    mark_string
                    )
                if res is not None:
                    mark_parts.append(res.groups()[0])
                    mark_string = res.groups()[1]
                else:
                    break
            group_name_parts[1] = mark_parts

        # Create set of groupname, mark and gost with unique GOST
        # and common part of Mark
        group_names_parts_with_unique_gost = []  # pylint: disable=invalid-name
        for group_name_parts in group_names_parts_with_gost:
            group_name, mark_parts, gost = group_name_parts
            for group_name_unique_parts in group_names_parts_with_unique_gost:
                if group_name_unique_parts[2] == gost \
                        and group_name_unique_parts[1][0] == mark_parts[0]:
                    # Leave only common parts of Mark
                    list_len = len(mark_parts)
                    if list_len > len(group_name_unique_parts[1]):
                        list_len = len(group_name_unique_parts[1])
                    for i in range(list_len):
                        if group_name_unique_parts[1][i] != mark_parts[i]:
                            group_name_unique_parts[1] = mark_parts[:i]
                            break
                    break
            else:
                # Format: [Groupname, [Markparts, ...], GOST]
                group_names_parts_with_unique_gost.append([group_name, mark_parts[:], gost])

        # Concatenate parts of names together
        group_names = []
        if len(group_names_parts_with_unique_gost) == 1:
            name = group_names_parts_with_unique_gost[0][0] + u' ' + \
                   group_names_parts_with_unique_gost[0][2]
            group_names.append(name)
        elif not multi_components_in_group:
            name = group_names_parts_with_unique_gost[0][0]
            group_names.append(name)
        else:
            for group_name_parts in group_names_parts_with_unique_gost:
                group_name_parts[1] = u''.join(group_name_parts[1])
                name = u' '.join(group_name_parts)
                group_names.append(name)

        # If GOST or Mark not present - use default group name
        if group_names == []:
            group_names = [group_name]

        return group_names, components

    def _normalize_row(self, columns):  # pylint: disable=too-many-locals, too-many-branches, too-many-statements
        """
        If value of a cell does not fit, it will be splitted and moved to
        extra row.
        This method returns a tuple: normalized columns and rest of it
        as extra row

        """
        norm_columns = list(columns)
        extra_ref = None
        extra_name = None
        extra_count = None
        extra_comment = None
        extra_row = None
        width_factors = [100, 100, 100, 100]
        for index, value in enumerate(columns):
            width_factors[index] = self._get_width_factor(
                '#{}:{}'.format(index + 1, self._cur_row),
                value
                )
        # Reference column
        if width_factors[0] < self.extremal_width_factor:
            ref = columns[0]
            extremal_pos = int(len(ref) * width_factors[0] / self.extremal_width_factor)
            # First try: find separator before extremal position
            pos1 = ref.rfind(u', ', 0, extremal_pos)
            pos2 = ref.rfind(u'-', 0, extremal_pos)
            pos = max(pos1, pos2)
            if pos == -1:
                # Second try: find separator after extremal position
                # (it is still less than extremal_width_factor,
                # but better than nothing)
                pos1 = ref.find(u', ', extremal_pos)
                pos2 = ref.find(u'-', extremal_pos)
                pos = max(pos1, pos2)
            if pos != -1:
                separator = ref[pos]
                if separator == u',':
                    norm_columns[0] = ref[:(pos + 1)]
                    extra_ref = ref[(pos + 2):]
                elif separator == u'-':
                    norm_columns[0] = ref[:(pos + 1)]
                    extra_ref = ref[pos:]
        # Name column
        if width_factors[1] < self.extremal_width_factor:
            name = columns[1]
            extremal_pos = int(len(name) * width_factors[1] / self.extremal_width_factor)
            # First try: find separator before extremal position
            pos = name.rfind(u' ', 0, extremal_pos)
            if pos == -1:
                # Second try: find separator after extremal position
                # (it is still less than extremal_width_factor,
                # but better than nothing)
                pos = name.find(u' ', extremal_pos)
            if pos != -1:
                norm_columns[1] = name[:pos]
                extra_name = name[(pos + 1):]
        # Comment column
        if width_factors[3] < self.extremal_width_factor:
            comment = columns[3]
            extremal_pos = int(len(comment) * width_factors[3] / self.extremal_width_factor)
            # First try: find separator before extremal position
            pos = comment.rfind(u' ', 0, extremal_pos)
            if pos == -1:
                # Second try: find separator after extremal position
                # (it is still less than extremal_width_factor,
                # but better than nothing)
                pos = comment.find(u' ', extremal_pos)
            if pos != -1:
                norm_columns[3] = comment[:pos]
                extra_comment = comment[(pos + 1):]

        if extra_ref is not None or extra_name is not None or extra_comment is not None:
            extra_row = []
            if extra_ref is None:
                extra_row.append(u'')
            else:
                extra_row.append(extra_ref)
            if extra_name is None:
                extra_row.append(u'')
            else:
                extra_row.append(extra_name)
            if extra_count is None:
                extra_row.append(u'')
            else:
                extra_row.append(extra_count)
            if extra_comment is None:
                extra_row.append(u'')
            else:
                extra_row.append(extra_comment)
        return norm_columns, extra_row

    def _set_row(self, columns):
        """
        Fill the row in list of the components using element's fields.

        Columns of the component list:
        0 - reference
        1 - name
        2 - count
        3 - comment

        """
        while True:
            columns, extra_row = self._normalize_row(columns)
            for index, value in enumerate(columns):
                center = False
                # Reference column
                if index == 0:
                    center = self.center_reference

                self._replace_text(
                    self._cur_page,
                    u'#{}:{}'.format(index + 1, self._cur_row),
                    value,
                    center=center
                    )
            if extra_row is None:
                break
            else:
                columns = extra_row
                self._next_row()

    def load(self, sch_file_name):  # pylint: disable=too-many-locals, too-many-branches, too-many-statements
        """
        Load values of the fields from all components of
        KiCad Schematic file.

        """

        def get_text_from_field(comp, field_name):
            """
            If field has 'name' then get text from it.

            """
            text = u''
            if field_name == u'Обозначение':
                text = ref
            elif field_name == u'Значение':
                text = self._get_value_with_units(
                    comp.fields[0].text,
                    comp.fields[1].text
                )
            elif field_name == u'Посад.место':
                text = comp.fields[2].text
            elif field_name == u'Документация':
                text = comp.fields[3].text
            else:
                for field in comp.fields:
                    if field.name == field_name:
                        text = field.text
            return text

        def apply_substitution(comp, ref, field_value):
            """
            Replace ${field_name} with value from field with name "field_name".

            """
            match = re.search('\$\{([^{}]*)\}', field_value)
            if match is None:
                return field_value
            else:
                new_field_value = field_value.replace(
                    u'${%s}' % match.group(1),
                    get_text_from_field(comp, match.group(1)),
                    1
                    )
                new_field_value = apply_substitution(comp, ref, new_field_value)
                return new_field_value

        def get_comp_by_ref(ref):
            """
            Get component object with reference "ref".

            """
            for comp in components:
                if comp.fields[0].text == ref:
                    return comp
                else:
                    if hasattr(comp, u'path_and_ref'):
                        for path_and_ref in comp.path_and_ref:
                            if path_and_ref[1] == ref:
                                return comp
            return None

        # Get title block description
        sch = Schematic(sch_file_name)
        self.developer = sch.descr.comment2
        self.verifier = sch.descr.comment3
        self.approver = sch.descr.comment4
        self.decimal_num = self.convert_decimal_num(sch.descr.comment1)
        self.title = self.convert_title(sch.descr.title)
        self.company = sch.descr.comp

        # Load all fields
        components = self.get_components(sch_file_name)
        comp_array = []
        for comp in components:
            # Skip components with not supported ref type
            if not re.match(REF_REGEXP, comp.fields[0].text):
                continue
            exclude = False
            # Skip components excluded manually
            if not self.all_components:
                for field in comp.fields:
                    if field.name == u'Исключён из ПЭ':
                        exclude = True
                        break
                if exclude:
                    continue
            # Skip parts of the same component
            for row in comp_array:
                if comp.fields[0].text == (row[1] + row[2]):
                    exclude = True
                    break
            if exclude:
                continue

            temp = []
            temp.append(get_text_from_field(
                comp,
                self.aliases_dict[u'группа']
                ))
            ref_type = re.search(REF_REGEXP, comp.fields[0].text).group(1)
            temp.append(ref_type)
            ref_num = re.search(REF_REGEXP, comp.fields[0].text).group(2)
            temp.append(ref_num)
            need_adjust = False
            for field in comp.fields:
                if field.name == u'Подбирают при регулировании':
                    need_adjust = True
                    break
            temp.append(need_adjust)
            temp.append(get_text_from_field(
                comp,
                self.aliases_dict[u'марка']
                ))
            temp.append(get_text_from_field(
                comp,
                self.aliases_dict[u'значение']
                ))
            temp.append(get_text_from_field(
                comp,
                self.aliases_dict[u'класс точности']
                ))
            temp.append(get_text_from_field(
                comp,
                self.aliases_dict[u'тип']
                ))
            temp.append(get_text_from_field(
                comp,
                self.aliases_dict[u'стандарт']
                ))
            temp.append(get_text_from_field(
                comp,
                self.aliases_dict[u'примечание']
                ))
            temp.append(u'1')
            if hasattr(comp, u'path_and_ref'):
                for ref in comp.path_and_ref:
                    # Skip components with not supported ref type
                    if not re.match(REF_REGEXP, ref[1]):
                        continue
                    # Skip parts of the same comp from different sheets
                    for value in comp_array:
                        tmp_ref = value[1] + value[2]
                        if tmp_ref == ref[1]:
                            break
                    else:
                        new_temp = list(temp)
                        new_temp[1] = re.search(REF_REGEXP, ref[1]).group(1)
                        new_temp[2] = re.search(REF_REGEXP, ref[1]).group(2)
                        comp_array.append(new_temp)
            else:
                comp_array.append(temp)

        if not comp_array:
            self.components_array = None
            return

        # Apply substitution
        for i, _ in enumerate(comp_array):
            comp = get_comp_by_ref(comp_array[i][1] + comp_array[i][2])
            for ii, _ in enumerate(comp_array[i]):  # pylint: disable=invalid-name
                # Skip for ref_type, ref_num, need_adjust_flag and count
                if ii in (1, 2, 3, 10):
                    continue
                field_value = comp_array[i][ii]
                new_field_value = apply_substitution(
                    comp,
                    comp_array[i][1] + comp_array[i][2],
                    field_value
                    )
                comp_array[i][ii] = new_field_value

        # Sort all components by ref_type
        comp_array = sorted(comp_array, key=itemgetter(1))

        # Split elements into groups based on ref_type
        # input: list of components;
        # every component represent as
        # [group, ref_type, ref_number, need_adjust_flag, mark, value, accuracy, type, GOST, comment, count]
        # output: list of groups;
        # every group represent as list of components.
        group_array = []
        grouped_comp_array = []
        cur_ref = None
        for comp in comp_array:
            if cur_ref is None:
                # First component
                group_array.append(comp)
                cur_ref = comp[1]
            elif comp[1] == cur_ref:
                # The same type
                group_array.append(comp)
            else:
                # Next group
                grouped_comp_array.append(group_array)
                group_array = [comp]
                cur_ref = comp[1]
        # Append last group
        grouped_comp_array.append(group_array)

        # Sort components into every group by ref_num
        for group in grouped_comp_array:
            group.sort(key=lambda num: int(num[2]))

        # Split every group by group name
        # (may have different name with same ref_type)
        comp_array = grouped_comp_array[:]
        grouped_comp_array = []
        for group in comp_array:
            cur_name = None
            group_array = []
            for comp in group:
                if cur_name is None:
                    # First component
                    group_array.append(comp)
                    cur_name = comp[0]
                elif comp[0] == cur_name:
                    # The same type
                    group_array.append(comp)
                else:
                    # Next group
                    grouped_comp_array.append(group_array)
                    group_array = [comp]
                    cur_name = comp[0]
            # Append last group
            grouped_comp_array.append(group_array)

        # If sequential groups has the same name but different ref_type
        # they may be joined in single group.
        if self.join_same_name_groups \
                and len(grouped_comp_array) > 1:
            temp_array = [grouped_comp_array[0]]
            for group in grouped_comp_array[1:]:
                # group name of last comp from previous group
                prev_groupname = temp_array[-1][-1][0]
                # group name of first comp from current group
                cur_groupname = group[0][0]
                if cur_groupname == prev_groupname \
                        and cur_groupname:
                    temp_array[-1].extend(group)
                else:
                    temp_array.append(group)
            grouped_comp_array = temp_array

        # Combining the identical elements in one line.
        # All identical elements differs by ref_num.
        # Resulting element has all ref_nums in ref_num field as list.
        temp_array = []
        for group in grouped_comp_array:
            ref_nums = []
            prev = None
            last_index = 0
            temp_group = []
            for element in group:
                if group.index(element) == 0:
                    # first element
                    ref_nums.append(int(element[2]))
                    prev = element[:]
                    if len(group) == 1:
                        temp_group.append(element)
                        temp_array.append(temp_group)
                    continue

                if element[:2] == prev[:2] \
                        and element[3:] == prev[3:]:
                    # equal elements
                    ref_nums.append(int(element[2]))
                    last_index = group.index(element)
                else:
                    # different elements
                    if len(ref_nums) > 1:
                        # finish processing of several identical elements
                        count = len(ref_nums)
                        temp_element = group[last_index]
                        temp_element[2] = ref_nums[:]
                        temp_element[10] = str(count)
                        temp_group.append(temp_element)
                    else:
                        # next different element
                        temp_group.append(prev)
                    ref_nums = [int(element[2])]

                if group.index(element) == len(group) - 1:
                    # last element in the group
                    if len(ref_nums) > 1:
                        # finish processing of several identical elements
                        count = len(ref_nums)
                        temp_element = group[last_index]
                        temp_element[2] = ref_nums[:]
                        temp_element[10] = str(count)
                        temp_group.append(temp_element)
                    else:
                        temp_group.append(element)
                    temp_array.append(temp_group)
                prev = element[:]
        self.components_array = temp_array

    def save(self, complist_file_name):  # pylint: disable=too-many-locals, too-many-branches, too-many-statements
        """
        Save created list of the components to the file.

        """
        if self.components_array is None:
            return

        base_path = os.path.dirname(os.path.realpath(__file__))
        if self.file_format == u'.csv':
            # File for writing the list of the components
            file_name = os.path.splitext(complist_file_name)[0] + self.file_format
            headers_row = [u'Поз. обозначение', u'Наименование', u'Кол.', u'Примечание']
            empty_row = ['', '', '', '']
            with codecs.open(file_name, 'wb', encoding='utf-8') as csv_file:
                csv_writer = csv.writer(csv_file)
                csv_writer.writerow(headers_row)

                # Fill list of the components
                prev_ref_type = self.components_array[0][0][1]
                for group in self.components_array:  # pylint: disable=too-many-nested-blocks
                    group_name = group[0][0]
                    ref_type = group[0][1]

                    # Empty rows between groups
                    add_empty_rows = True
                    if self.components_array.index(group) == 0:
                        # Not needed before first group
                        add_empty_rows = False
                    if prev_ref_type == ref_type \
                            and not self.empty_rows_everywhere:
                        # Not needed between elements of the same type,
                        # except it is required by user.
                        add_empty_rows = False
                    if add_empty_rows:
                        for _ in range(self.empty_rows_after_group):
                            csv_writer.writerow(empty_row)
                    prev_ref_type = ref_type

                    if group_name:
                        if len(group) == 1 and self.singular_group_name:
                            # Place group name with name of component
                            comp_values = self._get_final_values(group[0], True)
                            for value in comp_values:
                                value = self._get_unescaped_text(value)
                            csv_writer.writerow(comp_values)
                            continue
                        else:
                            # New group title
                            if self.gost_in_group_name:
                                group_names_with_gost, components = self._get_group_names_with_gost(group)
                                # Write group names with GOST
                                for group_name_with_gost in group_names_with_gost:
                                    group_name_with_gost = self._get_unescaped_text(group_name_with_gost)
                                    csv_writer.writerow([u'', group_name_with_gost, u'', u''])
                                # Empty row after group name
                                if self.empty_row_after_name:
                                    csv_writer.writerow(empty_row)
                                # Write to table prepared components
                                for comp in components:
                                    # Write component into list
                                    comp_values = self._get_final_values(comp)
                                    for value in comp_values:
                                        value = self._get_unescaped_text(value)
                                    csv_writer.writerow(comp_values)
                                continue
                            else:
                                csv_writer.writerow([u'', group_name, u'', u''])
                                # Empty row after group name
                                if self.empty_row_after_name:
                                    csv_writer.writerow(empty_row)

                    for comp in group:
                        # Write component into list
                        comp_values = self._get_final_values(comp)
                        for value in comp_values:
                            value = self._get_unescaped_text(value)
                        csv_writer.writerow(comp_values)
            return

        if self.file_format == u'.ods':
            # Load the pattern
            pattern = odf.opendocument.load(os.path.join(
                base_path, u'patterns', u'all_in_one.ods'))
            for sheet in pattern.spreadsheet.getElementsByType(Table):
                # Patterns for first page
                if sheet.getAttribute(u'name') == u'First1':
                    self._first_page_pattern_v1 = sheet
                elif sheet.getAttribute(u'name') == u'First2':
                    self._first_page_pattern_v2 = sheet
                elif sheet.getAttribute(u'name') == u'First3':
                    self._first_page_pattern_v3 = sheet
                elif sheet.getAttribute(u'name') == u'First4':
                    self._first_page_pattern_v4 = sheet
                # Pattern for other pages
                elif sheet.getAttribute(u'name') == u'Other':
                    self._other_pages_pattern = sheet
                # Pattern for last pages (the changes sheet)
                elif sheet.getAttribute(u'name') == u'Last':
                    self._last_page_pattern = sheet

            # Create list of the components file object
            self.complist = odf.opendocument.OpenDocumentSpreadsheet()

            # Copy all parameters from pattern to list of the components
            for font in pattern.fontfacedecls.childNodes[:]:
                self.complist.fontfacedecls.addElement(font)
            for style in pattern.styles.childNodes[:]:
                self.complist.styles.addElement(style)
            for masterstyle in pattern.masterstyles.childNodes[:]:
                self.complist.masterstyles.addElement(masterstyle)
            for autostyle in pattern.automaticstyles.childNodes[:]:
                self.complist.automaticstyles.addElement(autostyle)
            for setting in pattern.settings.childNodes[:]:
                self.complist.settings.addElement(setting)
        elif self.file_format == u'.odt':
            # Patterns for first page
            self._first_page_pattern_v1 = odf.opendocument.load(os.path.join(
                base_path, u'patterns', u'first1.odt'))
            self._first_page_pattern_v2 = odf.opendocument.load(os.path.join(
                base_path, u'patterns', u'first2.odt'))
            self._first_page_pattern_v3 = odf.opendocument.load(os.path.join(
                base_path, u'patterns', u'first3.odt'))
            self._first_page_pattern_v4 = odf.opendocument.load(os.path.join(
                base_path, u'patterns', u'first4.odt'))
            # Pattern for other pages
            self._other_pages_pattern = odf.opendocument.load(os.path.join(
                base_path, u'patterns', u'other.odt'))
            # Pattern for last pages (the changes sheet)
            self._last_page_pattern = odf.opendocument.load(os.path.join(
                base_path, u'patterns', u'last.odt'))

        # Select pattern for first page
        if not self.add_first_usage and not self.add_customer_fields:
            self._cur_page = self._first_page_pattern_v1
            self._rows_per_page = 29
        elif self.add_first_usage and not self.add_customer_fields:
            self._cur_page = self._first_page_pattern_v2
            self._rows_per_page = 29
        elif not self.add_first_usage and self.add_customer_fields:
            self._cur_page = self._first_page_pattern_v3
            self._rows_per_page = 26
        elif self.add_first_usage and self.add_customer_fields:
            self._cur_page = self._first_page_pattern_v4
            self._rows_per_page = 26

        if self.file_format == u'.odt':
            # Needed for getting styles in _replace_text_in_table
            self.complist = self._cur_page

        # Fill list of the components
        prev_ref_type = self.components_array[0][0][1]
        for group in self.components_array:  # pylint: disable=too-many-nested-blocks
            group_name = group[0][0]
            ref_type = group[0][1]

            # Empty rows between groups
            add_empty_rows = True
            if self.components_array.index(group) == 0:
                # Not needed before first group
                add_empty_rows = False
            if prev_ref_type == ref_type \
                    and not self.empty_rows_everywhere:
                # Not needed between elements of the same type,
                # except it is required by user.
                add_empty_rows = False
            if add_empty_rows:
                for _ in range(self.empty_rows_after_group):
                    if self.prohibit_empty_rows_on_top and self._cur_row == 1:
                        break
                    self._next_row()
            prev_ref_type = ref_type

            if group_name:
                if len(group) == 1 and self.singular_group_name:
                    # Place group name with name of component
                    columns = self._get_final_values(group[0], with_group=True)
                    self._set_row(columns)
                    self._next_row()
                    continue
                else:
                    # New group title
                    if self.gost_in_group_name:
                        group_names_with_gost, components = self._get_group_names_with_gost(group)
                        # If name of group at bottom of page - move it to next page
                        if self.prohibit_group_name_at_bottom \
                                and (self._cur_row + len(group_names_with_gost)) >= self._rows_per_page:
                            while self._cur_row != 1:
                                self._next_row()
                        # Write group names with GOST
                        for group_name_with_gost in group_names_with_gost:
                            self._replace_text(
                                self._cur_page,
                                u'#2:%d' % self._cur_row,
                                group_name_with_gost,
                                center=self.center_group_name,
                                underline=self.underline_group_name
                                )
                            self._next_row()
                        # Empty row after group name
                        if self.empty_row_after_name:
                            if not (self.prohibit_empty_rows_on_top and self._cur_row == 1):
                                self._next_row()
                        # Write to table prepared components
                        for comp in components:
                            # Write component into list
                            columns = self._get_final_values(comp)
                            self._set_row(columns)
                            self._next_row()
                        continue

                    else:
                        # If name of group at bottom of page - move it to next page
                        if self.prohibit_group_name_at_bottom \
                                and self._cur_row == self._rows_per_page:
                            self._next_row()
                        self._replace_text(
                            self._cur_page,
                            u'#2:%d' % self._cur_row,
                            group_name,
                            center=self.center_group_name,
                            underline=self.underline_group_name
                            )
                        self._next_row()
                        # Empty row after group name
                        if self.empty_row_after_name:
                            if not (self.prohibit_empty_rows_on_top and self._cur_row == 1):
                                self._next_row()

            for comp in group:
                # Write component into list
                columns = self._get_final_values(comp)
                self._set_row(columns)
                self._next_row()

        # Current table not empty - save it
        if self._cur_row != 1:
            # Set last row as current
            self._cur_row = self._rows_per_page
            # Go to next empty page and save current
            self._next_row()

        # If the sheet of changes is needed - append it
        pg_cnt = len(self.complist_pages)
        if self.add_changes_sheet \
                and pg_cnt > self.count_for_changes_sheet:
            self._cur_page = self._last_page_pattern
            if self.file_format == u'.ods':
                self._cur_page.setAttribute(u'name', u'стр. %d' % self._cur_page_num)
            self.complist_pages.append(self._cur_page)

        # Fill stamp fields on each page
        pg_cnt = len(self.complist_pages)
        for index, page in enumerate(self.complist_pages):
            # First page - big stamp
            if index == 0:

                if self.file_format == u'.odt':
                    # Needed for getting styles in _replace_text_in_table
                    self.complist = page

                self._replace_text(page, u'#5:1', self.developer)
                self._replace_text(page, u'#5:2', self.verifier)
                self._replace_text(page, u'#5:3', self.inspector)
                self._replace_text(page, u'#5:4', self.approver)
                self._replace_text(page, u'#5:5', self.decimal_num)
                self._replace_text(page, u'#5:6', self.title)
                if pg_cnt > 1:
                    self._replace_text(page, u'#5:7', str(index + 1))
                self._replace_text(page, u'#5:8', str(pg_cnt))
                self._replace_text(page, u'#5:9', self.company)
                if self.fill_first_usage:
                    first_usage = re.search(NUM_REGEXP, self.decimal_num)
                    if first_usage is not None:
                        self._replace_text(page, u'#6:1', first_usage.group(1).strip())

            # Other pages - small stamp
            else:
                self._replace_text(page, u'#5:10', self.decimal_num)
                self._replace_text(page, u'#5:11', str(index + 1))

        # Clear tables from labels
        for page in self.complist_pages:
            self._clear_page(page)

        # Merge all pages in single document
        # ODS
        if self.file_format == u'.ods':
            for table in self.complist_pages:
                self.complist.spreadsheet.addElement(table)
        # ODT
        elif self.file_format == u'.odt':  # pylint: disable=too-many-nested-blocks
            self.complist = self.complist_pages[0]
            if len(self.complist_pages) > 1:
                # Every style, frame or table must have unique name
                # on every separate page!
                for num, page in enumerate(self.complist_pages[1:]):
                    for autostyle in page.automaticstyles.childNodes[:]:
                        astyle_name = autostyle.getAttribute(u'name')
                        astyle_name = u'_{}_{}'.format(num + 2, astyle_name)
                        autostyle.setAttribute(u'name', astyle_name)
                        self.complist.automaticstyles.addElement(autostyle)
                    for body in page.body.childNodes[:]:
                        for frame in body.getElementsByType(Frame):
                            name = frame.getAttribute(u'name')
                            stylename = frame.getAttribute(u'stylename')
                            name = str(num + 2) + name
                            stylename = u'_{}_{}'.format(num + 2, stylename)
                            frame.setAttribute(u'name', name)
                            frame.setAttribute(u'stylename', stylename)
                            for table in frame.getElementsByType(Table):
                                name = table.getAttribute(u'name')
                                stylename = table.getAttribute(u'stylename')
                                name = str(num + 2) + name
                                stylename = u'_{}_{}'.format(num + 2, stylename)
                                table.setAttribute(u'name', name)
                                table.setAttribute(u'stylename', stylename)
                                for col in table.getElementsByType(TableColumn):
                                    stylename = col.getAttribute(u'stylename')
                                    stylename = u'_{}_{}'.format(num + 2, stylename)
                                    col.setAttribute(u'stylename', stylename)
                                for row in table.getElementsByType(TableRow):
                                    stylename = row.getAttribute(u'stylename')
                                    stylename = u'_{}_{}'.format(num + 2, stylename)
                                    row.setAttribute(u'stylename', stylename)
                                    for cell in row.getElementsByType(TableCell):
                                        stylename = cell.getAttribute(u'stylename')
                                        stylename = u'_{}_{}'.format(num + 2, stylename)
                                        cell.setAttribute(u'stylename', stylename)
                                        for paragraph in cell.getElementsByType(P):
                                            stylename = paragraph.getAttribute(u'stylename')
                                            stylename = u'_{}_{}'.format(num + 2, stylename)
                                            paragraph.setAttribute(u'stylename', stylename)
                        self.complist.body.addElement(body)

        # Add meta data
        version_file = codecs.open('version', 'r', encoding='utf-8')
        version = version_file.read()
        version = version.replace('\n', '')
        version_file.close()
        creation_time = time.localtime()
        creation_time_str = u'{year:04d}-{month:02d}-{day:02d}T{hour:02d}:{minutes:02d}:{sec:02d}'.format(
            year=creation_time.tm_year,
            month=creation_time.tm_mon,
            day=creation_time.tm_mday,
            hour=creation_time.tm_hour,
            minutes=creation_time.tm_min,
            sec=creation_time.tm_sec
            )
        self.complist.meta.addElement(meta.CreationDate(text=creation_time_str))
        self.complist.meta.addElement(meta.InitialCreator(text='kicadbom2spec v{}'.format(version)))

        # Set font style
        styles = self.complist.automaticstyles.childNodes + self.complist.styles.childNodes
        for style in styles:  # pylint: disable=too-many-nested-blocks
            for node in style.childNodes:
                if node.tagName == u'style:text-properties':
                    for attr_key in node.attributes:
                        if attr_key[-1] == u'font-style':
                            if self.italic:
                                node.attributes[attr_key] = u'italic'
                            else:
                                node.attributes[attr_key] = u'regular'
                            break
                    break

        # Save file of list of the components
        file_name = os.path.splitext(complist_file_name)[0] + self.file_format
        self.complist.save(file_name)

    @staticmethod
    def convert_decimal_num(num):
        """
        The correction of the decimal number (adding symbol "П" before the code
        of the schematic type).

        """
        num_parts = re.search(NUM_REGEXP, num)
        if num_parts is not None:
            if num_parts.group(1) is not None and num_parts.group(2) is not None:
                return u'П'.join(num_parts.groups())
        return num

    @staticmethod
    def convert_title(title):
        """
        The correction of the title.

        """
        suffix = u'Перечень элементов'
        title_parts = title.rsplit(u'Схема электрическая ', 1)
        sch_types = (
            u'структурная',
            u'функциональная',
            u'принципиальная',
            u'соединений',
            u'подключения',
            u'общая',
            u'расположения'
            )
        if len(title_parts) > 1 and title_parts[1] in sch_types:
            if not title_parts[0].endswith(u'\\n'):
                suffix = u'\\n' + suffix
            return title_parts[0] + suffix
        else:
            if title:
                suffix = u'\\n' + suffix
            return title + suffix

    def get_sheets(self, sch_file_name):
        """
        Return list of all hierarchical sheets used in schematic.

        """
        sheets = []
        exec_path = os.path.dirname(os.path.realpath(__file__))
        cur_path = os.path.dirname(sch_file_name)
        os.chdir(cur_path)
        sch = Schematic(sch_file_name)
        for item in sch.items:
            if item.__class__.__name__ == u'Sheet':
                sheets.append(
                    os.path.abspath(
                        os.path.join(cur_path, item.file_name)
                        )
                    )
                sheets.extend(
                    self.get_sheets(
                        os.path.abspath(os.path.join(cur_path, item.file_name))
                        )
                    )
        os.chdir(exec_path)
        return list(set(sheets))

    def get_components(self, sch_file_name, root_only=False):
        """
        Open KiCad Schematic file and get all components from it.

        """
        components = []
        if os.path.isabs(sch_file_name):
            exec_path = os.path.dirname(os.path.realpath(__file__))
            os.chdir(os.path.dirname(sch_file_name))
        sch = Schematic(sch_file_name)
        for item in sch.items:
            if item.__class__.__name__ == u'Comp':
                # Skip power symbols
                if not item.fields[0].text.startswith(u'#'):
                    components.append(item)
            elif item.__class__.__name__ == u'Sheet' and not root_only:
                components.extend(self.get_components(item.file_name))
        if os.path.isabs(sch_file_name):
            os.chdir(exec_path)
        return components
