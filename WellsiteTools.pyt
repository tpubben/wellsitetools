import arcpy
import os
import csv
from tkinter import *


class Toolbox(object):
    def __init__(self):
        """Define the toolbox (the name of the toolbox is the name of the
        .pyt file)."""
        self.label = "WellsiteTools"
        self.alias = "Wellsite Geo Tools"

        # List of tool classes associated with this toolbox
        self.tools = [StartWellTool, AddSurveyTool]


class StartWellTool(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Start Well"
        self.description = ""
        self.canRunInBackground = False

    def getParameterInfo(self):
        """Define parameter definitions"""
        param0 = arcpy.Parameter(
            displayName='KB elevation',
            name='kbElevation',
            datatype='GPDouble',
            parameterType='Required',
            direction='Input'
        )

        param1 = arcpy.Parameter(
            displayName='Wellhead UTM Easting',
            name='utmE',
            datatype='GPDouble',
            parameterType='Required',
            direction='Input'
        )

        param2 = arcpy.Parameter(
            displayName='Wellhead UTM Northing',
            name='utmN',
            datatype='GPDouble',
            parameterType='Required',
            direction='Input'
        )

        param3 = arcpy.Parameter(
            displayName='Wellname',
            name='wellname',
            datatype='GPString',
            parameterType='Required',
            direction='Input'
        )

        param4 = arcpy.Parameter(
            displayName='UWI',
            name='uwi',
            datatype='GPString',
            parameterType='Required',
            direction='Input'
        )

        param5 = arcpy.Parameter(
            displayName='Project Database',
            name='projFolder',
            datatype='DEWorkspace',
            parameterType='Required',
            direction='Input'
        )

        param6 = arcpy.Parameter(
            displayName='Coordinate System',
            name='coordSys',
            datatype='GPSpatialReference',
            parameterType='Required',
            direction='Input'
        )

        param7 = arcpy.Parameter(
            displayName='Survey File',
            name='surFile',
            datatype='DETextfile',
            direction='Input',
            parameterType='Optional'
        )

        param8 = arcpy.Parameter(
            displayName='Survey Column Order',
            name='colOrder',
            datatype='GPValueTable',
            parameterType='Optional',
            direction='Input'
        )

        param8.parameterDependencies = [param7.name]
        param8.columns = [['Field', 'Field'], ['GPString', 'Column']]
        param8.filters[1].type = 'ValueList'
        param8.values = [['MD', 1], ['TVD', 4], ['Northing', 6], ['Easting', 7]]
        param8.filters[1].list = [1, 2, 3, 4, 5, 6, 7, 8, 9]

        params = [param0, param1, param2, param3, param4, param5, param6, param7, param8]
        return params

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        arcpy.env.workspace = parameters[5].valueAsText
        arcpy.env.overwriteOutput = True
        wellName = parameters[3].valueAsText
        kbElev = float(parameters[0].valueAsText)
        utmE = float(parameters[1].valueAsText)
        utmN = float(parameters[2].valueAsText)
        uwi = parameters[4].valueAsText
        tblName = 'c_' + uwi
        # split the name out of the Spatial Reference object
        utmdat = parameters[6].valueAsText
        utmdat = utmdat[7:]
        utmdat = utmdat.split("'")[1]
        sur_file = parameters[7].valueAsText
        col_list = parameters[8].valueAsText.split(';')
        # set variables for each column
        m, t, n, e = int(col_list[0][-1]) - 1, int(col_list[1][-1]) - 1, int(col_list[2][-1]) - 1, int(
            col_list[3][-1]) - 1

        # create table for well center
        arcpy.CreateTable_management(parameters[5].valueAsText, tblName)
        arcpy.management.AddFields(tblName, [['wellName', 'TEXT', 'Well Name', None]])
        arcpy.management.AddFields(tblName, [['UWI', 'TEXT', 'UWI', None]])
        arcpy.management.AddFields(tblName, [['KBElev', 'DOUBLE', 'KB Elevation', None]])
        arcpy.management.AddFields(tblName, [['utmE', 'DOUBLE', 'UTM Easting', None]])
        arcpy.management.AddFields(tblName, [['utmN', 'DOUBLE', 'UTM Northing', None]])
        arcpy.management.AddFields(tblName, [['UTMDat', 'TEXT', 'UTM Datum', None]])

        # add information to table
        fields = ['wellName', 'UWI', 'KBElev', 'utmE', 'utmN', 'UTMDat']
        cursor = arcpy.da.InsertCursor(tblName, fields)
        cursor.insertRow((wellName, uwi, kbElev, utmE, utmN, utmdat))
        del cursor

        # check if a survey file has been provided, if it is then import all surveys to a new feature
        if sur_file != None:
            with open(sur_file, 'r') as sf:
                sl = []
                # read lines in provided survey file and find only the ones with survey data
                for line in sf:
                    line = line.strip().split()
                    if len(line) > 0 and line[0][0].isdigit():
                        sl.append(line)

            # create feature class for points
            tpm_points = 'p_'+ uwi
            arcpy.CreateFeatureclass_management(parameters[5].valueAsText, tpm_points, 'POINT', has_z='ENABLED',
                                                spatial_reference=parameters[6].valueAsText)
            arcpy.management.AddFields(tpm_points, [['MD', 'DOUBLE', 'MD', None]])
            arcpy.management.AddFields(tpm_points, [['TVD', 'DOUBLE', 'TVD', None]])
            arcpy.management.AddFields(tpm_points, [['EAST', 'DOUBLE', 'NORTH', None]])
            arcpy.management.AddFields(tpm_points, [['NORTH', 'DOUBLE', 'EAST', None]])

            # continue on with assigning each column to the appropriate value
            fields = ['MD', 'TVD', 'EAST', 'NORTH']
            cursor = arcpy.da.InsertCursor(tpm_points, ['MD', 'TVD', 'EAST', 'NORTH', 'SHAPE@Z', 'SHAPE@XY'])
            for item in sl:
                # m, t, n, e were defined from parameter 8
                md, tvd, east, north = float(item[m]), float(item[t]), float(item[e]), float(item[n])
                surveys = [md, utmE+east, utmN+north, kbElev-tvd, (utmE+east, utmN+north)]
                cursor.insertRow(surveys)

            arcpy.PointsToLine_management(tpm_points, 'w_'+uwi)
            # delete temp point feature
            # arcpy.Delete_management(tpm_points)
            # add surveys to map




            del cursor


        else:
            pass

        return


class AddSurveyTool(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Add Surveys"
        self.description = ""
        self.canRunInBackground = False

    def getParameterInfo(self):
        """Define parameter definitions"""
        param0 = arcpy.Parameter(
            displayName='Select Well',
            name='wellSelect',
            datatype='DEFeatureClass',
            parameterType='Required',
            direction='Input'
        )

        param1 = arcpy.Parameter(
            displayName='Survey File',
            name='surFile',
            datatype='DETextfile',
            direction='Input',
            parameterType='Optional'
        )

        param2 = arcpy.Parameter(
            displayName='Survey Column Order',
            name='colOrder',
            datatype='GPValueTable',
            parameterType='Optional',
            direction='Input'
        )

        param3 = arcpy.Parameter(
            displayName='Coordinate System',
            name='coordSys',
            datatype='GPSpatialReference',
            parameterType='Required',
            direction='Input'
        )

        params = [param0, param1, param2, param3]
        return params

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        well_file = parameters[0].valueAsText
        sur_file = parameters[1].valueAsText
        col_list = parameters[2].valueAsText.split(';')
        utmdat = parameters[3].valueAsText
        # set variables for each column
        m, t, n, e = int(col_list[0][-1]) - 1, int(col_list[1][-1]) - 1, int(col_list[2][-1]) - 1, int(
            col_list[3][-1]) - 1
        # create a search cursor to pull the info out of the config file
        inp_rows = arcpy.SearchCursor(well_file, fields='wellName; UWI; KBElev; utmE; utmN; UTMDat')

        for row in inp_rows:
            utmE = row.getValue('utmE')
            utmN = row.getValue('utmN')
            kbElev = row.getValue('KBElev')
            uwi = row.getValue('UWI')


        # after parameters are set
        with open(sur_file, 'r') as sf:
            sl = []
            # read lines in provided survey file and find only the ones with survey data
            for line in sf:
                line = line.strip().split()
                if len(line) > 0 and line[0][0].isdigit():
                    sl.append(line)

        # create feature class for points
        tpm_points = 'p_' + uwi
        arcpy.CreateFeatureclass_management(parameters[5].valueAsText, tpm_points, 'POINT', has_z='ENABLED',
                                            spatial_reference=utmdat)
        arcpy.management.AddFields(tpm_points, [['MD', 'DOUBLE', 'MD', None]])
        arcpy.management.AddFields(tpm_points, [['TVD', 'DOUBLE', 'TVD', None]])
        arcpy.management.AddFields(tpm_points, [['EAST', 'DOUBLE', 'NORTH', None]])
        arcpy.management.AddFields(tpm_points, [['NORTH', 'DOUBLE', 'EAST', None]])

        # continue on with assigning each column to the appropriate value
        fields = ['MD', 'TVD', 'EAST', 'NORTH']
        cursor = arcpy.da.InsertCursor(tpm_points, ['MD', 'TVD', 'EAST', 'NORTH', 'SHAPE@Z', 'SHAPE@XY'])
        for item in sl:
            # m, t, n, e were defined from parameter 8
            md, tvd, east, north = float(item[m]), float(item[t]), float(item[e]), float(item[n])
            surveys = [md, utmE + east, utmN + north, kbElev - tvd, (utmE + east, utmN + north)]
            cursor.insertRow(surveys)

        arcpy.PointsToLine_management(tpm_points, 'w_' + uwi)
        # delete temp point feature
        # arcpy.Delete_management(tpm_points)
        # add surveys to map
        return
