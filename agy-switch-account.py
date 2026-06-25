#!/usr/bin/env python3
# /// script
# requires-python = ">=3.8"
# dependencies = [
#     "keyring",
# ]
# ///

import os
import sys
import glob
import json
import keyring

if sys.platform.startswith("linux"):
    from keyring.backends.SecretService import Keyring
    keyring.set_keyring(Keyring())

CONFIG_DIR = os.path.expanduser("~/.gemini/antigravity-cli")
ACTIVE_PROFILE_FILE = os.path.join(CONFIG_DIR, "active_profile.txt")
SERVICE_NAME = "gemini"
USERNAME = "antigravity"

def get_active_profile():
    if os.path.exists(ACTIVE_PROFILE_FILE):
        with open(ACTIVE_PROFILE_FILE, "r") as f:
            return f.read().strip()
    return "default"

def set_active_profile(profile_name):
    with open(ACTIVE_PROFILE_FILE, "w") as f:
        f.write(profile_name)

def get_all_profiles():
    profiles = []
    pattern = os.path.join(CONFIG_DIR, "credentials_*.json")
    for f in glob.glob(pattern):
        basename = os.path.basename(f)
        # remove "credentials_" and ".json"
        profilename = basename[12:-5]
        profiles.append(profilename)
    return sorted(profiles)

def print_usage():
    print("Usage: agy-switch-account <profile_name>")
    print("       agy-switch-account delete <profile_name>")
    print("       agy-switch-account export <filepath.json>")
    print("       agy-switch-account import <filepath.json>\n")
    print("Available profiles:")

    active = get_active_profile()
    profiles = get_all_profiles()

    if not profiles:
        print("  (No profiles found yet)")
    else:
        for p in profiles:
            if p == active:
                print(f"  * {p} (active)")
            else:
                print(f"  - {p}")

    print("\nCommands:")
    print("  <profile_name>       Switch to or create a new profile")
    print("  delete <profile>     Delete an existing profile")
    print("  export <file.json>   Export all profiles to a JSON file")
    print("  import <file.json>   Import profiles from a JSON file")

def save_current_token_to_file():
    active = get_active_profile()
    try:
        token = keyring.get_password(SERVICE_NAME, USERNAME)
        if token:
            filepath = os.path.join(CONFIG_DIR, f"credentials_{active}.json")
            with open(filepath, "w") as f:
                f.write(token)
    except Exception as e:
        print(f"Warning: Failed to save current token: {e}")

def delete_profile(profile_name):
    active = get_active_profile()
    if profile_name == active:
        print(f"Error: Cannot delete the active profile '{profile_name}'.")
        print("Please switch to another profile first using 'agy-switch-account <other_profile>'.")
        sys.exit(1)

    filepath = os.path.join(CONFIG_DIR, f"credentials_{profile_name}.json")
    if not os.path.exists(filepath):
        print(f"Error: Profile '{profile_name}' does not exist.")
        sys.exit(1)

    os.remove(filepath)
    print(f"Profile '{profile_name}' has been successfully deleted.")

def export_profiles(export_path):
    save_current_token_to_file()
    profiles = get_all_profiles()
    export_data = {}

    for p in profiles:
        filepath = os.path.join(CONFIG_DIR, f"credentials_{p}.json")
        if os.path.exists(filepath):
            with open(filepath, "r") as f:
                content = f.read().strip()
                if content and content != "{}":
                    try:
                        export_data[p] = json.loads(content)
                    except json.JSONDecodeError:
                        export_data[p] = {}
                else:
                    export_data[p] = {}

    with open(export_path, "w") as f:
        json.dump(export_data, f, indent=2)

    print(f"Successfully exported {len(profiles)} profiles to {export_path}")

def import_profiles(import_path):
    if not os.path.exists(import_path):
        print(f"Error: File '{import_path}' does not exist.")
        sys.exit(1)

    with open(import_path, "r") as f:
        try:
            import_data = json.load(f)
        except Exception as e:
            print(f"Error reading JSON file: {e}")
            sys.exit(1)

    count = 0
    for p, token_data in import_data.items():
        filepath = os.path.join(CONFIG_DIR, f"credentials_{p}.json")
        with open(filepath, "w") as f:
            if token_data:
                json.dump(token_data, f)
            else:
                f.write("{}")
        count += 1

    print(f"Successfully imported {count} profiles from {import_path}")
    print("You can now use 'agy-switch-account <profile_name>' to switch to them.")

def switch_profile(profile_name):
    # 1. Save current active token
    save_current_token_to_file()

    # 2. Prepare new profile
    filepath = os.path.join(CONFIG_DIR, f"credentials_{profile_name}.json")
    new_token = ""
    if os.path.exists(filepath):
        with open(filepath, "r") as f:
            new_token = f.read().strip()
    else:
        with open(filepath, "w") as f:
            f.write("{}")

    # 3. Mark as active
    set_active_profile(profile_name)

    # Update symlink for agy fallback
    symlink_path = os.path.join(CONFIG_DIR, "credentials.json")
    if os.path.lexists(symlink_path):
        os.remove(symlink_path)
    os.symlink(filepath, symlink_path)

    # 4. Apply to Keyring
    # Ensure OS Keyring is completely wiped of old tokens first!
    while True:
        try:
            keyring.delete_password(SERVICE_NAME, USERNAME)
        except Exception:
            break

    if new_token and new_token != "{}":
        try:
            keyring.set_password(SERVICE_NAME, USERNAME, new_token)
            print(f"Switched to profile {profile_name}.")
        except Exception as e:
            print(f"Failed to set token in keyring: {e}")
    else:
        print(f"Switched to new profile {profile_name}. Please login (run agy for authentication).")

def main():
    if not os.path.exists(CONFIG_DIR):
        os.makedirs(CONFIG_DIR)

    if len(sys.argv) < 2:
        print_usage()
        sys.exit(1)

    if sys.argv[1] == "delete":
        if len(sys.argv) < 3:
            print("Error: Please specify the profile to delete.")
            print("Usage: agy-switch-account delete <profile_name>")
            sys.exit(1)
        delete_profile(sys.argv[2])
    elif sys.argv[1] == "export":
        if len(sys.argv) < 3:
            print("Error: Please specify the export file path.")
            print("Usage: agy-switch-account export <filepath.json>")
            sys.exit(1)
        export_profiles(sys.argv[2])
    elif sys.argv[1] == "import":
        if len(sys.argv) < 3:
            print("Error: Please specify the import file path.")
            print("Usage: agy-switch-account import <filepath.json>")
            sys.exit(1)
        import_profiles(sys.argv[2])
    else:
        switch_profile(sys.argv[1])

if __name__ == "__main__":
    main()
