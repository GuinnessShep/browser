import os
import gradio as gr
from modules import script_callbacks, shared

# Directory to store SSH keys
SSH_KEYS_DIR = os.path.expanduser("~/.ssh")

def browse_files(path='/'):
    try:
        files = os.listdir(path)
        return [{"name": f, "path": os.path.join(path, f), "is_dir": os.path.isdir(os.path.join(path, f))} for f in files]
    except Exception as e:
        return [{"name": str(e), "path": "", "is_dir": False}]

def download_file(file_path):
    try:
        with open(file_path, 'rb') as f:
            return f.read()
    except Exception as e:
        return str(e)

def upload_file(file, destination):
    try:
        with open(os.path.join(destination, file.name), 'wb') as f:
            f.write(file.read())
        return f"File {file.name} uploaded to {destination}."
    except Exception as e:
        return str(e)

def save_file(file_path, content):
    try:
        with open(file_path, 'w') as f:
            f.write(content)
        return f"File {file_path} saved."
    except Exception as e:
        return str(e)

def load_file(file_path):
    try:
        with open(file_path, 'r') as f:
            return f.read()
    except Exception as e:
        return str(e)

def on_ui_tabs():
    with gr.Blocks(elem_id="file-browser", analytics_enabled=False) as ui_component:

        def create_file_entry(file):
            with gr.Row():
                gr.Textbox(value=file["name"], label="", interactive=False)
                if file["is_dir"]:
                    gr.Button("Open", elem_id=f"open-{file['path']}").click(fn=lambda p: browse_files(p), inputs=None, outputs=files_list)
                else:
                    gr.Button("Download", elem_id=f"download-{file['path']}").click(fn=download_file, inputs=file["path"], outputs=download_output)
                    gr.Button("Edit", elem_id=f"edit-{file['path']}").click(fn=load_file, inputs=file["path"], outputs=file_content)

        with gr.Tab("File Browser"):
            with gr.Row():
                with gr.Column(scale=2):
                    current_path = gr.Textbox(label="Current Path", value="/")
                    files_list = gr.Column()
                    browse_button = gr.Button("Browse")
                    browse_button.click(fn=browse_files, inputs=current_path, outputs=files_list)
                    
                    gr.HTML("""
                    <style>
                        .gradio-container .file-entry {
                            display: flex;
                            align-items: center;
                            justify-content: space-between;
                        }
                    </style>
                    """)

                with gr.Column(scale=1):
                    download_path = gr.Textbox(label="Download File Path")
                    download_button = gr.Button("Download")
                    download_output = gr.File(label="Downloaded File")
                    download_button.click(fn=download_file, inputs=download_path, outputs=download_output)

                    upload_destination = gr.Textbox(label="Upload Destination Path")
                    upload_file_input = gr.File(label="Upload File")
                    upload_button = gr.Button("Upload")
                    upload_output = gr.Textbox(label="Upload Status", interactive=False)
                    upload_button.click(fn=upload_file, inputs=[upload_file_input, upload_destination], outputs=upload_output)

                    edit_file_path = gr.Textbox(label="File Path to Edit")
                    file_content = gr.Code(label="File Content", lines=20)
                    save_button = gr.Button("Save")
                    save_output = gr.Textbox(label="Save Status", interactive=False)
                    save_button.click(fn=save_file, inputs=[edit_file_path, file_content], outputs=save_output)

                    edit_button = gr.Button("Load File for Editing")
                    edit_button.click(fn=load_file, inputs=edit_file_path, outputs=file_content)

    return [(ui_component, "File Browser", "file-browser")]

def on_ui_settings():
    settings_section = ('file-browser', "File Browser")
    options = {
        "file_browser_default_path": shared.OptionInfo("/", "Default path for the file browser", gr.Textbox).needs_reload_ui(),
    }
    for name, opt in options.items():
        opt.section = settings_section
        shared.opts.add_option(name, opt)

script_callbacks.on_ui_tabs(on_ui_tabs)
script_callbacks.on_ui_settings(on_ui_settings)
