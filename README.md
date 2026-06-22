# Antigravity CLI Switch Account

Switch between multiple accounts for the Antigravity CLI (`agy`). Each account is stored as a named profile; the active profile is exposed to `agy` via a symlink and an OS keyring entry.

## Requirements

- Python 3
- `keyring` (`pip install keyring`)
- Linux: a Secret Service provider running (GNOME Keyring, KWallet, KeePassXC with Secret Service enabled, etc.)
- macOS / Windows: `keyring` uses the native credential store automatically (Not Tested)

## Installation

```bash
pip install keyring
chmod +x agy-switch-account.py
sudo ln -s "$(pwd)/agy-switch-account.py" /usr/local/bin/agy-switch-account
```

Or just run it directly: `./agy-switch-account.py <profile>`.

## How it works

State lives under `~/.gemini/antigravity-cli/`:

```
credentials.json          -> credentials_<active>.json   (symlink consumed by agy)
credentials_<name>.json   per-profile token (JSON blob)
active_profile.txt        name of the currently active profile
keyring (Secret Service)  service="agy-switch-account", user="<token>"
```

Switching profiles rewrites the symlink, updates `active_profile.txt`, and writes/clears the keyring entry.

## Usage

```
agy-switch-account <profile_name>          Switch to a profile, or create one if it doesn't exist
agy-switch-account delete <profile_name>   Delete a profile (cannot delete the active one)
agy-switch-account export <file.json>      Export all profiles to a JSON file
agy-switch-account import <file.json>      Import profiles from a JSON file
```

Running with no arguments prints the active profile and the list of saved profiles.

## Typical workflow

```bash
agy-switch-account personal
agy
/exit

agy-switch-account work
agy
/exit

# Switch between them any time
agy-switch-account personal
agy-switch-account work
```

When you switch to a profile that has no saved token, the tool prints `Please login (run agy for authentication)`. Run `agy`, log in, then run `agy-switch-account <same_name>` to capture that session.


## Notes

- Cannot delete the profile that is currently active — switch to another one first.
- `export` writes plain JSON; treat the file as sensitive (it contains auth tokens).
- On Linux, headless sessions without a Secret Service daemon (no `dbus`) will fail with keyring errors.
- This is a simple utility for personal use. Use at your own risk.
