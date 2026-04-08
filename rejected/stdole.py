from enum import IntFlag

import comtypes.gen._00020430_0000_0000_C000_000000000046_0_2_0 as __wrapper_module__
from comtypes.gen._00020430_0000_0000_C000_000000000046_0_2_0 import (
    EXCEPINFO, OLE_XSIZE_PIXELS, Picture, Color, CoClass,
    IEnumVARIANT, IFont, _check_version, DISPPROPERTY,
    OLE_YSIZE_HIMETRIC, FONTNAME, COMMETHOD, OLE_XPOS_HIMETRIC,
    IUnknown, DISPPARAMS, IPicture, Library, Font, Default, dispid,
    Checked, StdFont, Unchecked, StdPicture, DISPMETHOD, OLE_HANDLE,
    FONTUNDERSCORE, OLE_YPOS_CONTAINER, OLE_CANCELBOOL, VARIANT_BOOL,
    VgaColor, OLE_YSIZE_PIXELS, FONTITALIC, OLE_XPOS_CONTAINER, BSTR,
    OLE_YSIZE_CONTAINER, IFontEventsDisp, HRESULT, FontEvents,
    typelib_path, OLE_COLOR, IFontDisp, GUID, OLE_XSIZE_CONTAINER,
    FONTSTRIKETHROUGH, OLE_ENABLEDEFAULTBOOL, OLE_XSIZE_HIMETRIC,
    FONTBOLD, OLE_OPTEXCLUSIVE, Monochrome, OLE_YPOS_HIMETRIC,
    FONTSIZE, IDispatch, IPictureDisp, OLE_YPOS_PIXELS,
    OLE_XPOS_PIXELS, Gray, _lcid
)


class OLE_TRISTATE(IntFlag):
    Unchecked = 0
    Checked = 1
    Gray = 2


class LoadPictureConstants(IntFlag):
    Default = 0
    Monochrome = 1
    VgaColor = 2
    Color = 4


__all__ = [
    'FONTUNDERSCORE', 'OLE_YPOS_CONTAINER', 'OLE_CANCELBOOL',
    'OLE_XSIZE_PIXELS', 'Picture', 'VgaColor', 'OLE_YSIZE_PIXELS',
    'FONTITALIC', 'OLE_XPOS_CONTAINER', 'Color', 'IFont',
    'OLE_YSIZE_CONTAINER', 'IFontEventsDisp', 'OLE_YSIZE_HIMETRIC',
    'FONTNAME', 'FontEvents', 'typelib_path', 'OLE_TRISTATE',
    'IFontDisp', 'OLE_COLOR', 'OLE_XPOS_HIMETRIC', 'IPicture',
    'OLE_XSIZE_CONTAINER', 'FONTSTRIKETHROUGH',
    'OLE_ENABLEDEFAULTBOOL', 'Library', 'OLE_XSIZE_HIMETRIC',
    'FONTBOLD', 'OLE_OPTEXCLUSIVE', 'LoadPictureConstants', 'Font',
    'Default', 'Monochrome', 'Checked', 'OLE_YPOS_HIMETRIC',
    'FONTSIZE', 'StdFont', 'IPictureDisp', 'OLE_YPOS_PIXELS',
    'Unchecked', 'StdPicture', 'OLE_XPOS_PIXELS', 'Gray', 'OLE_HANDLE'
]

