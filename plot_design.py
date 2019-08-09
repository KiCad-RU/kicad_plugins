# coding: utf8
# plot_design.py
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

''' KiCad PCBNew Action Plugin for plot design files '''

import os
import pcbnew
import shutil
import sys
import tempfile
import zipfile


OUTPUT_NAME = 'design'
OUTPUT_DIR = '_generated_files' + os.path.sep + OUTPUT_NAME


class plot_design(pcbnew.ActionPlugin):
    def defaults(self):
        self.name = "Plot design files"
        self.category = "Plot files"
        self.description = "Plot design pcb and assembly files"
        self.icon_file_name = os.path.abspath(os.path.splitext(__file__)[0]) + '.svg'

    def Run(self):
        process_board(pcbnew.GetBoard())


def process_board(board):
    clean_output(get_output_abs_path(board))
    plot_layers(board)
    plot_drill_map(board)
    zip_output(get_output_abs_path(board), get_board_name(board) + '-' + OUTPUT_NAME)


def clean_output(path):
    if os.path.exists(path):
        shutil.rmtree(path, ignore_errors=False, onerror=None)
    os.makedirs(path)


def get_output_abs_path(board):
    path = os.path.dirname(os.path.abspath(board.GetFileName()))
    return path + os.path.sep + OUTPUT_DIR


def get_board_name(board):
    name = board.GetTitleBlock().GetComment1()
    if name == '':
        name = os.path.splitext(os.path.basename(board.GetFileName()))[0]
    return name


def plot_layers(board):
    plot_ctrl = pcbnew.PLOT_CONTROLLER(board)

    plot_opts = plot_ctrl.GetPlotOptions()
    plot_opts.SetOutputDirectory(OUTPUT_DIR)

    plot_opts.SetDXFPlotUnits(pcbnew.DXF_PLOTTER.DXF_UNIT_MILLIMETERS)
    plot_opts.SetDrillMarksType(pcbnew.PCB_PLOT_PARAMS.NO_DRILL_SHAPE)
    plot_opts.SetMirror(False)
    plot_opts.SetNegative(False)
    plot_opts.SetPlotFrameRef(False)
    plot_opts.SetPlotInvisibleText(False)
    plot_opts.SetPlotPadsOnSilkLayer(False)
    plot_opts.SetPlotReference(True)
    plot_opts.SetPlotValue(False)
    plot_opts.SetPlotViaOnMaskLayer(False)
    plot_opts.SetSubtractMaskFromSilk(True)
    plot_opts.SetUseAuxOrigin(True)

    plot_opts.SetExcludeEdgeLayer(False)
    plot_opts.SetDXFPlotPolygonMode(False)
    plot_opts.SetTextMode(pcbnew.PLOTTEXTMODE_NATIVE)

    plot_ctrl.SetLayer(pcbnew.F_Fab)
    plot_ctrl.OpenPlotfile('F_Fab', pcbnew.PLOT_FORMAT_DXF, 'F_Fab')
    plot_ctrl.PlotLayer()

    plot_ctrl.SetLayer(pcbnew.B_Fab)
    plot_ctrl.OpenPlotfile('B_Fab', pcbnew.PLOT_FORMAT_DXF, 'B_Fab')
    plot_ctrl.PlotLayer()

    plot_ctrl.SetLayer(pcbnew.Edge_Cuts)
    plot_ctrl.OpenPlotfile('Edge_Cuts', pcbnew.PLOT_FORMAT_DXF, 'Edge_Cuts')
    plot_ctrl.PlotLayer()

    plot_opts.SetExcludeEdgeLayer(True)
    plot_opts.SetDXFPlotPolygonMode(True)
    plot_opts.SetTextMode(pcbnew.PLOTTEXTMODE_STROKE)

    plot_ctrl.SetLayer(pcbnew.F_SilkS)
    plot_ctrl.OpenPlotfile('F_SilkS', pcbnew.PLOT_FORMAT_DXF, 'F_SilkS')
    plot_ctrl.PlotLayer()

    plot_ctrl.SetLayer(pcbnew.B_SilkS)
    plot_ctrl.OpenPlotfile('B_SilkS', pcbnew.PLOT_FORMAT_DXF, 'B_SilkS')
    plot_ctrl.PlotLayer()

    plot_ctrl.SetLayer(pcbnew.F_Mask)
    plot_ctrl.OpenPlotfile('F_Mask', pcbnew.PLOT_FORMAT_DXF, 'F_Mask')
    plot_ctrl.PlotLayer()

    plot_ctrl.SetLayer(pcbnew.B_Mask)
    plot_ctrl.OpenPlotfile('B_Mask', pcbnew.PLOT_FORMAT_DXF, 'B_Mask')
    plot_ctrl.PlotLayer()

    plot_ctrl.SetLayer(pcbnew.F_Cu)
    plot_ctrl.OpenPlotfile('F_Cu', pcbnew.PLOT_FORMAT_DXF, 'F_Cu')
    plot_ctrl.PlotLayer()

    cu_layer_count = board.GetDesignSettings().GetCopperLayerCount()
    for i in range(cu_layer_count - 2):
        plot_ctrl.SetLayer(pcbnew.In1_Cu + i)
        plot_ctrl.OpenPlotfile('In{0}_Cu'.format(i + 1), pcbnew.PLOT_FORMAT_DXF, 'In{0}_Cu'.format(i + 1))
        plot_ctrl.PlotLayer()

    plot_ctrl.SetLayer(pcbnew.B_Cu)
    plot_ctrl.OpenPlotfile('B_Cu', pcbnew.PLOT_FORMAT_DXF, 'B_Cu')
    plot_ctrl.PlotLayer()

    plot_ctrl.ClosePlot()


def plot_drill_map(board):
    #FIXME use mm units (Kicad BUG)
    gen_drill_map = pcbnew.EXCELLON_WRITER(board)
    gen_drill_map.SetMergeOption(False)
    gen_drill_map.SetMapFileFormat(pcbnew.PLOT_FORMAT_DXF)
    gen_drill_map.CreateDrillandMapFilesSet(get_output_abs_path(board), False, True)


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
    plot_design().register()
