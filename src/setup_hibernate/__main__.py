#!/usr/bin/env python3

import subprocess
import os
import re
import argparse
import difflib

SWAPFILE = "/swapfile"
FSTAB = "/etc/fstab"
GRUB_CONF = "/etc/default/grub"
MKINITCPIO = "/etc/mkinitcpio.conf"

preview = False
non_interactive = False

def run(cmd, capture=False):
    if preview:
        print(f"[preview] Would run: {cmd}")
        return "" if capture else None
    subprocess.run(cmd, shell=True, check=True)
    if capture:
        return subprocess.check_output(cmd, shell=True, text=True).strip()

def confirm_file_change(path, new_lines):
    if preview or non_interactive:
        print(f"[preview] Would write changes to {path}")
        return True
    with open(path, "r") as f:
        old_lines = f.readlines()
    diff = list(difflib.unified_diff(old_lines, new_lines, fromfile=path, tofile=path))
    if diff:
        print("\n--- Diff ---")
        for line in diff:
            print(line.rstrip())
        answer = input(f"[?] Apply these changes to {path}? (y/N): ")
        return answer.lower() == "y"
    else:
        print(f"[-] No changes needed for {path}.")
        return False

def create_swapfile(size_gb):
    print(f"[+] Creating {size_gb}G swapfile...")
    run(f"fallocate -l {size_gb}G {SWAPFILE}")
    run(f"chmod 600 {SWAPFILE}")
    run(f"mkswap {SWAPFILE}")
    run(f"swapon {SWAPFILE}")

def update_fstab():
    print("[+] Ensuring swapfile is in /etc/fstab...")
    if preview:
        print(f"[preview] Would append to {FSTAB}: {SWAPFILE} none swap defaults 0 0")
        return
    with open(FSTAB, "r") as f:
        old_lines = f.readlines()
        if any(SWAPFILE in line for line in old_lines):
            print("[-] Swapfile already in fstab.")
            return
    new_lines = old_lines + [f"{SWAPFILE} none swap defaults 0 0\n"]
    if confirm_file_change(FSTAB, new_lines):
        with open(FSTAB, "w") as f:
            f.writelines(new_lines)
    else:
        print("[!] Skipped writing to fstab.")

def get_swap_uuid():
    print("[+] Getting swap UUID...")
    return run(f"findmnt -no UUID -T {SWAPFILE}", capture=True)

def get_resume_offset():
    print("[+] Calculating resume_offset...")
    out = run(f"filefrag -v {SWAPFILE}", capture=True)
    for line in out.splitlines():
        match = re.search(r"^\s*\d+:\s+\d+\.\.\s*\d+:\s+(\d+)", line)
        if match:
            offset = match.group(1)
            if offset != "0":
                print(f"[✓] Found resume_offset: {offset}")
                return offset
    raise RuntimeError("Couldn't find valid resume offset.")

def update_grub(uuid, offset):
    print("[+] Updating GRUB_CMDLINE_LINUX_DEFAULT...")
    if preview:
        print(f"[preview] Would modify {GRUB_CONF} to include resume=UUID={uuid} resume_offset={offset}")
        run("update-grub")
        return

    with open(GRUB_CONF, "r") as f:
        lines = f.readlines()

    new_lines = lines[:]
    for i, line in enumerate(new_lines):
        if line.startswith("GRUB_CMDLINE_LINUX_DEFAULT"):
            # Extract current quoted content
            match = re.match(r'^(GRUB_CMDLINE_LINUX_DEFAULT=)(["\'])(.*)(\2)$', line.strip())
            if not match:
                print("[!] Unexpected format in GRUB_CMDLINE_LINUX_DEFAULT, skipping safe modification.")
                continue

            prefix, quote, content, _ = match.groups()

            # Remove existing resume/resume_offset if present
            content = re.sub(r'\s*resume=UUID=\S+', '', content)
            content = re.sub(r'\s*resume_offset=\S+', '', content)
            content = content.strip()

            # Append new values
            resume_args = f"resume=UUID={uuid} resume_offset={offset}"
            if content:
                content += f" {resume_args}"
            else:
                content = resume_args

            # Write the modified line
            new_lines[i] = f"{prefix}{quote}{content}{quote}\n"
            break

    if confirm_file_change(GRUB_CONF, new_lines):
        with open(GRUB_CONF, "w") as f:
            f.writelines(new_lines)
        run("update-grub")
    else:
        print("[!] Skipped writing to grub config.")

def update_mkinitcpio():
    print("[+] Ensuring resume hook in mkinitcpio.conf...")
    if preview:
        print(f"[preview] Would ensure 'resume' is included in {MKINITCPIO}")
        run("mkinitcpio -P")
        return

    with open(MKINITCPIO, "r") as f:
        lines = f.readlines()

    new_lines = lines[:]
    for i, line in enumerate(new_lines):
        if line.startswith("HOOKS="):
            # Extract hook list
            match = re.search(r'\((.*?)\)', line)
            if not match:
                continue

            hooks = match.group(1).split()
            if "resume" in hooks:
                print("[-] 'resume' hook already present.")
                return

            # Insert resume after encrypt (or just before filesystems as fallback)
            if "encrypt" in hooks:
                index = hooks.index("encrypt") + 1
            elif "filesystems" in hooks:
                index = hooks.index("filesystems")
            else:
                index = len(hooks)

            hooks.insert(index, "resume")
            new_line = f'HOOKS=({" ".join(hooks)})\n'
            new_lines[i] = new_line
            break

    if confirm_file_change(MKINITCPIO, new_lines):
        with open(MKINITCPIO, "w") as f:
            f.writelines(new_lines)
        run("mkinitcpio -P")
    else:
        print("[!] Skipped writing to mkinitcpio.")

def main():
    global preview, non_interactive

    if os.geteuid() != 0:
        print("This script must be run as root.")
        return

    parser = argparse.ArgumentParser(description="Configure hibernation with optional swapfile setup.")
    parser.add_argument("--create-swapfile", action="store_true", help="Create and configure a swapfile")
    parser.add_argument("--swap-size", type=int, default=32, help="Swapfile size in GB (default: 32)")
    parser.add_argument("-p", "--preview", action="store_true", help="Show what would be done without making changes")
    parser.add_argument("--non-interactive", action="store_true", help="Apply all changes without prompting")
    args = parser.parse_args()

    preview = args.preview
    non_interactive = args.non_interactive

    if args.create_swapfile:
        create_swapfile(args.swap_size)
        update_fstab()

    uuid = get_swap_uuid()
    offset = get_resume_offset()
    update_grub(uuid, offset)
    update_mkinitcpio()

    if preview:
        print("\n✅ Hibernate setup preview complete.")
    else:
        print("\n✅ Hibernate setup complete. Please reboot your system:")
        print("    sudo reboot")

if __name__ == "__main__":
    main()