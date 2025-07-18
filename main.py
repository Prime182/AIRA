import subprocess
import sys
import os

def run_in_new_terminal(command):
    """Runs a command in a new terminal window."""
    try:
        if sys.platform == "win32":
            # For Windows, start a new command prompt and run the command
            # Using 'call' to ensure the command is executed within the new cmd instance
            subprocess.Popen(f'start cmd /k "call {command}"', shell=True)
        elif sys.platform == "darwin":
            # For macOS, open a new Terminal window
            # This is a bit more complex as it requires AppleScript
            script = f'tell app "Terminal" to do script "{command}"'
            subprocess.Popen(['osascript', '-e', script])
        else: # Linux
            # Try with a common terminal emulator
            subprocess.Popen(['x-terminal-emulator', '-e', command])
    except FileNotFoundError:
        print(f"Could not find a suitable terminal emulator for your OS ({sys.platform}).")
        print("Please run the following commands manually in separate terminal windows:")
        print(f"Backend: {backend_command}")
        print(f"Frontend: {frontend_command}")
    except Exception as e:
        print(f"An unexpected error occurred while trying to open a new terminal: {e}")
        print("Please run the following commands manually in separate terminal windows:")
        print(f"Backend: {backend_command}")
        print(f"Frontend: {frontend_command}")


if __name__ == "__main__":
    # Ensure python commands are executed by the same interpreter running the script
    python_executable = sys.executable

    # Command to run the backend server
    backend_command = f"{python_executable} mcp_server.py"
    
    # Command to run the streamlit frontend using the current Python executable
    frontend_command = f"{python_executable} -m streamlit run ui/streamlit_app.py"

    print("Starting backend server in a new terminal...")
    run_in_new_terminal(backend_command)
    
    print("Starting frontend UI in a new terminal...")
    run_in_new_terminal(frontend_command)

    print("\nApplication has been launched in new terminal windows.")
    print("You can close this window.")
