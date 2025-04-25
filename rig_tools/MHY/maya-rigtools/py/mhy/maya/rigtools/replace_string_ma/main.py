import os
import pymel.core as pm

def replace_string_in_files(source_folder, output_folder, source_string, target_string):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    for file_name in os.listdir(source_folder):
        if file_name.endswith('.ma'):
            source_file_path = os.path.join(source_folder, file_name)
            output_file_path = os.path.join(output_folder, file_name)
            
            with open(source_file_path, 'r', encoding='utf-8') as file:
                file_contents = file.read()
            
            modified_contents = file_contents.replace(source_string, target_string)
            
            with open(output_file_path, 'w', encoding='utf-8') as file:
                file.write(modified_contents)
            
            print(f"Processed {file_name}")

def show_ui():
    window_id = 'replaceStringUI'
    window_width = 600
    
    if pm.window(window_id, exists=True):
        pm.deleteUI(window_id)
    
    pm.window(window_id, title="Replace String in Maya .ma Files", widthHeight=(window_width, 200), sizeable=False)
    pm.columnLayout(adjustableColumn=True)
    
    # Load existing values or set defaults
    source_string_default = pm.optionVar.get('replaceStringSource', '')
    target_string_default = pm.optionVar.get('replaceStringTarget', '')
    source_folder_default = pm.optionVar.get('replaceStringSourceFolder', '')
    output_folder_default = pm.optionVar.get('replaceStringOutputFolder', '')
    
    source_string_field = pm.textFieldGrp(label='Source String:', placeholderText='Enter source string here...', columnWidth=[(1, 100), (2, window_width - 110)], text=source_string_default)
    target_string_field = pm.textFieldGrp(label='Target String:', placeholderText='Enter target string here...', columnWidth=[(1, 100), (2, window_width - 110)], text=target_string_default)
    
    source_folder_field = pm.textFieldButtonGrp(label='Source Folder:', buttonLabel='+', columnWidth=[(1, 100), (2, window_width - 160)], text=source_folder_default, buttonCommand=lambda: on_folder_select_clicked(source_folder_field))
    output_folder_field = pm.textFieldButtonGrp(label='Output Folder:', buttonLabel='+', columnWidth=[(1, 100), (2, window_width - 160)], text=output_folder_default, buttonCommand=lambda: on_folder_select_clicked(output_folder_field))
    
    pm.button(label='Run', command=lambda x: on_run_clicked(source_string_field, target_string_field, source_folder_field, output_folder_field))
    pm.showWindow()

def on_folder_select_clicked(text_field, caption):
    folder_path = pm.textFieldButtonGrp(text_field, query=True, text=True)
    
    # If the folder path is empty, prompt the user to select a folder
    if not folder_path:
        folder_path = pm.fileDialog2(fileMode=3, dialogStyle=1, caption=caption)
        if folder_path:
            pm.textFieldButtonGrp(text_field, edit=True, text=folder_path[0])
            if "Source" in pm.textFieldButtonGrp(text_field, query=True, label=True):
                pm.optionVar['replaceStringSourceFolder'] = folder_path[0]
            else:
                pm.optionVar['replaceStringOutputFolder'] = folder_path[0]

def on_run_clicked(source_string_field, target_string_field, source_folder_field, output_folder_field):
    source_string = pm.textFieldGrp(source_string_field, query=True, text=True).replace("\\", "/")
    target_string = pm.textFieldGrp(target_string_field, query=True, text=True).replace("\\", "/")
    source_folder = pm.textFieldButtonGrp(source_folder_field, query=True, text=True)
    output_folder = pm.textFieldButtonGrp(output_folder_field, query=True, text=True)
    
    # If either folder path is empty, prompt the user to select a folder
    if not source_folder:
        on_folder_select_clicked(source_folder_field, "Select Source Folder")
        source_folder = pm.textFieldButtonGrp(source_folder_field, query=True, text=True)
    if not output_folder:
        on_folder_select_clicked(output_folder_field, "Select Output Folder")
        output_folder = pm.textFieldButtonGrp(output_folder_field, query=True, text=True)
    
    # Save the strings and folder paths for future use
    pm.optionVar['replaceStringSource'] = source_string
    pm.optionVar['replaceStringTarget'] = target_string
    
    replace_string_in_files(source_folder, output_folder, source_string, target_string)

show_ui()
