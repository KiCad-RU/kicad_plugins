# coding: utf8
# plot_gerber_and_drill.py
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

''' KiCad PCBNew Action Plugin for plot gerber and drill files '''

import os
import pcbnew
import shutil
import sys
import tempfile
import zipfile


OUTPUT_NAME = 'gerber'
OUTPUT_DIR = '_generated_files' + os.path.sep + OUTPUT_NAME


class plot_gerber_and_drill(pcbnew.ActionPlugin):
    def defaults(self):
        self.name = "Plot gerber and drill files"
        self.category = "Plot files"
        self.description = "Plot gerber and drill files"
        self.icon_file_name = os.path.abspath(os.path.splitext(__file__)[0]) + '.svg'

    def Run(self):
        process_board(pcbnew.GetBoard())


def process_board(board):
    clean_output(get_output_abs_path(board))
    plot_layers(board)
    plot_drill(board)
    zip_output(get_output_abs_path(board), get_board_name(board) + '-' + OUTPUT_NAME)


def clean_output(path):
    if os.path.exists(path):
        shutil.rmtree(path, ignore_errors=False, onerror=None)
    os.makedirs(path)


def get_output_abs_path(board):
    return os.path.dirname(board.GetFileName()) + os.path.sep + OUTPUT_DIR


def get_board_name(board):
    return os.path.splitext(os.path.basename(board.GetFileName()))[0]


def plot_layers(board):
    plot_ctrl = pcbnew.PLOT_CONTROLLER(board)

    plot_opts = plot_ctrl.GetPlotOptions()
    plot_opts.SetOutputDirectory(OUTPUT_DIR)

    plot_opts.SetCreateGerberJobFile(False)
    plot_opts.SetExcludeEdgeLayer(True)
    plot_opts.SetGerberPrecision(6)
    plot_opts.SetIncludeGerberNetlistInfo(False)
    plot_opts.SetPlotFrameRef(False)
    plot_opts.SetPlotInvisibleText(False)
    plot_opts.SetPlotMode(pcbnew.FILLED)
    plot_opts.SetPlotPadsOnSilkLayer(False)
    plot_opts.SetPlotReference(True)
    plot_opts.SetPlotValue(False)
    plot_opts.SetPlotViaOnMaskLayer(False)
    plot_opts.SetSkipPlotNPTH_Pads(False)
    plot_opts.SetSubtractMaskFromSilk(True)
    plot_opts.SetUseAuxOrigin(True)
    plot_opts.SetUseGerberAttributes(False)
    plot_opts.SetUseGerberProtelExtensions(False)
    plot_opts.SetUseGerberX2format(False)

    plot_ctrl.SetLayer(pcbnew.Edge_Cuts)
    plot_ctrl.OpenPlotfile('Edge_Cuts', pcbnew.PLOT_FORMAT_GERBER, 'Edge_Cuts')
    plot_ctrl.PlotLayer()

    plot_ctrl.SetLayer(pcbnew.F_SilkS)
    plot_ctrl.OpenPlotfile('F_SilkS', pcbnew.PLOT_FORMAT_GERBER, 'F_SilkS')
    plot_ctrl.PlotLayer()

    plot_ctrl.SetLayer(pcbnew.B_SilkS)
    plot_ctrl.OpenPlotfile('B_SilkS', pcbnew.PLOT_FORMAT_GERBER, 'B_SilkS')
    plot_ctrl.PlotLayer()

    plot_ctrl.SetLayer(pcbnew.F_Mask)
    plot_ctrl.OpenPlotfile('F_Mask', pcbnew.PLOT_FORMAT_GERBER, 'F_Mask')
    plot_ctrl.PlotLayer()

    plot_ctrl.SetLayer(pcbnew.B_Mask)
    plot_ctrl.OpenPlotfile('B_Mask', pcbnew.PLOT_FORMAT_GERBER, 'B_Mask')
    plot_ctrl.PlotLayer()

    plot_ctrl.SetLayer(pcbnew.F_Cu)
    plot_ctrl.OpenPlotfile('F_Cu', pcbnew.PLOT_FORMAT_GERBER, 'F_Cu')
    plot_ctrl.PlotLayer()

    cu_layer_count = board.GetDesignSettings().GetCopperLayerCount()
    for i in range(cu_layer_count - 2):
        plot_ctrl.SetLayer(pcbnew.In1_Cu + i)
        plot_ctrl.OpenPlotfile('In{0}_Cu'.format(i + 1), pcbnew.PLOT_FORMAT_GERBER, 'In{0}_Cu'.format(i + 1))
        plot_ctrl.PlotLayer()

    plot_ctrl.SetLayer(pcbnew.B_Cu)
    plot_ctrl.OpenPlotfile('B_Cu', pcbnew.PLOT_FORMAT_GERBER, 'B_Cu')
    plot_ctrl.PlotLayer()

    plot_ctrl.SetLayer(pcbnew.F_Paste)
    plot_ctrl.OpenPlotfile('F_Paste', pcbnew.PLOT_FORMAT_GERBER, 'F_Paste')
    plot_ctrl.PlotLayer()

    plot_ctrl.SetLayer(pcbnew.B_Paste)
    plot_ctrl.OpenPlotfile('B_Paste', pcbnew.PLOT_FORMAT_GERBER, 'B_Paste')
    plot_ctrl.PlotLayer()

    plot_ctrl.ClosePlot()


def plot_drill(board):
    gen_drill = pcbnew.EXCELLON_WRITER(board)
    gen_drill.SetFormat(True, pcbnew.GENDRILL_WRITER_BASE.KEEP_ZEROS)
    gen_drill.SetOptions(False, False, board.GetAuxOrigin(), False)
    gen_drill.SetRouteModeForOvalHoles(True)
    gen_drill.CreateDrillandMapFilesSet(get_output_abs_path(board), True, False)


def zip_output(path, name):
    temp_dir = tempfile.mkdtemp()
    zip_name = temp_dir + os.path.sep + name
    shutil.make_archive(zip_name, 'zip', path)
    shutil.move(zip_name + '.zip', path)
    os.rmdir(temp_dir)


if __name__ == '__main__':
    board = pcbnew.LoadBoard(sys.argv[1])
    process_board(board)
else:
    plot_gerber_and_drill().register()
