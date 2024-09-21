import os
from smb.SMBConnection import SMBConnection
from colorama import init, Fore, Style

# Initialize Colorama
init()

def print_header():
    print(Fore.CYAN + "=========================================" + Style.RESET_ALL)
    print(Fore.GREEN + "            SMB Enumeration" + Style.RESET_ALL)
    print(Fore.CYAN + "=========================================" + Style.RESET_ALL)
    print(Fore.RED + "!!!Please use this tool responsibly and legally!!!" + Style.RESET_ALL)


def connect_to_smb(ip, username, password):
    try:
        conn = SMBConnection(username, password, "client_name", "server_name", use_ntlm_v2=True)
        conn.connect(ip, 139)  # You can also try port 445
        return conn
    except Exception as e:
        print(Fore.RED + f"Failed to connect to SMB: {str(e)}" + Style.RESET_ALL)
        return None


def list_shares(smb_connection):
    try:
        shares = smb_connection.listShares()
        print(Fore.BLUE + f"Shares found: {len(shares)}" + Style.RESET_ALL)
        return [
            {'name': share.name, 'permissions': 'Read/Write' if getattr(share, 'isWritable', False) else 'Read Only'}
            for share in shares]
    except Exception as e:
        print(Fore.RED + f"Error listing shares: {str(e)}" + Style.RESET_ALL)
        return []


def list_share_contents(smb_connection, share_name, path):
    try:
        return smb_connection.listPath(share_name, path)
    except Exception as e:
        print(Fore.RED + f"Error listing contents of share '{share_name}' at path '{path}': {str(e)}" + Style.RESET_ALL)
        return []


def read_file_from_share(smb_connection, share_name, file_path):
    try:
        with open('temp_file', 'wb') as file:
            smb_connection.retrieveFile(share_name, file_path, file)

        with open('temp_file', 'r') as file:
            content = file.read()
        os.remove('temp_file')  # Clean up temp file
        return content
    except Exception as e:
        print(Fore.RED + f"Error reading file '{file_path}' from '{share_name}': {str(e)}" + Style.RESET_ALL)
        return None


def upload_file_to_share(smb_connection, share_name, local_file_path, remote_file_name):
    if not os.path.isfile(local_file_path):
        print(Fore.RED + f"Local file '{local_file_path}' does not exist." + Style.RESET_ALL)
        return

    try:
        with open(local_file_path, 'rb') as file:
            smb_connection.storeFile(share_name, remote_file_name, file)
        print(Fore.GREEN + f"Successfully uploaded '{local_file_path}' to '{remote_file_name}' in '{share_name}'." + Style.RESET_ALL)
    except Exception as e:
        print(Fore.RED + f"Error uploading file '{local_file_path}' to '{remote_file_name}': {str(e)}" + Style.RESET_ALL)


def main():
    print_header()

    ip = input(Fore.CYAN + "Enter the target IP: " + Style.RESET_ALL)
    auth_choice = input(Fore.CYAN + "Do you want to (1) Connect with credentials or (2) Brute Force? (1/2): " + Style.RESET_ALL)

    if auth_choice == '1':
        username = input(Fore.CYAN + "Enter your SMB username: " + Style.RESET_ALL)
        password = input(Fore.CYAN + "Enter your SMB password: " + Style.RESET_ALL)
        smb_connection = connect_to_smb(ip, username, password)
    else:
        print(Fore.RED + "Brute Force option not implemented." + Style.RESET_ALL)
        return

    if not smb_connection:
        return

    print(Fore.CYAN + "Enumerating SMB shares..." + Style.RESET_ALL)
    shares = list_shares(smb_connection)
    if not shares:
        print(Fore.RED + "No shares found. Exiting." + Style.RESET_ALL)
        return

    for share in shares:
        print(Fore.YELLOW + f" - {share['name']} (Permissions: {share['permissions']})" + Style.RESET_ALL)

    share_name = input(Fore.CYAN + "Enter the share name to explore: " + Style.RESET_ALL)
    current_path = '/'

    while True:
        contents = list_share_contents(smb_connection, share_name, current_path)
        if contents is None:
            break

        print(Fore.CYAN + f"\nContents of '{current_path}' in '{share_name}':" + Style.RESET_ALL)
        for item in contents:
            print(Fore.YELLOW + f" - {item.filename} (Directory: {item.isDirectory})" + Style.RESET_ALL)

        command = input(
            Fore.CYAN + "Enter a command (cd <directory>, cat <file>, upload <local_file_path> <remote_file_name>, exit): " + Style.RESET_ALL).strip()

        if command.startswith("cd "):
            dir_name = command[3:].strip()
            new_path = os.path.normpath(os.path.join(current_path, dir_name)).replace('\\', '/')
            if any(item.filename == dir_name and item.isDirectory for item in contents):
                current_path = new_path
                print(Fore.GREEN + f"Changed directory to '{current_path}'." + Style.RESET_ALL)
            else:
                print(Fore.RED + "Directory does not exist." + Style.RESET_ALL)
        elif command.startswith("cat "):
            file_name = command[4:].strip()
            file_path = os.path.normpath(os.path.join(current_path, file_name)).replace('\\', '/')
            content = read_file_from_share(smb_connection, share_name, file_path)
            if content:
                print(Fore.YELLOW + f"Contents of '{file_name}':\n{content}" + Style.RESET_ALL)
            else:
                print(Fore.RED + f"Could not read file '{file_name}'." + Style.RESET_ALL)
        elif command.startswith("upload "):
            parts = command.split(' ', 2)
            if len(parts) < 3:
                print(Fore.RED + "Usage: upload <local_file_path> <remote_file_name>" + Style.RESET_ALL)
                continue
            local_file_path = parts[1]
            remote_file_name = parts[2]
            upload_file_to_share(smb_connection, share_name, local_file_path, remote_file_name)
        elif command.lower() == "exit":
            print(Fore.GREEN + "Exiting the tool. Goodbye!" + Style.RESET_ALL)
            break
        else:
            print(Fore.RED + "Invalid command. Use 'cd', 'cat', or 'upload <local> <remote>', or 'exit'." + Style.RESET_ALL)

    smb_connection.close()


if __name__ == "__main__":
    main()
