"""Copies all values from Occupant Load Factors Keys into Occupant Load Factor parameter."""

from pyrevit import revit, DB
from pyrevit import script
from pyrevit.output import PyRevitOutputWindow
from pyrevit.revit import query

__title__ = "Copy Load\nFactors"
__author__ = "{{author}}"
__context__ = ""

logger = script.get_logger()
output = script.get_output()

output.print_md('*****\n\n\n###PROCESSED AREAS:\n')

def print_area(a, prefix='', print_id=True, missing_key=False):
    if missing_key:
        outstr = "Area: {} doesn't have assigned Function of Space.".format(query.get_param(a, 'Name', '').AsString())
    else:
        outstr = 'Name: {} processed successfully!'.format(query.get_param(a, 'Name', '').AsString())
    if print_id:
        outstr = PyRevitOutputWindow.linkify(a.Id) + '\t' + outstr
    print(prefix + outstr)

areas = DB.FilteredElementCollector(revit.doc)\
         .OfCategory(DB.BuiltInCategory.OST_Areas)\
         .WhereElementIsNotElementType()

with revit.Transaction("Copy LS Occupant Load Factors") as t:
    for a in areas:
        key = a.LookupParameter("LS Occupant Load Factor_Key")
        if (key == None or key.HasValue == False):
            print_area(a, prefix='\t\t', print_id=True, missing_key=True)
        else:
            param = query.get_param(a, 'LS Occupant Load Factor', '')
            if param != None:
                param.Set(float(key.AsString()))
                print_area(a, prefix='\t\t', print_id=True, missing_key=False)
        