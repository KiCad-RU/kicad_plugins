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
Python-wrapper for KiCad's Schematics and Libraries.

"""

import codecs


class ParsingError(Exception):
    """
    Exception for files with unsupported content.

    """

    def __init__(self, value):  # pylint: disable=super-init-not-called
        self.value = value

    def __str__(self):
        if isinstance(self.value, (str, unicode)):  # pylint: disable=undefined-variable
            return self.value
        return repr(self.value)


class Schematic(object):
    """
    Implementation of KiCad Schematic diagram file.
    Supported version: 4

    """
    EESCHEMA_FILE_STAMP = u'EESchema'
    SCHEMATIC_HEAD_STRING = u'Schematic File Version'

    def __init__(self, sch_name):
        """
        Load all contents from KiCad's Schematic file.

        Attributes:

            sch_name (unicode) - full name of KiCad Schematic file;
            version (int) - version of file format;
            libs (Libs) - list of used libraries;
            eelayer (list of Eelayer) - list of eelayer's information;
            descr (Descr) - title block description;
            items (list of Comp, Sheet, Bitmap, Connection, TextLabel, Wire or
        Entry) - list of all items in schematic.

        """
        self.sch_name = sch_name
        self.load(self.sch_name)

    def load(self, sch_name):  # pylint: disable=too-many-branches
        """
        Open KiCad Schematic file and read all information from it.

        Args:

            sch_name (unicode) - full name of KiCad Schematic file;

        """
        self.sch_name = sch_name
        self.libs = self.Libs(self)
        self.eelayer = []
        self.items = []

        sch_file = codecs.open(self.sch_name, 'r', 'utf-8')
        first_line = sch_file.readline()
        first_line = first_line.replace(u'\n', u'')
        if not first_line.startswith(self.EESCHEMA_FILE_STAMP):
            raise ParsingError(u'File "{}" is not KiCad Schematic.'.format(self.sch_name))
        self.version = int(split_line(first_line)[-1])
        for sch_line in sch_file:
            if sch_line.startswith(u'$'):
                if sch_line.startswith(u'$EndSCHEMATC'):
                    return
                item = sch_line
                item_val = u''
                while not sch_line.startswith(u'$End'):
                    item_val += sch_line
                    sch_line = sch_file.readline()
                if item.startswith(u'$Descr'):
                    self.descr = self.Descr(self, item_val)
                elif item.startswith(u'$Comp'):
                    self.items.append(self.Comp(self, item_val))
                elif item.startswith(u'$Sheet'):
                    self.items.append(self.Sheet(self, item_val))
                elif item.startswith(u'$Bitmap'):
                    self.items.append(self.Bitmap(self, item_val))
            elif sch_line.startswith(u'Connection'):
                self.items.append(self.Connection(self, sch_line))
            elif sch_line.startswith(u'NoConn'):
                self.items.append(self.Connection(self, sch_line))
            elif sch_line.startswith(u'Text'):
                sch_line += sch_file.readline()
                self.items.append(self.Text(self, sch_line))
            elif sch_line.startswith(u'Wire'):
                sch_line += sch_file.readline()
                self.items.append(self.Wire(self, sch_line))
            elif sch_line.startswith(u'Entry'):
                sch_line += sch_file.readline()
                self.items.append(self.Entry(self, sch_line))
            elif sch_line.startswith(u'LIBS:'):
                self.libs.add(sch_line)
            elif sch_line.startswith(u'EELAYER') and not u'END' in sch_line:
                self.eelayer.append(self.Eelayer(self, sch_line))

    def save(self, sch_name=None):
        """
        Save all content to KiCad Schematic file.

        Args:

            sch_name (unicode) - new name of schematic file (optional).

        """
        sch_file_name = self.sch_name
        if sch_name:
            sch_file_name = sch_name
        sch_file = codecs.open(sch_file_name, 'w', 'utf-8')

        first_line = u'{stamp} {head} {version}\n'.format(
            stamp=self.EESCHEMA_FILE_STAMP,
            head=self.SCHEMATIC_HEAD_STRING,
            version=self.version
            )
        sch_file.write(first_line)

        self.libs.save(sch_file)

        for eelayer in self.eelayer:
            eelayer.save(sch_file)
        sch_file.write(u'EELAYER END\n')

        self.descr.save(sch_file)

        for item in self.items:
            item.save(sch_file)

        sch_file.write(u'$EndSCHEMATC\n')
        sch_file.close()


    class Libs(list):
        """
        List of libraries used in schematic.

        """

        def __init__(self, schematic, *args):
            """
            Modified constructor of built-in type "list".

            Agrs:

                schematic (Schematic) - parent schematic.

            """
            list.__init__(self, *args)
            self.schematic = schematic

        def add(self, str_lib):
            """
            Extracts library name from string and add it to the list.

            Args:

                str_lib (unicode) - text line read from KiCad Schematic file.

            """
            str_lib = str_lib.rstrip(u'\n')
            lib_str = str_lib.replace(u'LIBS:', u'', 1)
            # In earlier versions libraries writes in single line
            # separated by comma.
            libs = lib_str.split(',')
            self.extend(libs)

        def save(self, sch_file):
            """
            Save current library name to KiCad Schematic file.

            Args:

                sch_file (file) - file for writing.

            """
            for lib in self:
                line = u'LIBS:{}\n'.format(lib)
                sch_file.write(line)


    class Eelayer(object):  # pylint: disable=too-few-public-methods
        """
        Description of EESchema layers (not used in Eeschema).

        Attributes:

            schematic (Schematic) - parent schematic;
            count (int) - number of layers;
            current (int) - current layer.

        """

        def __init__(self, schematic, str_eelayer):
            """
            Extracts EELAYER description from string.

            Args:

                schematic (Schematic) - parent schematic;
                str_eelayer (unicode) - text line read from KiCad Schematic file.

            """
            self.schematic = schematic
            str_eelayer = str_eelayer.lstrip(u'EELAYER ')
            parts = split_line(str_eelayer)
            self.count = int(parts[0])
            self.current = int(parts[1])

        def save(self, sch_file):
            """
            Save EELAYER description to KiCad Schematic file.

            Args:

                sch_file (file) - file for writing.

            """
            line = u'EELAYER {n} {c}\n'.format(
                n=self.count,
                c=self.current
                )
            sch_file.write(line)


    class Descr(object):  # pylint: disable=too-few-public-methods, too-many-instance-attributes
        """
        Title block description.

        Attributes:

            schematic (Schematic) - parent schematic;
            sheet_format (unicode) - string of sheet format (A4...A0, A...E);
            sheet_size_x (int) - width of sheet in mils (1/1000 inch);
            sheet_size_y (int) - height of sheet in mils;
            portrait (bool) - if True - orientation is portrait;
            encoding (srt) - encoding of text;
            sheet_number (int) - number of current sheet;
            sheet_count (int) - count of all sheets;
            title (unicode) - title of schematic;
            date (unicode) - date from title block;
            rev (srt) - revision of schematic;
            comp (unicode) - company name;
            comment1 (unicode) - comment #1 (GOST - decimal number);
            comment2 (unicode) - comment #2 (GOST - developer);
            comment3 (unicode) - comment #3 (GOST - verfier);
            comment4 (unicode) - comment #4 (GOST - approver);

        """

        def __init__(self, schematic, str_descr):  # pylint: disable=too-many-branches
            """
            Extracts title block description form strings.

            Args:

                schematic (Schematic) - parent schematic;
                str_descr (unicode) - text lines read from KiCad Schematic file.

            """
            self.schematic = schematic
            lines = str_descr.splitlines()
            for line in lines:
                parts = split_line(line)
                if parts[0] == u'$Descr':
                    self.sheet_format = parts[1]
                    self.sheet_size_x = int(parts[2])
                    self.sheet_size_y = int(parts[3])
                    self.portrait = False
                    if len(parts) > 3:
                        self.portrait = bool(parts[-1] == u'portrait')
                elif parts[0] == u'encoding':
                    self.encoding = parts[1]
                elif parts[0] == u'Sheet':
                    self.sheet_number = int(parts[1])
                    self.sheet_count = int(parts[2])
                elif parts[0] == u'Title':
                    self.title = parts[1]
                elif parts[0] == u'Date':
                    self.date = parts[1]
                elif parts[0] == u'Rev':
                    self.rev = parts[1]
                elif parts[0] == u'Comp':
                    self.comp = parts[1]
                elif parts[0] == u'Comment1':
                    self.comment1 = parts[1]
                elif parts[0] == u'Comment2':
                    self.comment2 = parts[1]
                elif parts[0] == u'Comment3':
                    self.comment3 = parts[1]
                elif parts[0] == u'Comment4':
                    self.comment4 = parts[1]

        def save(self, sch_file):
            """
            Save title block description to Schematic file.

            Args:

                sch_file (file) - file for writing.

            """
            descr = u'$Descr {paper} {width} {height}{portrait}\n' \
                    u'encoding {encoding}\n' \
                    u'Sheet {number} {count}\n' \
                    u'Title "{title}"\n' \
                    u'Date "{date}"\n' \
                    u'Rev "{rev}"\n' \
                    u'Comp "{comp}"\n' \
                    u'Comment1 "{comment1}"\n' \
                    u'Comment2 "{comment2}"\n' \
                    u'Comment3 "{comment3}"\n' \
                    u'Comment4 "{comment4}"\n' \
                    u'$EndDescr\n'.format(
                        paper=self.sheet_format,
                        width=self.sheet_size_x,
                        height=self.sheet_size_y,
                        portrait={True:u' portrait', False:u''}[self.portrait],
                        encoding=self.encoding,
                        number=self.sheet_number,
                        count=self.sheet_count,
                        title=self.title,
                        date=self.date,
                        rev=self.rev,
                        comp=self.comp,
                        comment1=self.comment1,
                        comment2=self.comment2,
                        comment3=self.comment3,
                        comment4=self.comment4
                        )
            sch_file.write(descr)


    class Comp(object):  # pylint: disable=too-few-public-methods, too-many-instance-attributes
        """
        Description of the component.

        Attributes:

            schematic (Schematic) - parent schematic;
            name (unicode) - name of the component in library;
            ref (unicode) - reference of the component;
            unit (int) - part of the component;
            path_and_ref (list of ["path", "ref", "part"]) - references of
                the components from complex hierarchy;
            convert (boot) - True - show as De Morgan convert, False - normal;
            timestamp (unicode) - timestamp of component;
            pos_x (int) - horizontal position of component;
            pos_y (int) - vertical position of component;
            fields (list of Field) - list of fields of the element;
            orient_matrix (tuple of 4 ints) - rotation matrix.

        """

        def __init__(self, schematic, str_comp):
            """
            Create description of component from strings.

            Args:

                schematic (Schematic) - parent schematic;
                str_comp (unicode) - text lines read from KiCad Schematic file.

            """
            self.schematic = schematic
            lines = str_comp.splitlines()
            self.fields = []
            for line in lines:
                parts = split_line(line)
                if parts[0] == u'L':
                    self.name = parts[1]
                    self.ref = parts[2]
                elif parts[0] == u'U':
                    self.unit = int(parts[1])
                    self.convert = (int(parts[2]) == 2)
                    self.timestamp = parts[3]
                elif parts[0] == u'P':
                    self.pos_x = int(parts[1])
                    self.pos_y = int(parts[2])
                elif parts[0] == u'AR':
                    if not hasattr(self, u'path_and_ref'):
                        self.path_and_ref = []
                    # Splitting gives list of two items:
                    # empty string and Value inside quotes.
                    # Strip method removes quotes around Value
                    # and leaves pure value.
                    ar_path = parts[1].split(u'Path=')[-1].strip(u'"')
                    ar_ref = parts[2].split(u'Ref=')[-1].strip(u'"')
                    ar_part = parts[3].split(u'Part=')[-1].strip(u'"')
                    item = [ar_path, ar_ref, ar_part]
                    self.path_and_ref.append(item)
                elif parts[0] == u'F':
                    self.fields.append(self.Field(self, line))
                elif parts[0].startswith(u'\t') \
                        or parts[0].startswith(u' '):
                    test_str = u'\t{unit:<4} {pos_x:<4} {pos_y:<4}'.format(
                        unit=self.unit,
                        pos_x=self.pos_x,
                        pos_y=self.pos_y
                        )
                    if line == test_str:
                        # Just check first line that starts with tab or space.
                        # It's redundant: not used
                        continue
                    else:
                        # Second line contains orientation matrix.
                        line = line.lstrip(u'\t ')
                        line = split_line(line)
                        self.orient_matrix = (int(line[0]), int(line[1]), \
                                              int(line[2]), int(line[3]))

        def save(self, sch_file):
            """
            Save description of the component to Schematic file.

            Args:

                sch_file (file) - file for writing.

            """
            comp_str = u'$Comp\n' \
                       u'L {name} {ref}\n' \
                       u'U {unit} {convert} {timestamp}\n' \
                       u'P {pos_x} {pos_y}\n'.format(
                           name=self.name,
                           ref=self.ref,
                           unit=self.unit,
                           convert={True:u'2', False:u'1'}[self.convert],
                           timestamp=self.timestamp,
                           pos_x=self.pos_x,
                           pos_y=self.pos_y
                           )
            sch_file.write(comp_str)
            if hasattr(self, u'path_and_ref'):
                for item in self.path_and_ref:
                    path_and_ref_str = u'AR Path="{path}" Ref="{ref}"  Part="{part}" \n'.format(
                        path=item[0],
                        ref=item[1],
                        part=item[2]
                        )
                    sch_file.write(path_and_ref_str)
            for field in self.fields:
                field.save(sch_file)
            comp_str = u'\t{unit:<4} {pos_x:<4} {pos_y:<4}\n' \
                       u'\t{or_m[0]:<4} {or_m[1]:<4} {or_m[2]:<4} {or_m[3]:<4}\n' \
                       u'$EndComp\n'.format(
                           unit=self.unit,
                           pos_x=self.pos_x,
                           pos_y=self.pos_y,
                           or_m=self.orient_matrix
                           )
            sch_file.write(comp_str)


        class Field(object):  # pylint: disable=too-few-public-methods, too-many-instance-attributes
            """
            Description of the field of the component.

            Attributes:

                comp (Comp) - parent component;
                number (int) - number of the field:
                    0 - reference;
                    1 - value;
                    2 - pcb footprint;
                    3 - doc link;
                    4, 5, ... - user specified;
                text (unicode) - text of field;
                orientation (unicode) - 'H' - horizontal, 'V' - vertical;
                pos_x (int) - horizontal position of the field;
                pos_y (int) - vertical position of the field;
                size (int) - size of the text;
                flags (unicode) - string of flags;
                hjustify (unicode) - horizontal justify:
                        'L' - left;
                        'C' - center;
                        'R' - right;
                vjustify (unicode) - vertical justify:
                        'T' - top;
                        'C' - center;
                        'B' - bottom;
                italic (bool) - if True - text is italic;
                bold (bool) - if True - text is bold;
                name (unicode) - name of the field (only if it is not default
            name).

            """

            def __init__(self, comp, str_field):
                """
                Create description of the field from string.

                Args:

                    comp (Comp) - parent component;
                    str_field (unicode) - text line from KiCad Schematic file.

                """
                self.comp = comp
                items = split_line(str_field)
                self.number = int(items[1])
                self.text = items[2]
                # make valid empty text value of field
                if self.number == 1 and self.text == u'~':
                    self.text = u''
                self.orientation = items[3]
                self.pos_x = int(items[4])
                self.pos_y = int(items[5])
                self.size = int(items[6])
                self.flags = items[7]
                self.hjustify = items[8]
                self.vjustify = items[9][0]
                self.italic = False
                self.bold = False
                if len(items[9]) == 3:
                    self.italic = {u'I':True, u'N':False}[items[9][1]]
                    self.bold = {u'B':True, u'N':False}[items[9][2]]
                self.name = u''
                if len(items) == 11:
                    self.name = items[10]

            def save(self, sch_file):
                """
                Save description of the field to Schematic file.

                Args:

                    sch_file (file) - file for writing.

                """
                # make valid empty text value of field
                if self.number == 1 and self.text == u'':
                    vtext = u'~'
                else:
                    vtext = self.text
                name = u''
                if self.name:
                    name = u' "{}"'.format(self.name)
                field_str = u'F {number} "{text}" {orient} {pos_x:<3} {pos_y:<3} {size:<3} {flags} {hjustify} {vjustify}{italic}{bold}{name}\n'.format(  # pylint: disable=line-too-long
                    number=self.number,
                    text=vtext,
                    orient=self.orientation,
                    pos_x=self.pos_x,
                    pos_y=self.pos_y,
                    size=self.size,
                    flags=self.flags,
                    hjustify=self.hjustify,
                    vjustify=self.vjustify,
                    italic={True:u'I', False:u'N'}[self.italic],
                    bold={True:u'B', False:u'N'}[self.bold],
                    name=name
                    )
                sch_file.write(field_str)


    class Sheet(object):  # pylint: disable=too-few-public-methods, too-many-instance-attributes
        """
        Description of the hierarchical sheet.

        Attributes:

            schematic (Schematic) - parent schematic;
            name (unicode) - name of the hierarchical sheet;
            name_size (int) - size of the text 'name';
            file_name (unicode) - name of the hierarchical sheet file;
            file_name_size (int) - size of the text 'file_name';
            pos_x (int) - horizontal position of the hierarchical sheet;
            pos_y (int) - vertical position of the hierarchical sheet;
            dim_x (int) - horizontal dimension of the hierarchical sheet;
            dim_y (int) - vertical dimension of the hierarchical sheet;
            timestamp (unicode) - time stamp;
            fields (list of Field) - list of fields of the hierarchical sheet.

        """

        def __init__(self, schematic, str_sheet):
            """
            Create description of hierarchical sheet from strings.

            Args:

                schematic (Schematic) - parent schematic;
                str_sheet (unicode) - text lines read from KiCad Schematic file.

            """
            self.schematic = schematic
            lines = str_sheet.splitlines()
            self.fields = []
            for line in lines:
                parts = split_line(line)
                if parts[0] == u'S':
                    self.pos_x = int(parts[1])
                    self.pos_y = int(parts[2])
                    self.dim_x = int(parts[3])
                    self.dim_y = int(parts[4])
                elif parts[0] == u'U':
                    self.timestamp = parts[1]
                elif parts[0].startswith(u'F'):
                    if int(parts[0][1:]) == 0:
                        self.name = parts[1]
                        self.name_size = parts[2]
                    elif int(parts[0][1:]) == 1:
                        self.file_name = parts[1]
                        self.file_name_size = parts[2]
                    elif int(parts[0][1:]) > 1:
                        self.fields.append(self.Field(self, line))

        def save(self, sch_file):
            """
            Save description of the hierarchical sheet to Schematic file.

            Args:

                sch_file (file) - file for writing.

            """
            sheet_str = u'$Sheet\n' \
                        u'S {pos_x:<4} {pos_y:<4} {dim_x:<4} {dim_y:<4}\n' \
                        u'U {timestamp}\n' \
                        u'F0 "{name}" {name_size}\n' \
                        u'F1 "{file_name}" {file_name_size}\n'.format(
                            pos_x=self.pos_x,
                            pos_y=self.pos_y,
                            dim_x=self.dim_x,
                            dim_y=self.dim_y,
                            timestamp=self.timestamp,
                            name=self.name,
                            name_size=self.name_size,
                            file_name=self.file_name,
                            file_name_size=self.file_name_size
                            )
            sch_file.write(sheet_str)
            for field in self.fields:
                field.save(sch_file)
            sheet_str = u'$EndSheet\n'
            sch_file.write(sheet_str)


        class Field(object):  # pylint: disable=too-few-public-methods, too-many-instance-attributes
            """
            Description of field of the hierarchical sheet.

            Attributes:

                sheet (Sheet) - parent hierarchical sheet;
                number (int) - number of the field (starts from 2);
                text (unicode) - text of field;
                form (unicode) - field format:
                    'I' - input;
                    'O' - output;
                    'B' - bidirectional;
                    'T' - tri state;
                    'U' - unspecified;
                side (unicode) - side of the field:
                    'L' - left;
                    'R' - right;
                    'T' - top;
                    'B' - bottom;
                pos_x (int) - horizontal position of the field;
                pos_y (int) - vertical position of the field;
                dimension (int) - dimension of the field;

            """

            def __init__(self, sheet, str_field):
                """
                Create description of the field from string.

                Args:

                    sheet (Sheet) - parent hierarchical sheet;
                    str_field (unicode) - text line from KiCad Schematic file.

                """
                self.sheet = sheet
                items = split_line(str_field)
                self.number = items[0][1:]
                self.text = items[1]
                self.form = items[2]
                self.side = items[3]
                self.pos_x = int(items[4])
                self.pos_y = int(items[5])
                self.dimension = int(items[6])

            def save(self, sch_file):
                """
                Save description of the field to Schematic file.

                Args:

                    sch_file (file) - file for writing.

                """
                field_str = u'F{number} "{text}" {form} {side} {pos_x:<3} {pos_y:<3} {dim:<3}\n'.format(  # pylint: disable=line-too-long
                    number=self.number,
                    text=self.text,
                    form=self.form,
                    side=self.side,
                    pos_x=self.pos_x,
                    pos_y=self.pos_y,
                    dim=self.dimension
                    )
                sch_file.write(field_str)


    class Bitmap(object):  # pylint: disable=too-few-public-methods
        """
        Description of the bitmap.

        Attributes:

            schematic (Schematic) - parent schematic;
            pos_x (int) - horizontal position of the bitmap;
            pos_y (int) - vertical position of the bitmap;
            scale (float) - scale of the bitmap;
            data (list of int) - byte array of the png data.

        """

        def __init__(self, schematic, str_bitmap):
            """
            Create description of bitmap from strings.

            Args:

                schematic (Schematic) - parent schematic;
                str_bitmap (unicode) - text lines read from KiCad Schematic file.

            """
            self.schematic = schematic
            lines = str_bitmap.splitlines()
            self.data = []
            data_block = False
            for line in lines:
                if data_block:
                    if line.startswith(u'EndData'):
                        break
                    line = line.rstrip(u' ')
                    byte_array = split_line(line)
                    for byte in byte_array:
                        if byte == u'$EndBitmap':
                            # Fix for bug in Eeschema:
                            # marker '$EndBitmap' present in data block.
                            # https://bugs.launchpad.net/kicad/+bug/1200836
                            continue
                        self.data.append(int(byte, 16))
                elif line.startswith(u'Pos'):
                    parts = split_line(line)
                    self.pos_x = parts[1]
                    self.pos_y = parts[2]
                elif line.startswith(u'Scale'):
                    parts = split_line(line)
                    self.scale = float(parts[1].replace(u',', u'.'))
                elif line.startswith(u'Data'):
                    data_block = True

        def save(self, sch_file):
            """
            Save description of the bitmap to Schematic file.

            Args:

                sch_file (file) - file for writing.

            """
            data_str = u''
            i = 0
            for byte in self.data:
                i += 1
                data_str += u'{:02X} '.format(byte)
                if i == 32:
                    i = 0
                    data_str += u'\n'
            bitmap_str = u'$Bitmap\n' \
                         u'Pos {pos_x:<4} {pos_y:<4}\n' \
                         u'Scale {scale:.6f}\n' \
                         u'Data\n' \
                         u'{data}\n' \
                         u'EndData\n' \
                         u'$EndBitmap\n'.format(
                             pos_x=self.pos_x,
                             pos_y=self.pos_y,
                             scale=self.scale,
                             data=data_str
                             )
            sch_file.write(bitmap_str)


    class Connection(object):  # pylint: disable=too-few-public-methods
        """
        Description of the connection (junction) or no connection position.

        Attributes:

            schematic (Schematic) - parent schematic;
            tpye (unicode) - type of the connection (Connection, NoConn);
            pos_x (int) - horizontal position of the connection;
            pos_y (int) - vertical position of the connection.

        """

        def __init__(self, schematic, str_connection):
            """
            Create description of the connection from string.

            Args:

                schematic (Schematic) - parent schematic;
                str_connect (unicode) - text line read from KiCad Schematic.

            """
            self.schematic = schematic
            str_connection.replace(u'\n', u'')
            parts = split_line(str_connection)
            self.type = parts[0]
            self.pos_x = int(parts[2])
            self.pos_y = int(parts[3])

        def save(self, sch_file):
            """
            Save description of the connection to Schematic file.

            Args:

                sch_file (file) - file for writing;

            """
            connection_str = u'{conn_type} ~ {pos_x:<4} {pos_y:<4}\n'.format(
                conn_type=self.type,
                pos_x=self.pos_x,
                pos_y=self.pos_y
                )
            sch_file.write(connection_str)


    class Text(object):  # pylint: disable=too-few-public-methods, too-many-instance-attributes
        """
        Description of the text label.

        Attributes:

            schematic (Schematic) - parent schematic;
            type (unicode) - type of the text label (Notes, Label, GLable, HLabel);
            text (unicode) - text of the label;
            pos_x (int) - horizontal position of the text label;
            pos_y (int) - vertical position of the text label;
            orientation (int) - orientation of the text label;
            dimension (int) - dimension of the text label;
            shape (unicode) - shape type of the text label (only for GLabel and
        HLabel);

            # May not exists in old versions:
            italic (bool) - True - if text is italic;
            bold (int) - coefficient of the bold text.

        """

        def __init__(self, schematic, str_text):
            """
            Create description of the text label from string.

            Args:

                schematic (Schematic) - parent schematic;
                str_connect (unicode) - text line read from KiCad Schematic.

            """
            self.schematic = schematic
            lines = str_text.splitlines()
            parts = split_line(lines[0])
            self.type = parts[1]
            self.pos_x = int(parts[2])
            self.pos_y = int(parts[3])
            self.orientation = int(parts[4])
            self.dimension = int(parts[5])
            index = 5
            if parts[1] in (u'GLabel', u'HLabel'):
                self.shape = parts[6]
                index += 1
            self.italic = False
            self.bold = 0
            if self.schematic.version > 1:
                # The following options do not exists in version 1 schematic
                # files and not always in version 2 for Hlabels and GLabels.
                if self.schematic.version > 2 or len(parts) > index+1:
                    self.italic = {u'Italic':True, u'~':False}[parts[index+1]]
                    index += 1
                if len(parts) > index+1:
                    self.bold = int(parts[index+1])
            self.text = lines[1]

        def save(self, sch_file):
            """
            Save description of the text label to Schematic file.

            Args:

                sch_file (file) - file for writing;

            """
            shape = u''
            if self.type in (u'GLabel', u'HLabel'):
                shape = u' ' + self.shape
            text_str = u'Text {label_type} {pos_x:<4} {pos_y:<4} {orient:<4} {dim:<4}{shape} {italic} {bold}\n{text}\n'.format(  # pylint: disable=line-too-long
                label_type=self.type,
                pos_x=self.pos_x,
                pos_y=self.pos_y,
                orient=self.orientation,
                dim=self.dimension,
                shape=shape,
                italic={True:u'Italic', False:u'~'}[self.italic],
                bold=self.bold,
                text=self.text
                )
            sch_file.write(text_str)


    class Wire(object):  # pylint: disable=too-few-public-methods, too-many-instance-attributes
        """
        Description of the wire.

        Attributes:

            schematic (Schematic) - parent schematic;
            type (unicode) - type of the wire (Note, Wire, Bus);
            start_x (int) - horizontal coordinates of the start position;
            start_y (int) - vertical coordinates of the start position;
            end_x (int) - horizontal coordinates of the end position;
            end_y (int) - vertical coordinates of the end position.

            # Since Sept 15, 2017, custom line width/style/color allowed.
            # Only non default values are stored.
            width (int) - width of line in mils;
            style (unicode) - style of line (solid, dashed, dotted, dash_dot);
            color (unicode) - color in CSS format: rgb(0, 0, 0) rgba(0, 0, 0, 0)

        """

        def __init__(self, schematic, str_wire):
            """
            Create description of the wire from string.

            Args:

                schematic (Schematic) - parent schematic;
                str_connect (unicode) - text line read from KiCad Schematic.

            """
            self.schematic = schematic
            lines = str_wire.splitlines()
            parts = split_line(lines[0])
            self.type = parts[1]
            if len(parts) > 3:
                # Custom width/style/color is present.
                # Present is optional but sequence is strict.
                custom_parts = parts[3:]
                if custom_parts[0] == u'width':
                    self.width = int(custom_parts[1])
                    custom_parts = custom_parts[2:]
                if custom_parts and custom_parts[0] == u'style':
                    self.style = custom_parts[1]
                    custom_parts = custom_parts[2:]
                if custom_parts and custom_parts[0].startswith(u'rgb'):
                    self.color = u' '.join(custom_parts)
            parts = split_line(lines[1])
            self.start_x = int(parts[0].lstrip(u'\t'))
            self.start_y = int(parts[1])
            self.end_x = int(parts[2])
            self.end_y = int(parts[3])

        def save(self, sch_file):
            """
            Save description of the wire to Schematic file.

            Args:

                sch_file (file) - file for writing;

            """
            custom_options = u''
            if hasattr(self, u'width'):
                custom_options += u' width ' + str(self.width)
            if hasattr(self, u'style'):
                custom_options += u' style ' + self.style
            if hasattr(self, u'color'):
                custom_options += u' ' + self.color
            wire_str = u'Wire {wire_type} Line{custom}\n' \
                       u'\t{start_x:<4} {start_y:<4} {end_x:<4} {end_y:<4}\n'.format(
                           wire_type=self.type,
                           custom=custom_options,
                           start_x=self.start_x,
                           start_y=self.start_y,
                           end_x=self.end_x,
                           end_y=self.end_y
                           )
            sch_file.write(wire_str)



    class Entry(object):  # pylint: disable=too-few-public-methods
        """
        Description of the entry.

        Attributes:

            schematic (Schematic) - parent schematic;
            type (unicode) - type of the wire (Wire Line, Bus Bus);
            start_x (int) - horizontal coordinates of the start position;
            start_y (int) - vertical coordinates of the start position;
            end_x (int) - horizontal coordinates of the end position;
            end_y (int) - vertical coordinates of the end position.

        """

        def __init__(self, schematic, str_entry):
            """
            Create description of the entry from string.

            Args:

                schematic (Schematic) - parent schematic;
                str_connect (unicode) - text line read from KiCad Schematic.

            """
            self.schematic = schematic
            lines = str_entry.splitlines()
            parts = split_line(lines[0])
            self.type = u'{type_parts[1]} {type_parts[2]}'.format(type_parts=parts)  # pylint: disable=invalid-format-index
            parts = split_line(lines[1])
            self.start_x = int(parts[0].lstrip(u'\t'))
            self.start_y = int(parts[1])
            self.end_x = int(parts[2])
            self.end_y = int(parts[3])

        def save(self, sch_file):
            """
            Save description of the entry to Schematic file.

            Args:

                sch_file (file) - file for writing;

            """
            entry_str = u'Entry {entry_type}\n' \
                        u'\t{start_x:<4} {start_y:<4} {end_x:<4} {end_y:<4}\n'.format(
                            entry_type=self.type,
                            start_x=self.start_x,
                            start_y=self.start_y,
                            end_x=self.end_x,
                            end_y=self.end_y
                            )
            sch_file.write(entry_str)


class Library(object):
    """
    Implementation of KiCad Schematic library.
    Supported version: 2.4

    """
    LIBFILE_IDENT = u'EESchema-LIBRARY Version'

    def __init__(self, lib_name):
        """
        Load all contents from KiCad's Schematic library.

        Attributes:

            lib_name (unicode) - full name of KiCad Schematic library file;
            version_major (int) - major version of file format (1..);
            version_minor (int) - minor version of file format (1..99);
            encoding (srt) - encoding of text;
            components (list of Component) - list of components of library.

        """
        self.lib_name = lib_name
        self.load(self.lib_name)

    def load(self, lib_name):
        """
        Open KiCad Schematic library file and read all information from it.

        Args:

            lib_name (unicode) - full name of KiCad Schematic library file;

        """
        self.lib_name = lib_name
        self.components = []

        lib_file = codecs.open(self.lib_name, 'r', 'utf-8')
        first_line = lib_file.readline()
        first_line = first_line.replace(u'\n', u'')
        if not first_line.startswith(self.LIBFILE_IDENT):
            raise ParsingError(u'File "{}" is not KiCad Schematic Library.'.format(self.lib_name))
        # Header can contains date in old versions:
        # EESchema-LIBRARY Version 2.0 24/1/1997-18:9:6
        version_str = split_line(first_line)[2]
        major_str, minor_str = version_str.split(u'.')
        self.version_major = int(major_str)
        self.version_minor = int(minor_str)
        for lib_line in lib_file:
            lib_line = lib_line
            if lib_line.startswith(u'DEF'):
                component_value = u''
                while not lib_line.startswith(u'ENDDEF'):
                    component_value += lib_line
                    lib_line = lib_file.readline()
                self.components.append(self.Component(self, component_value))
            elif lib_line.startswith(u'#encoding'):
                self.encoding = split_line(lib_line)[-1].replace(u'\n', u'')
            elif lib_line.startswith(u'#End Library'):
                return

    def save(self, new_name=None):
        """
        Save all content to KiCad Schematic library file.

        Args:

            lib_name (unicode) - new name of schematic library file (optional).

        """
        lib_file_name = self.lib_name
        if new_name:
            lib_file_name = new_name
        lib_file = codecs.open(lib_file_name, 'w', 'utf-8')

        header = u'{file_id} {major}.{minor}\n' \
                 u'#encoding {encoding}\n'.format(
                     file_id=self.LIBFILE_IDENT,
                     major=self.version_major,
                     minor=self.version_minor,
                     encoding=self.encoding
                     )
        lib_file.write(header)
        for component in self.components:
            component.save(lib_file)
        lib_file.write(u'#\n#End Library\n')
        lib_file.close()


    class Component(object):  # pylint: disable=too-few-public-methods, too-many-instance-attributes
        """
        Description of the component of a library.

        Attributes:

            library (Library) - parent library;
            name (unicode) - component name in library;
            reference (unicode) - reference of component;
            text_offset (int) - offset for pin name position;
            draw_pinnumber (bool) - True - display number, False - do not display number;
            draw_pinname (bool) - True - display name, False do not display name;
            unit_count (int) - number of part (or section) in component;
            units_locked (bool) - True - units are not identical and cannot be swapped,
        False - units are identical and therefore can be swapped;
            power_flag (bool) - False - normal, True - component type "power" (optional);
            fields (list of Field) - list of component fields;
            aliases (list of str) - list of aliases (exists only if the component has alias names);
            fplist (list of str) - list of footprints assigned to component (if specified);
            graphic_elements (list of Polygon, Rectangle, Circle, Arc, Text,
        Pin) - list of all graphical elements of a component.

        """

        def __init__(self, library, str_component):  # pylint: disable=too-many-branches
            """
            Create description of library component from strings.

            Args:

                library (Library) - parent library;
                str_component (unicode) - text lines read from KiCad Schematic library file.

            """
            self.library = library
            lines = str_component.splitlines()
            self.aliases = []
            self.fields = []
            self.graphic_elements = []
            footprint = False
            for line in lines:
                parts = split_line(line)
                if footprint:
                    if parts[0] == u'$ENDFPLIST':
                        footprint = False
                    else:
                        self.fplist.append(parts[0])  # pylint: disable=access-member-before-definition
                elif parts[0] == u'DEF':
                    self.name = parts[1]
                    self.reference = parts[2]
                    # parts[3] - NumOfPins, unused
                    self.text_offset = int(parts[4])
                    self.draw_pinnumber = {u'Y':True, u'N':False}[parts[5]]
                    self.draw_pinname = {u'Y':True, u'N':False}[parts[6]]
                    self.unit_count = int(parts[7])
                    # In version 2.2 and earlier parameter 'unit_locked' not
                    # used and always had value '0' (just place holder).
                    self.units_locked = {u'L':True, u'F':False, u'0':False}[parts[8]]
                    self.power_flag = False
                    if len(parts) > 9:
                        # Power flag is optional
                        self.power_flag = {u'P':True, u'N':False}[parts[9]]
                elif parts[0] == u'ALIAS':
                    self.aliases = parts[1:]
                elif parts[0].startswith(u'F'):
                    self.fields.append(self.Field(self, line))
                elif parts[0] == u'P':
                    self.graphic_elements.append(self.Polygon(self, line))
                elif parts[0] == u'S':
                    self.graphic_elements.append(self.Rectangle(self, line))
                elif parts[0] == u'C':
                    self.graphic_elements.append(self.Circle(self, line))
                elif parts[0] == u'A':
                    self.graphic_elements.append(self.Arc(self, line))
                elif parts[0] == u'T':
                    self.graphic_elements.append(self.Text(self, line))
                elif parts[0] == u'X':
                    self.graphic_elements.append(self.Pin(self, line))
                elif parts[0] == u'$FPLIST':
                    footprint = True
                    self.fplist = []

        def save(self, lib_file):
            """
            Save description of the component to Schematic library file.

            Args:

                lib_file (file) - file for writing.

            """
            nick = self.name
            if nick.startswith(u'~'):
                nick = nick.replace(u'~', u'', 1)
            component_str = u'#\n' \
                            u'# {nick}\n' \
                            u'#\n' \
                            u'DEF {name} {ref} 0 {offset} {pin_num} {pin_name} {unit_count} {units_locked} {power_flag}\n'.format(  # pylint: disable=line-too-long
                                nick=nick,
                                name=self.name,
                                ref=self.reference,
                                offset=str(self.text_offset),
                                pin_num={True:u'Y', False:u'N'}[self.draw_pinnumber],
                                pin_name={True:u'Y', False:u'N'}[self.draw_pinname],
                                unit_count=str(self.unit_count),
                                units_locked={True:u'L', False:u'F'}[self.units_locked],
                                power_flag={True:u'P', False:u'N'}[self.power_flag]
                                )
            lib_file.write(component_str)
            for field in self.fields:
                field.save(lib_file)
            component_str = u''
            if self.aliases:
                component_str += u'ALIAS {}\n'.format(u' '.join(self.aliases))
            if hasattr(self, u'fplist'):
                component_str += u'$FPLIST\n'
                for footprint in self.fplist:
                    component_str += u' {}\n'.format(footprint)
                component_str += u'$ENDFPLIST\n'
            component_str += u'DRAW\n'
            lib_file.write(component_str)
            for graphic_element in self.graphic_elements:
                graphic_element.save(lib_file)
            component_str = u'ENDDRAW\n' \
                            u'ENDDEF\n'
            lib_file.write(component_str)


        class Field(object):  # pylint: disable=too-few-public-methods, too-many-instance-attributes
            """
            Description of the field of the library component.

            Attributes:

                component (Component) - parent component;
                number (int) - number of the field:
                    0 - reference;
                    1 - name;
                    2 - pcb footprint;
                    3 - doc link;
                    4, 5, ... - user specified;
                text (unicode) - text of field;
                pos_x (int) - horizontal position of the field;
                pos_y (int) - vertical position of the field;
                diamension (int) - diamension of the text;
                orientation (unicode) - 'H' - horizontal, 'V' - vertical;
                visibility (bool) - True - text is visible, False - text is invisible;
                hjustify (unicode) - horizontal justify:
                        'L' - left;
                        'C' - center;
                        'R' - right;
                vjustify (unicode) - vertical justify:
                        'T' - top;
                        'C' - center;
                        'B' - bottom;
                italic (bool) - if True - text is italic;
                bold (bool) - if True - text is bold;
                name (unicode) - name of the field (only if it is not default
            name).

            """

            def __init__(self, component, str_field):
                """
                Create description of the field from string.

                Args:

                    component (Component) - parent component;
                    str_field (unicode) - text line from KiCad Schematic library file.

                """
                self.component = component
                items = split_line(str_field)
                self.number = int(items[0][1:])
                self.text = items[1]
                self.pos_x = int(items[2])
                self.pos_y = int(items[3])
                self.diamension = int(items[4])
                self.orientation = items[5]
                self.visibility = {u'V':True, u'I':False}[items[6]]
                self.hjustify = items[7]
                self.vjustify = items[8][0]
                self.italic = False
                self.bold = False
                if len(items[8]) == 3:
                    self.italic = {u'I':True, u'N':False}[items[8][1]]
                    self.bold = {u'B':True, u'N':False}[items[8][2]]
                self.name = u''
                if len(items) > 9:
                    self.name = items[9]

            def save(self, lib_file):
                """
                Save description of the field to Schematic file.

                Args:

                    lib_file (file) - file for writing.

                """
                name = u''
                if self.name:
                    name = u' "{}"'.format(self.name)
                field_str = u'F{number} "{text}" {pos_x} {pos_y} {size} {orient} {visibility} {hjustify} {vjustify}{italic}{bold}{name}\n'.format(  # pylint: disable=line-too-long
                    number=self.number,
                    text=self.text,
                    pos_x=self.pos_x,
                    pos_y=self.pos_y,
                    size=self.diamension,
                    orient=self.orientation,
                    visibility={True:u'V', False:u'I'}[self.visibility],
                    hjustify=self.hjustify,
                    vjustify=self.vjustify,
                    italic={True:u'I', False:u'N'}[self.italic],
                    bold={True:u'B', False:u'N'}[self.bold],
                    name=name
                    )
                lib_file.write(field_str)


        class Polygon(object):  # pylint: disable=too-few-public-methods
            """
            Description of the polygon.

            Attributes:

                component (Component) - parent component;
                unit (int) - 0 if common to the parts; if not, number of part (1. .n);
                convert (int) - 0 if common to the 2 representations, if not 1 or 2;
                thickness (int) - line thickness;
                points (list of [x(int), y(int)]) - list of x and y coordinates of points;
                fill (unicode) - F - fill foreground, f - fill background, N - do not fill.

            """

            def __init__(self, component, str_polygon):
                """
                Create description of the polygon.

                Args:

                    component (Component) - parent component;
                    str_polygon (unicode) - text line from KiCad Schematic library file.

                """
                self.component = component
                items = split_line(str_polygon)
                self.unit = int(items[2])
                self.convert = int(items[3])
                self.thickness = int(items[4])
                offset = 5
                self.points = []
                for point in range(int(items[1])):
                    x_pos = items[offset + point*2]
                    y_pos = items[offset + point*2 + 1]
                    self.points.append([x_pos, y_pos])
                if items[-1] in (u'F', u'f', u'N'):
                    self.fill = items[-1]
                else:
                    self.fill = u'N'

            def save(self, lib_file):
                """
                Save description of the polygon to Schematic library file.

                Args:

                    lib_file (file) - file for writing.

                """
                polygon_str = u'P {p_count} {unit} {convert} {thickness}'.format(
                    p_count=len(self.points),
                    unit=self.unit,
                    convert=self.convert,
                    thickness=self.thickness
                    )
                for point in self.points:
                    polygon_str += u' {p[0]} {p[1]}'.format(p=point)
                polygon_str += u' {}\n'.format(self.fill)
                lib_file.write(polygon_str)


        class Rectangle(object):  # pylint: disable=too-few-public-methods, too-many-instance-attributes
            """
            Description of the rectangle.

            Attributes:

                component (Component) - parent component;
                start_x (int) - x coordinate of rectangle start;
                start_y (int) - y coordinate of rectangle start;
                end_x (int) - x coordinate of rectangle end;
                end_y (int) - y coordinate of rectangle end;
                unit (int) - 0 if common to the parts; if not, number of part (1. .n);
                convert (int) - 0 if common to the 2 representations, if not 1 or 2;
                thickness (int) - line thickness;
                fill (unicode) - F - fill foreground, f - fill background, N - do not fill.

            """

            def __init__(self, component, str_rectangle):
                """
                Create description of the rectangle.

                Args:

                    component (Component) - parent component;
                    str_rectangle (unicode) - text line from KiCad Schematic library file.

                """
                self.component = component
                items = split_line(str_rectangle)
                self.start_x = int(items[1])
                self.start_y = int(items[2])
                self.end_x = int(items[3])
                self.end_y = int(items[4])
                self.unit = int(items[5])
                self.convert = int(items[6])
                self.thickness = int(items[7])
                self.fill = u'N'
                if len(items) > 8:
                    self.fill = items[8]

            def save(self, lib_file):
                """
                Save description of the rectangle to Schematic library file.

                Args:

                    lib_file (file) - file for writing.

                """
                rectangle_str = u'S {start_x} {start_y} {end_x} {end_y} {unit} {convert} {thickness} {fill}\n'.format(  # pylint: disable=line-too-long
                    start_x=self.start_x,
                    start_y=self.start_y,
                    end_x=self.end_x,
                    end_y=self.end_y,
                    unit=self.unit,
                    convert=self.convert,
                    thickness=self.thickness,
                    fill=self.fill
                    )
                lib_file.write(rectangle_str)


        class Circle(object):  # pylint: disable=too-few-public-methods, too-many-instance-attributes
            """
            Description of the circle.

            Attributes:

                component (Component) - parent component;
                pos_x (int) - x coordinate of circle center position;
                pos_y (int) - y coordinate of circle center position;
                radius (int) - radius of circle;
                unit (int) - 0 if common to the parts; if not, number of part (1. .n);
                convert (int) - 0 if common to the 2 representations, if not 1 or 2;
                thickness (int) - line thickness;
                fill (unicode) - F - fill foreground, f - fill background, N - do not fill.

            """

            def __init__(self, component, str_circle):
                """
                Create description of the circle.

                Args:

                    component (Component) - parent component;
                    str_circle (unicode) - text line from KiCad Schematic library file.

                """
                self.component = component
                items = split_line(str_circle)
                self.pos_x = int(items[1])
                self.pos_y = int(items[2])
                self.radius = int(items[3])
                self.unit = int(items[4])
                self.convert = int(items[5])
                self.thickness = int(items[6])
                self.fill = u'N'
                if len(items) > 7:
                    self.fill = items[7]

            def save(self, lib_file):
                """
                Save description of the circle to Schematic library file.

                Args:

                    lib_file (file) - file for writing.

                """
                circle_str = u'C {pos_x} {pos_y} {radius} {unit} {convert} {thickness} {fill}\n'.format(  # pylint: disable=line-too-long
                    pos_x=self.pos_x,
                    pos_y=self.pos_y,
                    radius=self.radius,
                    unit=self.unit,
                    convert=self.convert,
                    thickness=self.thickness,
                    fill=self.fill
                    )
                lib_file.write(circle_str)


        class Arc(object):  # pylint: disable=too-few-public-methods, too-many-instance-attributes
            """
            Description of the arc.

            Attributes:

                component (Component) - parent component;
                pos_x (int) - x coordinate of arc center position;
                pos_y (int) - y coordinate of arc center position;
                radius (int) - radius of arc;
                start (int) - angle of the starting point (in 0,1 degrees);
                end (int) - angle of the end point (in 0,1 degrees);
                unit (int) - 0 if common to the parts; if not, number of part (1. .n);
                convert (int) - 0 if common to the 2 representations, if not 1 or 2;
                thickness (int) - line thickness;
                fill (unicode) - F - fill foreground, f - fill background, N - do not fill;
                start_x (int) - x coordinate of the starting point (role similar to start);
                start_y (int) - y coordinate of the starting point (role similar to start);
                end_x (int) - x coordinate of the ending point (role similar to end);
                end_y (int) - y coordinate of the ending point (role similar to end).

            """

            def __init__(self, component, str_arc):
                """
                Create description of the arc.

                Args:

                    component (Component) - parent component;
                    str_arc (unicode) - text line from KiCad Schematic library file.

                """
                self.component = component
                items = split_line(str_arc)
                self.pos_x = int(items[1])
                self.pos_y = int(items[2])
                self.radius = int(items[3])
                self.start = int(items[4])
                self.end = int(items[5])
                self.unit = int(items[6])
                self.convert = int(items[7])
                self.thickness = int(items[8])
                self.fill = u'N'
                index = 9
                if len(items) > index:
                    # Old libraries (version <= 2.2) do not have always FILLMODE.
                    if items[9] in (u'F', u'f', u'N'):
                        self.fill = items[9]
                        index += 1
                    if len(items) > index:
                        # Coordinates of start and end points saves in new libraries.
                        # Earlier this coordinates calculating at loading.
                        self.start_x = int(items[index])
                        self.start_y = int(items[index+1])
                        self.end_x = int(items[index+2])
                        self.end_y = int(items[index+3])

            def save(self, lib_file):
                """
                Save description of the arc to Schematic library file.

                Args:

                    lib_file (file) - file for writing.

                """
                start_end_points = u''
                if hasattr(self, 'start_x') \
                        and hasattr(self, 'start_y') \
                        and hasattr(self, 'end_x') \
                        and hasattr(self, 'end_y'):
                    start_end_points = ' {start_x} {start_y} {end_x} {end_y}'.format(
                        start_x=self.start_x,
                        start_y=self.start_y,
                        end_x=self.end_x,
                        end_y=self.end_y
                        )
                arc_str = u'A {pos_x} {pos_y} {radius} {start} {end} {unit} {convert} {thickness} {fill}{points}\n'.format(  # pylint: disable=line-too-long
                    pos_x=self.pos_x,
                    pos_y=self.pos_y,
                    radius=self.radius,
                    start=self.start,
                    end=self.end,
                    unit=self.unit,
                    convert=self.convert,
                    thickness=self.thickness,
                    fill=self.fill,
                    points=start_end_points
                    )
                lib_file.write(arc_str)


        class Text(object):  # pylint: disable=too-few-public-methods, too-many-instance-attributes
            """
            Description of the text.

            Attributes:

                component (Component) - parent component;
                angle (int) - angle of the text (in 0,1 degrees);
                pos_x (int) - x coordinate of text position;
                pos_y (int) - y coordinate of text position;
                size (int) - size of text;
                attr (int) - attributs of the text (visibility etc);
                unit (int) - 0 if common to the parts; if not, number of part (1. .n);
                convert (int) - 0 if common to the 2 representations, if not 1 or 2;
                text (unicode) - text;
                italic (bool) - True - text is italic, False - text is normal;
                bold (bool) - True - text is bold, False - text is normal;
                hjustify (unicode) - horizontal justify:
                        'L' - left;
                        'C' - center;
                        'R' - right;
                vjustify (unicode) - vertical justify:
                        'B' - bottom;
                        'C' - center;
                        'T' - top.

            """

            def __init__(self, component, str_text):
                """
                Create description of the text.

                Args:

                    component (Component) - parent component;
                    str_text (unicode) - text line from KiCad Schematic library file.

                """
                self.component = component
                items = split_line(str_text)
                self.angle = int(items[1])
                self.pos_x = int(items[2])
                self.pos_y = int(items[3])
                self.size = int(items[4])
                self.attr = int(items[5])
                self.unit = int(items[6])
                self.convert = int(items[7])
                self.text = items[8]
                # Default values
                self.italic = False
                self.bold = False
                self.hjustify = u'C'
                self.vjustify = u'C'
                if len(items) > 9:
                    self.italic = {u'Italic':True, u'Normal':False}[items[9]]
                    self.bold = {u'1':True, u'0':False}[items[10]]
                    if len(items) > 11:
                        self.hjustify = items[11]
                        self.vjustify = items[12]

            def save(self, lib_file):
                """
                Save description of the text to Schematic library file.

                Args:

                    lib_file (file) - file for writing.

                """
                text = self.text
                if u'~' in text or u"''" in text:
                    text = u'"{}"'.format(text)
                text_str = u'T {angle} {pos_x} {pos_y} {size} {attr} {unit} {convert} {text} {italic} {bold} {hjustify} {vjustify}\n'.format(  # pylint: disable=line-too-long
                    angle=self.angle,
                    pos_x=self.pos_x,
                    pos_y=self.pos_y,
                    size=self.size,
                    attr=self.attr,
                    unit=self.unit,
                    convert=self.convert,
                    text=text,
                    italic={True:u'Italic', False:u'Normal'}[self.italic],
                    bold={True:1, False:0}[self.bold],
                    hjustify=self.hjustify,
                    vjustify=self.vjustify
                    )
                lib_file.write(text_str)


        class Pin(object):  # pylint: disable=too-few-public-methods, too-many-instance-attributes
            """
            Description of the pin.

            Attributes:

                component (Component) - parent component;
                name (unicode) - name of the pin ("~" - if empty);
                number (unicode) - number of the pin ("~" - if empty);
                pos_x (int) - x coordinate of pin position;
                pos_y (int) - y coordinate of pin position;
                length (int) - length of the pin;
                orientation (unicode) - orientation of the pin:
                    'U' - up;
                    'D' - down;
                    'L' - left;
                    'R' - right;
                number_size (int) - size of number text label;
                name_size (int) - size of name text label;
                unit (int) - 0 if common to the parts; if not, number of part (1. .n);
                convert (int) - 0 if common to the 2 representations, if not 1 or 2;
                electric_type (unicode) - electric type:
                    'I' - input;
                    'O' - output;
                    'B' - BiDi;
                    'T' - tristate;
                    'P' - passive;
                    'U' - unspecified;
                    'W' - power input;
                    'w' - power output;
                    'C' - open collector;
                    'E' - open emitter;
                    'N' - not connected;
                shape (unicode) - if present:
                    'N' - invisible;
                    'I' - inverted;
                    'C' - clock;
                    'L' - input low;
                    'V' - output low;
                    'F' - falling adge low;
                    'X' - non logic;

            """

            def __init__(self, component, str_pin):
                """
                Create description of the pin.

                Args:

                    component (Component) - parent component;
                    str_pin (unicode) - text line from KiCad Schematic library file.

                """
                self.component = component
                items = split_line(str_pin)
                self.name = items[1]
                self.number = items[2]
                self.pos_x = int(items[3])
                self.pos_y = int(items[4])
                self.length = int(items[5])
                self.orientation = items[6]
                self.number_size = int(items[7])
                self.name_size = int(items[8])
                self.unit = int(items[9])
                self.convert = int(items[10])
                self.electric_type = items[11]
                if len(items) == 13:
                    self.shape = items[12]

            def save(self, lib_file):
                """
                Save description of the text to Schematic library file.

                Args:

                    lib_file (file) - file for writing.

                """
                shape = u''
                if hasattr(self, u'shape'):
                    shape = u' {}'.format(self.shape)
                pin_str = u'X {name} {num} {pos_x} {pos_y} {length} {orient} {num_size} {name_size} {unit} {convert} {el_type}{shape}\n'.format(  # pylint: disable=line-too-long
                    name=self.name,
                    num=self.number,
                    pos_x=self.pos_x,
                    pos_y=self.pos_y,
                    length=self.length,
                    orient=self.orientation,
                    num_size=self.number_size,
                    name_size=self.name_size,
                    unit=self.unit,
                    convert=self.convert,
                    el_type=self.electric_type,
                    shape=shape
                    )
                lib_file.write(pin_str)


def split_line(str_to_split):
    """
    Split string by whitespace considering text in quotes.

    For example, string:
        u'    str1 str2  "str 3" str 4 '
    will be converted to list:
        [u'str1', u'str2', u'str 3', u'str', u'4']

    Args:

        str_to_split (unicode) - string that must be splint.

    Returns:

        output (list of unicode) - list of strings.

    """
    items = str_to_split.split(u' ')
    output = []
    quoted = False
    for item in items:
        if not quoted and item.startswith(u'"'):
            if item.endswith(u'"') and not item.endswith(u'\\"') and \
               len(item) > 1:
                quoted = False
                output.append(item[1:-1])
            else:
                quoted = True
                output.append(item[1:])
            continue
        elif quoted:
            if item.endswith(u'"') and not item.endswith(u'\\"'):
                quoted = False
                output[-1] += u' ' + item[:-1]
                continue
            else:
                output[-1] += u' ' + item
        else:
            if item:
                output.append(item)
    return output
