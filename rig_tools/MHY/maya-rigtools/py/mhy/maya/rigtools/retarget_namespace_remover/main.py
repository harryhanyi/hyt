import maya.cmds as cmds
import json

def createUI():
    if cmds.window("Retarget Namespace Remover", exists=True):
        cmds.deleteUI("Retarget Namespace Remover", window=True)

    window = cmds.window("Retarget Namespace Remover", title="Retarget Namespace Remover", sizeable=False, resizeToFitChildren=True)
    cmds.columnLayout(adjustableColumn=True)
    
    sourceStringDefault = cmds.optionVar(q="retargetSource") if cmds.optionVar(exists="retargetSource") else ""
    targetStringDefault = cmds.optionVar(q="retargetTarget") if cmds.optionVar(exists="retargetTarget") else ""
    outputFolderDefault = cmds.optionVar(q="retargetOutputFolder") if cmds.optionVar(exists="retargetOutputFolder") else ""
    targetFile01Default = cmds.optionVar(q="retargetTargetFile01") if cmds.optionVar(exists="retargetTargetFile01") else ""
    targetFile02Default = cmds.optionVar(q="retargetTargetFile02") if cmds.optionVar(exists="retargetTargetFile02") else ""

    cmds.textFieldGrp('sourceStringTFG', label='Source String:', placeholderText='Enter source string here', text=sourceStringDefault)
    cmds.textFieldGrp('targetStringTFG', label='Target String:', placeholderText='Enter target string here', text=targetStringDefault)
    cmds.textFieldButtonGrp('outputFolderTBG', label='Output Folder:', buttonLabel='+', placeholderText='Select output folder', text=outputFolderDefault, buttonCommand=selectOutputFolder)
    cmds.textFieldButtonGrp('targetFile01TBG', label='Target File 01:', buttonLabel='+', placeholderText='Select first target file', text=targetFile01Default, buttonCommand=selectTargetFile01)
    cmds.textFieldButtonGrp('targetFile02TBG', label='Target File 02:', buttonLabel='+', placeholderText='Select second target file', text=targetFile02Default, buttonCommand=selectTargetFile02)
    
    cmds.button(label='Run', command=runReplacer)

    cmds.showWindow(window)

def selectOutputFolder(*args):
    folderPath = cmds.fileDialog2(fileMode=3, dialogStyle=2)
    if folderPath:
        cmds.textFieldButtonGrp("outputFolderTBG", edit=True, text=folderPath[0])

def selectTargetFile01(*args):
    filePath = cmds.fileDialog2(fileMode=1, dialogStyle=2)
    if filePath:
        cmds.textFieldButtonGrp("targetFile01TBG", edit=True, text=filePath[0])

def selectTargetFile02(*args):
    filePath = cmds.fileDialog2(fileMode=1, dialogStyle=2)
    if filePath:
        cmds.textFieldButtonGrp("targetFile02TBG", edit=True, text=filePath[0])

def runReplacer(*args):
    sourceString = cmds.textFieldGrp('sourceStringTFG', query=True, text=True)
    targetString = cmds.textFieldGrp('targetStringTFG', query=True, text=True)
    outputFolder = cmds.textFieldButtonGrp('outputFolderTBG', query=True, text=True)
    targetFile01 = cmds.textFieldButtonGrp('targetFile01TBG', query=True, text=True)
    targetFile02 = cmds.textFieldButtonGrp('targetFile02TBG', query=True, text=True)
    
    if not outputFolder:
        cmds.warning("Output folder is not specified.")
        return
    targetFiles = [targetFile01, targetFile02]

    cmds.optionVar(sv=("retargetSource", sourceString))
    cmds.optionVar(sv=("retargetTarget", targetString))
    cmds.optionVar(sv=("retargetOutputFolder", outputFolder))
    cmds.optionVar(sv=("retargetTargetFile01", targetFile01))
    cmds.optionVar(sv=("retargetTargetFile02", targetFile02))

    for filePath in targetFiles:
        if filePath:
            replaceStringInFile(filePath, sourceString, targetString, outputFolder)

def replaceStringInFile(filePath, sourceString, targetString, outputFolder):
    try:
        with open(filePath, 'r') as file:
            fileContent = file.read()
        
        updatedContent = fileContent.replace(sourceString, targetString)
        baseFileName = os.path.basename(filePath)
        newFilePath = os.path.join(outputFolder, baseFileName)

        if updatedContent != fileContent and outputFolder:
            with open(newFilePath, 'w') as file:
                file.write(updatedContent)
            print(f"Updated file saved to: {newFilePath}")
        else:
            print(f"No changes made to file: {filePath}")
    except Exception as e:
        cmds.warning(f"Error processing file {filePath}: {str(e)}")

createUI()
