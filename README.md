# kicad_plugins
Contain:
- Footprint Wizard Plugin for generating Russia packages
- PCBNew Action Plugin for ploting design (pcb and assembly) files
- PCBNew Action Plugin for ploting gerber and drill files

**WARNING: next not work with format .kicad_sch only old .sch**
- PCBNew Action Plugin for generating BOM and Specification files (GOST). TODO: implement new sch BOM generator
- PCBNew Action Plugin for generating Pos files. TODO: use sch BOM generator .xml instead .sch

Remarks: last two use result of kicadbom2spec application. TODO: no use.

## Install
See [KiCad PCBNew documentation](https://docs.kicad.org/7.0/en/pcbnew/pcbnew.html#scripting)

## Links
Files kicadsch.py and complist.py from [kicadbom2spec](https://github.com/KiCad-RU/kicadbom2spec)
