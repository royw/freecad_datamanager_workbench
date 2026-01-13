import FreeCAD as App

def createVarSet_VarSet(doc_: App.Document) -> App.Object:
    """
    Create a VarSet object with the following properties:

    """

    VarSet = doc_.addObject('App::VarSet', 'VarSet')
    doc_.getObject('VarSet').Label = 'VarSet'
    VarSet.addProperty('App::PropertyDistance', 'BottomInternalZ', 'Base')
    VarSet.setExpression('BottomInternalZ', 'ModuloZ - TopInternalZ')
    VarSet.addProperty('App::PropertyDistance', 'BottomThickness', 'Dimensions')
    VarSet.BottomThickness = '4.0 mm'
    VarSet.addProperty('App::PropertyDistance', 'Clearance', 'Dimensions')
    VarSet.Clearance = '0.2 mm'
    VarSet.addProperty('App::PropertyDistance', 'ExternalCornerFillets', 'Base')
    VarSet.ExternalCornerFillets = '4.0 mm'
    VarSet.addProperty('App::PropertyDistance', 'Gasket', 'Dimensions')
    VarSet.Gasket = '2.5 mm'
    VarSet.addProperty('App::PropertyBool', 'HasHandle', 'Options')
    VarSet.HasHandle = True
    VarSet.addProperty('App::PropertyDistance', 'HingePin', 'Dimensions')
    VarSet.HingePin = '3.0 mm'
    VarSet.addProperty('App::PropertyDistance', 'HingeRadius', 'Base')
    VarSet.HingeRadius = '4.0 mm'
    VarSet.addProperty('App::PropertyDistance', 'InsertDiameter', 'Dimensions')
    VarSet.InsertDiameter = '4.2 mm'
    VarSet.addProperty('App::PropertyDistance', 'InternalCornerFillets', 'Base')
    VarSet.InternalCornerFillets = '1.0 mm'
    VarSet.addProperty('App::PropertyDistance', 'InternalX', 'Base')
    VarSet.setExpression('InternalX', 'ModuloX * xUnits')
    VarSet.addProperty('App::PropertyDistance', 'InternalY', 'Base')
    VarSet.setExpression('InternalY', 'ModuloY * yUnits')
    VarSet.addProperty('App::PropertyDistance', 'LatchHookLever', 'Base')
    VarSet.LatchHookLever = '10.0 mm'
    VarSet.addProperty('App::PropertyDistance', 'LatchRadius', 'Base')
    VarSet.LatchRadius = '1.5 mm'
    VarSet.addProperty('App::PropertyAngle', 'LipAngle', 'Base')
    VarSet.LipAngle = '35.0 deg'
    VarSet.addProperty('App::PropertyDistance', 'ModuloX', 'Dimensions')
    VarSet.ModuloX = '40.0 mm'
    VarSet.addProperty('App::PropertyDistance', 'ModuloY', 'Dimensions')
    VarSet.ModuloY = '45.0 mm'
    VarSet.addProperty('App::PropertyDistance', 'ModuloZ', 'Dimensions')
    VarSet.ModuloZ = '50.0 mm'
    VarSet.addProperty('App::PropertyDistance', 'OverallX', 'OverallSize')
    VarSet.setExpression('OverallX', 'InternalX + WallThickness * 4')
    VarSet.addProperty('App::PropertyDistance', 'OverallY', 'OverallSize')
    VarSet.setExpression('OverallY', 'InternalY + (WallThickness + HingeRadius) * 2 + 14 mm')
    VarSet.addProperty('App::PropertyDistance', 'Ribs', 'Base')
    VarSet.Ribs = '5.0 mm'
    VarSet.addProperty('App::PropertyDistance', 'TopInternalZ', 'Base')
    VarSet.TopInternalZ = '10.0 mm'
    VarSet.addProperty('App::PropertyDistance', 'TopThickness', 'Dimensions')
    VarSet.TopThickness = '3.5 mm'
    VarSet.addProperty('App::PropertyBool', 'UseScrews', 'Options')
    VarSet.UseScrews = True
    VarSet.addProperty('App::PropertyDistance', 'WallThickness', 'Dimensions')
    VarSet.WallThickness = '3.0 mm'
    VarSet.addProperty('App::PropertyInteger', 'xUnits', 'Options')
    VarSet.xUnits = 6
    VarSet.addProperty('App::PropertyInteger', 'yUnits', 'Options')
    VarSet.yUnits = 5
    doc_.recompute()
    return VarSet

doc = App.ActiveDocument
varset = createVarSet_VarSet(doc)
