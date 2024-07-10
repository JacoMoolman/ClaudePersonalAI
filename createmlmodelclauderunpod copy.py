import pyautogui
import time
import pyperclip
import re
import paramiko
import os
from datetime import datetime

# User-defined maximum number of iterations
max_iterations = 10  # User can change this value to set the maximum number of optimization attempts

# SSH connection details
ssh_host = "194.26.196.135"
ssh_port = 16266
ssh_user = "root"

# Directory to save local scripts
local_script_dir = "generated_scripts"

# Ensure the local script directory exists
os.makedirs(local_script_dir, exist_ok=True)

# Start Text 
start_text = fr'''
ALWYS GIVE ME ALL THE CODE!!
I have a GPU avalable!!! Alwys try and make the generated code use the GPU!

If there is errors regarding packages not found please add this to the script being generated!

There is Files in /workspace/brain_tumor_dataset/yes anb /workspace/brain_tumor_dataset/no
This is images with brain tumors.The images in YES has brain tumors and the images in NO does not.

Please can you create a ml model to predict the two above given an input image.-

During training it should do the following:
The generated script should log each step in DETAIL! Do not print out anything that will create tons of output.
Only Text for logging using print() No Actual graphs!

Once the model as finished training it should do the following:
*Output the F1 score and the confustion matrix in txt format in the following format F1_SCORE:XXX
*Save the model for later inferance! The name should be descriptive and have the following with the name:
date,time,F1 score
'''

def set_clipboard(text):
    pyperclip.copy(text)

def click_at_coordinates(x, y):
    print(f"Clicking at X: {x}, Y: {y}")
    pyautogui.moveTo(x, y)
    pyautogui.click()
    time.sleep(1)

def paste_text():
    print("Pasting text")
    pyautogui.hotkey('ctrl', 'v')
    time.sleep(1)

def press_enter():
    print("Pressing Enter")
    pyautogui.press('enter')

def save_script_locally(script_content, iteration):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"script_iteration_{iteration}_{timestamp}.py"
    filepath = os.path.join(local_script_dir, filename)
    with open(filepath, "w") as file:
        file.write(script_content)
    print(f"Script saved locally as: {filepath}")
    return filepath

def run_script_on_remote_server(script_content, iteration):
    error_message = "No error occurred"
    print("Running script on remote server")
    
    # Save the script locally first
    local_script_path = save_script_locally(script_content, iteration)
    
    try:
        # Create SSH client
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        # Connect to the remote server
        client.connect(ssh_host, port=ssh_port, username=ssh_user)
        
        # Execute the script on the remote server
        stdin, stdout, stderr = client.exec_command('python3 -c "import sys; exec(sys.stdin.read())"')
        stdin.write(script_content)
        stdin.channel.shutdown_write()
        
        # Capture and print output in real-time
        output = ""
        for line in stdout:
            print(line.strip())
            output += line
        for line in stderr:
            print(line.strip())
            output += line
        
        # Check return code
        if stdout.channel.recv_exit_status() != 0:
            error_message = f"Script exited with non-zero status"
            print(error_message)
            output += error_message
        
        # Close the SSH connection
        client.close()
        
        pyperclip.copy(output)
        print("Output has been copied to the clipboard.")
        return output, error_message
    except Exception as e:
        error_message = f"An error occurred while running the script on the remote server: {e}"
        print(error_message)
        pyperclip.copy(error_message)
        print("Error message has been copied to the clipboard.")
        return "", error_message

def print_big(text):
    print("\n" + "#" * 50)
    print(text)
    print("#" * 50 + "\n")

def check_for_outcome(output):
    f1_match = re.search(r'F1_SCORE:([\d.]+)', output)
    if f1_match:
        return "YES", f1_match.group(1)
    return "NO", "0"

bestF1 = 0
f1_score = 0
bestcode = ""
best_output = ""
iteration_count = 0

print_big("FIRST RUN")
print_big("USING CLAUDE")

