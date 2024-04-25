import contextlib
import gradio as gr
import modules.scripts as scripts
from modules import script_callbacks, shared
import os


script_dir = scripts.basedir()

class ClipboardScript(scripts.Script):
    def __init__(self) -> None:
        super().__init__()
    
    def title(self):
        return "Clipboard example"
    
    clipboard_path = shared.opts.data.get("clipboard_path", os.path.join(script_dir, "scripts"))

    def ui(self, is_img2img):
        return ClipboardScript.clipboard_path

    def show(self, is_img2img):
        # You don't have to go select it from "script"
        return scripts.AlwaysVisible

    def ui(self, is_img2img):
        with gr.Group():
            with gr.Accordion("Clipboard", open=False):
                gr.Markdown(value="You can save and load text here. You can find and change the store location from Options/Clipboard")
                with gr.Row():
                    clipboard = gr.Textbox(label="Saved text", lines=5)
                with gr.Row():
                    load_text = gr.Button(value='Load', variant='primary')
                    save_text = gr.Button(value='Save', variant='primary')
                with gr.Row():
                    load_backUp = gr.Button(value='Load Backup')
                    save_backUp = gr.Button(value='Save Backup')
        
        with contextlib.suppress(AttributeError): # Ignore the error if the attribute is not present
            if is_img2img:
                save_text.click(fn=saveText, inputs=[clipboard], outputs=[clipboard])
                save_backUp.click(fn=saveBackUp, inputs=[clipboard], outputs=[clipboard])
                load_text.click(fn=loadText, inputs=[clipboard], outputs=[clipboard])
                load_backUp.click(fn=loadBackUp, inputs=[clipboard], outputs=[clipboard])
            else:
                save_text.click(fn=saveText, inputs=[clipboard], outputs=[clipboard])
                save_backUp.click(fn=saveBackUp, inputs=[clipboard], outputs=[clipboard])
                load_text.click(fn=loadText, inputs=[clipboard], outputs=[clipboard])
                load_backUp.click(fn=loadBackUp, inputs=[clipboard], outputs=[clipboard])

        return [clipboard, load_text, save_text, load_backUp, save_backUp]

    
    @staticmethod
    def on_after_component(component, **_kwargs):
        elem_id = getattr(component, "elem_id", None)
             
        if elem_id == "txt2img_generate":
            ClipboardScript.txt2img_submit_button = component
            return
            
        if elem_id == "img2img_generate":
            ClipboardScript.img2img_submit_button = component
            return   

def on_ui_settings():
    section = ("cliboard", "Clipboard")
    shared.opts.add_option(
        "clipboard_path",
        shared.OptionInfo(
            os.path.join(script_dir, "scripts"),
            "Change path to save clipboard and backup (requires restart)",
            gr.Textbox,
            section=section,
        ),
    )

def saveText(new_text):
    with open(ClipboardScript.clipboard_path + '/newText.txt', 'w') as f:
        f.write(new_text)
    
    new_text=new_text
    return new_text

def loadText(new_text):
    file = open(ClipboardScript.clipboard_path + "/newText.txt", "r")
    new_text = file.read()

    return new_text

def saveBackUp(new_text):
    with open(ClipboardScript.clipboard_path + '/newBackUp.txt', 'w') as f:
        f.write(new_text)
    
    new_text=new_text
    return new_text

def loadBackUp(new_text):
    file = open(ClipboardScript.clipboard_path + "/newBackUp.txt", "r")
    new_text = file.read()

    return new_text

script_callbacks.on_ui_settings(on_ui_settings)
script_callbacks.on_after_component(ClipboardScript.on_after_component)