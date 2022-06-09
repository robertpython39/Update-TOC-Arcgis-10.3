import arcpy
import os


class Toolbox(object):
    def __init__(self):
        """Define the toolbox (the name of the toolbox is the name of the
        .pyt file)."""
        self.label = "Blom Toolbox"
        self.alias = "TBlom Toolbox"

        # List of tool classes associated with this toolbox
        self.tools = [Tool]


class Tool(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "CreateGroups_SUTDS"
        self.description = "Tool for loading or merge GDB's in Arcmap"
        self.canRunInBackground = False
        self.ROOT_PATH = r"C:\Data\ESRI"
    
        
    def getParameterInfo(self):
        """Define parameter definitions"""
        #Define parameter definitions

        # First parameter
        param0 = arcpy.Parameter(
            displayName="Proiect",
            name="prjName",
            datatype="GPString",
            parameterType="Required",
            direction="Input")


        prjs =  [ d for d in os.listdir(r"c:\data\esri")]
        param0.filter.list = prjs

        param1 = arcpy.Parameter(
            displayName="User",
            name="user",
            datatype="GPString",
            parameterType="Required",
            direction="Input")
        param1.filter.list = []
       
        param2 = arcpy.Parameter(
            displayName="Area",
            name="area",
            datatype="GPString",
            parameterType="Required",
            direction="Input")
        param2.filter.list = []


        param3 = arcpy.Parameter(
            displayName="Grad",
            name="grad",
            datatype="GPString",
            parameterType="Required",
            direction="Input")
        param3.filter.list = []

        param4 = arcpy.Parameter(
            displayName="Actiune",
            name="actiune",
            datatype="GPString",
            parameterType="Required",
            direction="Input")
        param4.filter.list = ['Group','Merge','Group by OCS']
        
       
        param5 = arcpy.Parameter(
            displayName='GDBS',
            name='selectedGdbs',
            datatype='GPString',
            parameterType='Required',
            direction='Input',
            multiValue=True)
        param5.filter.type='ValueList'
        
        params = [param0,param1,param2,param3,param4, param5]
        return params

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        if parameters[0].altered:
            p = "c:\\data\\esri\\"+parameters[0].value
            parameters[1].filter.list = [ d for d in os.listdir(p)]
        if(parameters[1].altered):
            p = "c:\\data\\esri\\"+parameters[0].value+"\\"+parameters[1].value+"\\Projects"
            parameters[2].filter.list=[ d for d in os.listdir(p)]
        if(parameters[2].altered):
            p = "c:\\data\\esri\\"+parameters[0].value+"\\"+parameters[1].value+"\\Projects\\"+parameters[2].value
            parameters[3].filter.list=[ d for d in os.listdir(p)]
        if(parameters[3].altered):
            p = "c:\\data\\esri\\"+parameters[0].value+"\\"+parameters[1].value+"\\Projects\\"+parameters[2].value + "\\" + parameters[3].value
            gdbs = [f for f in os.listdir(p) if f.endswith(".gdb")]    
            vals = []
            for i in range(len(gdbs)):
                vals.append(gdbs[i])
            parameters[5].filter.list = vals
        return
        
    def copy_gdb(self, gdb_inPath, gdb_outPath):
        arcpy.env.overwriteOutput = True
        arcpy.Copy_management(gdb_inPath, gdb_outPath)
    
    def merge_gdbs(self, gdb1, gdb2):
        arcpy.env.workspace = gdb1
        fc_list1 = arcpy.ListFeatureClasses(feature_dataset='ThematicData')
        d1 = {}
        for fc in fc_list1:
            i = 0
            with arcpy.da.SearchCursor(fc,["SHAPE"]) as cursor:
                for elem in cursor:
                    i = 1
                    break
            if i == 1:
                d1[fc] = ""
    
        arcpy.env.workspace = gdb2
        fc_list2 = arcpy.ListFeatureClasses(feature_dataset='ThematicData')
        d2 = {}
        for fc in fc_list2:
            i = 0
            with arcpy.da.SearchCursor(fc,["SHAPE"]) as cursor:
                for elem in cursor:
                    i = 1
                    break
            if i == 1:
                d2[fc] = ""
        print "Feature populat in gdb1: " + str(d1)
        print "Feature populat in gdb1: " + str(d2)
        for key in d2:
            cale1 = os.path.join(gdb1, "ThematicData", key)
            cale2 = os.path.join(gdb2, "ThematicData", key)
            temp = os.path.join(gdb1,'ThematicData', "temp")
    
            if key in d1:
                print "Aici se face merge-ul " + key
                arcpy.Merge_management([cale1, cale2], temp)
                cale3 = temp
            else:
                print "Aici se face copierea " + key
                cale3 = cale2
            rows1 = arcpy.InsertCursor(cale1)
            rows2 = arcpy.SearchCursor(cale3)
            for row in rows2:
                rows1.insertRow(row)
            del row
            del rows1
            del rows2
            if cale3 == temp:
                arcpy.Delete_management(temp)

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        prj = parameters[0].value
        user = parameters[1].value
        aria = parameters[2].value
        grad = parameters[3].value
        actiune = parameters[4].value
        gdbs = parameters[5].value
        selected_gdbs = []
        for i in range(gdbs.rowCount):
            if gdbs.getTrueValue (i, 0):
                selected_gdbs.append(gdbs.getRow(i).replace("'",""))
        arcpy.AddMessage(dir(gdbs))
        arcpy.AddMessage(selected_gdbs)
        
        if(actiune=='Group'):
            self.grupeaza(prj,user,aria,grad, selected_gdbs, messages)
        elif(actiune=='Merge'):
           self.mergefeatures(prj,user,aria,grad, selected_gdbs, messages)
        elif(actiune=='Group by OCS'):
           self.grupeazaDupaOcs(prj,user,aria,grad, selected_gdbs, messages)
        

        return
    
    def citire_fisier(self, cale):
        with open(cale, "r") as f:
            d = {}
            for line in f:
                line = line.strip().upper()
                arr = line.split(",")
                d[arr[0]] = {"name": arr[1], "category": arr[2]}
        return d
    
    def grupeaza(self,prj,user,aria,grad, selected_gdbs, messages):
        tbxPath = os.path.dirname(__file__)
        dict_categories = self.citire_fisier(os.path.join(tbxPath, "grupuri_SUTDS.txt"))
        #print(dict_categories)
        grpPath = os.path.join(tbxPath, "C.lyr")
        
        mxd = arcpy.mapping.MapDocument("CURRENT")
        df = arcpy.mapping.ListDataFrames(mxd)[0]
        lyrNames = [lyr.name for lyr in arcpy.mapping.ListLayers(mxd, "", df)]
        arcpy.AddMessage("Deleting layers from MXD...")
        
        for lyr in arcpy.mapping.ListLayers(mxd, "", df):
            arcpy.mapping.RemoveLayer(df, lyr)
        arcpy.RefreshActiveView()
        arcpy.RefreshTOC()
        
        data_path = os.path.join(self.ROOT_PATH, prj, user, "Projects", aria, grad)
        
        for gdb in selected_gdbs:
            dicCreatedGroups={}
            gdbpath = os.path.join(data_path, gdb)
            arcpy.AddMessage(gdbpath)
            #creare grup corespunzator bazei gdb
            
            arcpy.env.workspace = gdbpath
            grpLyrGdb = arcpy.mapping.Layer(grpPath)
            grpLyrGdb.name = gdb
            grpLyrGdb.visible = False
            arcpy.AddMessage("Creating Groups " + gdb)
            arcpy.mapping.AddLayer(df,grpLyrGdb)
            grpLyrGdb = arcpy.mapping.ListLayers(mxd, gdb, df)[0]
            arcpy.AddMessage(grpLyrGdb)
            feature_codes_gdb = []
            for fc in arcpy.ListFeatureClasses(feature_dataset='ThematicData'):
                i = 0
                fc_path = os.path.join(arcpy.env.workspace, 'ThematicData', fc)
                #fc_count = arcpy.GetCount_management(fc_path)
                #if fc_count > 0:
                with arcpy.da.SearchCursor(fc_path, ["SHAPE"]) as cursor:
                    for row in cursor:
                        i += 1
                        break
                if i == 0:
                    continue
                else:
                    feature_codes_gdb.append(fc)
                     
            
            #arcpy.AddMessage('Create group layers')
            for fc in feature_codes_gdb:
                if(fc in dict_categories):
                    fcGroupName = "NONE"
                    try:
                        fcName = dict_categories[fc]["name"]
                        fcGroupName = dict_categories[fc]["category"]
                        if(not dicCreatedGroups.has_key(fcGroupName)):
                            dicCreatedGroups[fcGroupName] = []
                            grpLyr = arcpy.mapping.Layer(grpPath)
                            grpLyr.name = fcGroupName
                            grpLyr.visible = False
                            arcpy.AddMessage("Create Group " + fcGroupName)
                            arcpy.mapping.AddLayerToGroup(df,grpLyrGdb,grpLyr)

                        dicCreatedGroups[fcGroupName].append(fcName)
                    except Exception,ex:
                        arcpy.AddMessage("fc={} grp={} err={}".format(fcName,fcGroupName,str(ex)))

            arcpy.AddMessage('Move layers to corresponding groups')
            for fc in feature_codes_gdb:
                if (fc in dict_categories):
                    print(fc)
                    try:
                        fcName = dict_categories[fc]["name"]
                        fcGroupName = dict_categories[fc]["category"]
                        #arcpy.AddMessage("\tMove layer {} to {}".format(fcName,fcGroupName))
                        fc_path = os.path.join(arcpy.env.workspace, 'ThematicData', fc)
                        layer = arcpy.mapping.Layer(fc_path)
                        layer.name = fcName
                        layer.visible = False
                        for lyr in arcpy.mapping.ListLayers(grpLyrGdb, "", df):
                            if (lyr.name == fcGroupName):
                                arcpy.mapping.AddLayerToGroup(df, lyr, layer)
                                break


                    except Exception,ex:
                        arcpy.AddMessage("Eroare {}".format(str(ex)))
        for lyr in arcpy.mapping.ListLayers(mxd, "", df):
            lyr.visible = True
        arcpy.RefreshActiveView()
        arcpy.RefreshTOC()

    def mergefeatures(self,prj,user,aria,grad, selected_gdbs, messages):
    
        merged_gdb_path = os.path.join(self.ROOT_PATH,prj, user, "Projects", aria, grad,"merged_gdbs.gdb")
        crt_gdb_path = os.path.join(self.ROOT_PATH,prj, user, "Projects", aria, grad,selected_gdbs[0])
        #arcpy.AddMessage(crt_gdb_path)
        #arcpy.AddMessage(merged_gdb_path)
        arcpy.AddMessage("1st GDB has been created...")
        self.copy_gdb(crt_gdb_path, merged_gdb_path)
        for i in range(1, len(selected_gdbs)):
            crt_gdb_path = os.path.join(self.ROOT_PATH, prj, user, "Projects", aria, grad,selected_gdbs[i])
            arcpy.AddMessage("Merge cu {}".format(selected_gdbs[i]))
            self.merge_gdbs(merged_gdb_path, crt_gdb_path)
        self.grupeaza(prj,user,aria,grad, ['merged_gdbs.gdb'], messages)
        
        
    def grupeazaDupaOcs(self,prj,user,aria,grad, selected_gdbs, messages):
        #C:\ProiecteBlom\groupsOCS.txt
        tbxPath = os.path.dirname(__file__)
        dict_categories = self.citire_fisier(os.path.join(tbxPath, "groupsOCS_SUTDS.txt"))
        arcpy.AddMessage(dict_categories)
        grpPath = os.path.join(tbxPath, "C.lyr")
        
        mxd = arcpy.mapping.MapDocument("CURRENT")
        df = arcpy.mapping.ListDataFrames(mxd)[0]
        lyrNames = [lyr.name for lyr in arcpy.mapping.ListLayers(mxd, "", df)]
        arcpy.AddMessage("Deleting lyr from MXD...")
        
        for lyr in arcpy.mapping.ListLayers(mxd, "", df):
            arcpy.mapping.RemoveLayer(df, lyr)
        arcpy.RefreshActiveView()
        arcpy.RefreshTOC()
        
        data_path = os.path.join(self.ROOT_PATH, prj, user, "Projects", aria, grad)
        
        for gdb in selected_gdbs:
            dicCreatedGroups={}
            gdbpath = os.path.join(data_path, gdb)
            arcpy.AddMessage(gdbpath)
            #creare grup corespunzator bazei gdb
            
            arcpy.env.workspace = gdbpath
            grpLyrGdb = arcpy.mapping.Layer(grpPath)
            grpLyrGdb.name = gdb
            grpLyrGdb.visible = False
            arcpy.AddMessage("Create group " + gdb)
            arcpy.mapping.AddLayer(df,grpLyrGdb)
            grpLyrGdb = arcpy.mapping.ListLayers(mxd, gdb, df)[0]
            arcpy.AddMessage(grpLyrGdb)
            feature_codes_gdb = []
            for fc in arcpy.ListFeatureClasses(feature_dataset='ThematicData'):
                i = 0
                fc_path = os.path.join(arcpy.env.workspace, 'ThematicData', fc)
                #fc_count = arcpy.GetCount_management(fc_path)
                #if fc_count > 0:
                with arcpy.da.SearchCursor(fc_path, ["SHAPE"]) as cursor:
                    for row in cursor:
                        i += 1
                        break
                if i == 0:
                    continue
                else:
                    feature_codes_gdb.append(fc)
                     
            
            arcpy.AddMessage(feature_codes_gdb)
            for fc in feature_codes_gdb:
                if(fc in dict_categories):
                    fcGroupName = "NONE"
                    try:
                        fcName = dict_categories[fc]["name"]
                        fcGroupName = dict_categories[fc]["category"]
                        if(not dicCreatedGroups.has_key(fcGroupName)):
                            # arcpy.AddMessage('\tCreate %s'%(fcGroupName))
                            dicCreatedGroups[fcGroupName] = []
                            grpLyr = arcpy.mapping.Layer(grpPath)
                            grpLyr.name = fcGroupName
                            grpLyr.visible = False
                            arcpy.AddMessage("Create group " + fcGroupName)
                            arcpy.mapping.AddLayerToGroup(df,grpLyrGdb,grpLyr)

                        dicCreatedGroups[fcGroupName].append(fcName)
                    except Exception,ex:
                        arcpy.AddMessage("fc={} grp={} err={}".format(fcName,fcGroupName,str(ex)))

            arcpy.AddMessage('Move layers to corresponding groups')
            for fc in feature_codes_gdb:
                if (fc in dict_categories):
                    print(fc)
                    try:
                        fcName = dict_categories[fc]["name"]
                        fcGroupName = dict_categories[fc]["category"]
                        #arcpy.AddMessage("\tMove layer {} to {}".format(fcName,fcGroupName))
                        fc_path = os.path.join(arcpy.env.workspace, 'ThematicData', fc)
                        layer = arcpy.mapping.Layer(fc_path)
                        layer.name = fcName
                        layer.visible = False
                        for lyr in arcpy.mapping.ListLayers(grpLyrGdb, "", df):
                            if (lyr.name == fcGroupName):
                                arcpy.mapping.AddLayerToGroup(df, lyr, layer)
                                break


                    except Exception,ex:
                        arcpy.AddMessage("Eroare {}".format(str(ex)))
        for lyr in arcpy.mapping.ListLayers(mxd, "", df):
            lyr.visible = True
        arcpy.RefreshActiveView()
        arcpy.RefreshTOC() 