# Click on claude main chat to start the input
click_at_coordinates(709, 340)

# Copy Text above into clipboard
set_clipboard(start_text)

# Paste into the main claude screen
paste_text()

press_enter()

# Wait for the code to be written
time.sleep(60)

# Click the copy button at the bottom of the screen
click_at_coordinates(1843, 1002)

clipboard_text = pyperclip.paste()

output, error_message = run_script_on_remote_server(clipboard_text, iteration_count)

# Check if F1 Score is given
has_f1_score, f1_score = check_for_outcome(output)
print(f"\033[38;5;208mHas F1 score: {has_f1_score}\033[0m")  # Orange
if has_f1_score == "YES":
    print_big(f1_score)
    if float(f1_score) > float(bestF1):
        print("Past Best F1 Score:", bestF1)
        print_output = f"{f1_score} > {bestF1}"
        print_big(print_output)
        bestF1 = f1_score
        bestcode = clipboard_text
        best_output = output

print_big("END OF FIRST RUN")

# Optimization loop
while float(f1_score) < 1 and iteration_count < max_iterations:
    iteration_count += 1
    print_big(f"LOOP START (Iteration {iteration_count} of {max_iterations})")
    print("Current F1 SCORE:", f1_score)
    print("Highest F1 SCORE:", bestF1)
    print("HAS F1 SCORE:", has_f1_score)
    
    if has_f1_score == "YES":
        print("-->HAS F1 SCORE!<---")
        llm_input_pass_or_fail = f"""
        This code gave an F1 score of {f1_score}. 

        For Reference:
        The BEST F1 overall score you could manage was {bestF1}

        Here's the output of the current run:
        {output}

        Here's the output of the best run so far:
        {best_output}

        This was produced by this code:
        {bestcode}

        Please come up with a new way to try to improve the F1 score, be it via additional data processing or a new ML model approach.
        Consider the confusion matrix and other metrics provided in the output to guide your improvements.
        """
    else:
        print("-->NO F1 SCORE DETECTED!<---")
        llm_input_pass_or_fail = f"""
        THIS HAS GIVEN THE FOLLOWING OUTPUT:
        {output}

        Look at the code you have given me and the output or error, then update the code you have given me to resolve the issue.
        This has not met the output I asked for.
        """

    complied_instructions = f"""
    HERE IS THE CODE YOU HAVE GIVEN ME:
    {clipboard_text}

    {llm_input_pass_or_fail}

    Here is the background of the task:
    {start_text}
    """

    # Click on the new location of the text input
    click_at_coordinates(225, 981)

    # Copy the compiled instructions into the clipboard
    set_clipboard(complied_instructions)

    # Paste into the main claude screen
    paste_text()
    
    press_enter()

    # Wait for the code to be written
    time.sleep(60)

    # Click the copy button at the bottom of the screen
    click_at_coordinates(1843, 1002)

    clipboard_text = pyperclip.paste()

    output, error_message = run_script_on_remote_server(clipboard_text, iteration_count)

    # Check if F1 Score is given
    has_f1_score, f1_score = check_for_outcome(output)
    print(f"\033[38;5;208mHas F1 score: {has_f1_score}\033[0m")  # Orange
    if has_f1_score == "YES":
        print_big(f1_score)
        if float(f1_score) > float(bestF1):
            print("Past Best F1 Score:", bestF1)
            print_output = f"{f1_score} > {bestF1}"
            print_big(print_output)
            bestF1 = f1_score
            bestcode = clipboard_text
            best_output = output

    print_big(f"END OF LOOP (Iteration {iteration_count} of {max_iterations})")

if iteration_count >= max_iterations:
    print_big(f"Reached maximum number of iterations ({max_iterations})")
else:
    print_big("Achieved perfect F1 score of 1.0")

print_big(f"FINAL BEST F1 SCORE: {bestF1}")
print("BEST CODE:")
print(bestcode)
print("BEST OUTPUT:")
print(best_output)