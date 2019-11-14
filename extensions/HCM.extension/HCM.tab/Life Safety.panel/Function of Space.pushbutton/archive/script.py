"""Manage project keynotes.

Shift+Click:
Reset window configurations and open.
"""
#pylint: disable=E0401,W0613,C0111,C0103,C0302,W0703
import os
import os.path as op
import shutil
import math
from collections import defaultdict

from pyrevit import HOST_APP
from pyrevit import framework
from pyrevit.framework import System
from pyrevit import coreutils
from pyrevit import revit, DB, UI
from pyrevit import forms
from pyrevit import script

from pyrevit.coreutils.loadertypes import UIDocUtils

__title__ = "Function of\nSpace"
__author__ = "{{author}}"
__context__ = ""

logger = script.get_logger()
output = script.get_output()

class CodeItem():
    def __init__(self, function, load_factor, load_type, source):
        self.function = function
        self.load_factor = load_factor
        self.load_type = load_type
        self.source = source

class CreateScheduleWindow(forms.WPFWindow):
    def __init__(self, xaml_file_name):
        forms.WPFWindow.__init__(self, xaml_file_name)

        # Default values for UI
        self.CodeTypeComboBox.ItemsSource = self.get_code_types()
        self.CodeYearComboBox.ItemsSource = self.get_code_years()
        self.ScheduleComboBox.ItemsSource = self.get_schedules()
        self.CodeTypeComboBox.SelectedItem = "IBC"
        self.CodeYearComboBox.SelectedItem = "2012"
        self.ScheduleComboBox.SelectedItem = None
        self.CodePreviewDataGrid.ItemsSource = self.get_codes(self.code_type + " " + self.code_year)

    @property
    def code_type(self):
        return self.CodeTypeComboBox.SelectedItem
    
    @property
    def code_year(self):
        return self.CodeYearComboBox.SelectedItem

    @property
    def schedule_name(self):
        return self.ScheduleNameTextBox.Text

    @property
    def schedule(self):
        return self.ScheduleComboBox.SelectedItem
    
    def get_codes(self, key):
        self.codes = {
            "IBC 2012": [
                CodeItem("Accessory Areas - Mechanical and Storage", "300", "gsf", "IBC 2012, Table 1004"),
                CodeItem("Assembly Use - Commercial Kitchens", "200", "gsf", "IBC 2012, Table 1004"),
                CodeItem("Assembly Use - Concentrated", "7", "nsf", "IBC 2012, Table 1004"),
                CodeItem("Assembly Use - Concentrated", "7", "nsf", "IBC 2012, Table 1004"),
                CodeItem("Assembly Use - Exercise Rooms", "50", "gsf", "IBC 2012, Table 1004"),
                CodeItem("Assembly Use - Exhibits Galleries and Museums", "30", "nsf", "IBC 2012, Table 1004"),
                CodeItem("Assembly Use - Fixed Seating", "0", "Fixed", "IBC 2012, Table 1004"),
                CodeItem("Assembly Use - Library Reading Rooms", "50", "nsf", "IBC 2012, Table 1004"),
                CodeItem("Assembly Use - Library Stack Areas", "100", "gsf", "IBC 2012, Table 1004"),
                CodeItem("Assembly Use - Stages and Platforms", "15", "nsf", "IBC 2012, Table 1004"),
                CodeItem("Assembly Use - Standing Space", "5", "nsf", "IBC 2012, Table 1004"),
                CodeItem("Assembly Use - Unconcentrated", "15", "nsf", "IBC 2012, Table 1004"),
                CodeItem("Business Use - General", "100", "gsf", "IBC 2012, Table 1004"),
                CodeItem("Educational Use - Classrooms", "20", "nsf", "IBC 2012, Table 1004"),
                CodeItem("Educational Use - Shops and Laboratories", "50", "nsf", "IBC 2012, Table 1004"),
                CodeItem("Health Care Use - Inpatient Sleeping",	"120", "gsf", "IBC 2012, Table 1004"),
                CodeItem("Health Care Use - Inpatient Treatment", "240", "gsf", "IBC 2012, Table 1004"),
                CodeItem("Health Care Use - Outpatient/Ambulatory Care", "100", "gsf", "IBC 2012, Table 1004"),
                CodeItem("Mercantile Use - Basement and Grade Floor", "30", "gsf", "IBC 2012, Table 1004"),
                CodeItem("Mercantile Use - All Other Floors", "60", "gsf", "IBC 2012, Table 1004"),
                CodeItem("Mercantile Use - Storage, Stock, and Shipping Areas", "300", "gsf", "IBC 2012, Table 1004"),
                CodeItem("Parking Garage", "200", "gsf", "IBC 2012, Table 1004"),
                CodeItem("Unoccupied", "0", "N/A", "N/A"),
            ],
            "IBC 2015": [
                CodeItem("Accessory Mechanical and Storage Areas", "300", "gsf", "IBC 2015, Table 1004")
            ],
            "IBC 2018": [
                CodeItem("Accessory Mechanical and Storage Areas", "300", "gsf", "IBC 2018, Table 1004")
            ],
            "NFPA 101 2012": [
                CodeItem("Accessory Mechanical and Storage Areas", "300", "gsf", "IBC 2018, Table 1004")
            ],
            "NFPA 101 2015": [
                CodeItem("Accessory Mechanical and Storage Areas", "300", "gsf", "IBC 2018, Table 1004")
            ],
            "NFPA 101 2018": [
                CodeItem("Accessory Mechanical and Storage Areas", "300", "gsf", "IBC 2018, Table 1004")
            ]
        }
        return self.codes[key]

    def get_code_types(self):
        return ["IBC", "NFPA 101"]

    def get_code_years(self):
        return ["2012", "2015", "2018"]
    
    def get_schedules(self):
        schedules = DB.FilteredElementCollector(revit.doc)\
                        .OfClass(framework.get_type(DB.ViewSchedule))\
                        .WhereElementIsNotElementType()\
                        .ToElements()
        return [x for x in schedules if x.Definition.IsKeySchedule]

    def CodeYearTypeSelectionChanged(self, sender, args):
        if self.code_type == None or self.code_year == None:
            return

        self.CodePreviewDataGrid.ItemsSource = self.get_codes(self.code_type + " " + self.code_year)
    
    def ScheduleSelectionChanged(self, sender, args):
        if self.schedule == None:
            return
        
        has_load_factor = False
        has_load_type = False
        has_source = False
        fields = self.schedule.Definition.GetSchedulableFields()

        for field in fields:
            parameter = revit.doc.GetElement(field.ParameterId)
            if parameter == None:
                continue
        
            if parameter.Name == "LS Occupant Load Factor_Key":
                has_load_factor = True
                continue
            elif parameter.Name == "LS OL Factor Net Gross Fixed_Key":
                has_load_type = True
                continue
            elif parameter.Name == "LS Code Source_Key":
                has_source = True
                continue
        
        if not (has_load_factor and has_load_type and has_source):
            forms.alert("Select LS Function of Space Schedule that has all needed parameters.")

    def OkButtonClick(self, sender, args):
        data = self.get_codes(self.code_type + " " + self.code_year)

        existing_rows = DB.FilteredElementCollector(revit.doc, self.schedule.Id)\
                            .WhereElementIsNotElementType()\
                            .ToElementIds()
        try:
            with revit.Transaction("Clean Existing Schedule") as t:
                revit.doc.Delete(existing_rows)
        except:
            pass
        
        try:
            with revit.Transaction("Create Rows") as t:
                table_data = self.schedule.GetTableData()
                section_data = table_data.GetSectionData(DB.SectionType.Body)
                for i in data:
                    section_data.InsertRow(0)
            
                new_rows = DB.FilteredElementCollector(revit.doc, self.schedule.Id)\
                            .WhereElementIsNotElementType()\
                            .ToElements()
                for row, value in zip(new_rows, data):
                    key_name = row.LookupParameter("Key Name")
                    if key_name != None:
                        key_name.Set(value.function)
                    load_factor = row.LookupParameter("LS Occupant Load Factor_Key")
                    if load_factor != None:
                        load_factor.Set(value.load_factor)
                    load_type = row.LookupParameter("LS OL Factor Net Gross Fixed_Key")
                    if load_type != None:
                        load_type.Set(value.load_type)
                    source = row.LookupParameter("LS Code Source_Key")
                    if source != None:
                        source.Set(value.source)
        except:
            pass
        
        self.Close()

    def CancelButtonClick(self, sender, args):
        self.Close()

    def show(self):
        self.ShowDialog()

try:
    CreateScheduleWindow(xaml_file_name='FunctionOfSpace.xaml').show()
except Exception as kmex:
    forms.alert(str(kmex))