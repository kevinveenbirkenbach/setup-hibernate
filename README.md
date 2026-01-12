# Hibernate Setup

A Python-based utility for configuring hibernation on Linux systems using a swap file.
This tool automates resume configuration for GRUB and initramfs and optionally creates a swap file of configurable size.

Designed for Arch-based systems (Arch Linux, Manjaro) and intended for automation and reproducible system setup.

---

## 🛠 Features

* Optionally create and activate a swap file
* Automatically detect UUID and resume offset
* Inject `resume` and `resume_offset` into GRUB config
* Regenerate initramfs via `mkinitcpio`
* Interactive confirmation before file changes
* Preview mode for dry-run without changes
* Non-interactive mode for automation
* Root permission required

---

## 📦 Installation

### Using pip (recommended)

Install directly from PyPI:

```bash
pip install setup-hibernate
```

Or system-wide:

```bash
sudo pip install setup-hibernate
```

Or isolated using pipx:

```bash
pipx install setup-hibernate
```

---

### From source

```bash
git clone https://github.com/kevinveenbirkenbach/setup-hibernate.git
cd setup-hibernate
pip install .
```

---

## 🚀 Usage

Run the tool as root:

```bash
sudo setup-hibernate [OPTIONS]
```

Or via Python module:

```bash
sudo python -m setup_hibernate [OPTIONS]
```

---

## ⚙ Options

| Option              | Description                                                          |
| ------------------- | -------------------------------------------------------------------- |
| `--create-swapfile` | Create and configure a swap file at `/swapfile`                      |
| `--swap-size <int>` | Set the swap file size in GB (default: `32`)                         |
| `-p`, `--preview`   | Show what would be done without executing any changes (dry-run mode) |
| `--non-interactive` | Apply all changes automatically without prompting for confirmation   |

---

## 🧪 Examples

Create a 40GB swapfile and configure hibernation interactively:

```bash
sudo setup-hibernate --create-swapfile --swap-size 40
```

Preview what would happen without actually doing anything:

```bash
sudo setup-hibernate --create-swapfile --swap-size 40 --preview
```

Non-interactive, suitable for automation:

```bash
sudo setup-hibernate --create-swapfile --swap-size 40 --non-interactive
```

---

## ✅ Requirements

* Python 3.8+
* Tools:

  * `fallocate`
  * `mkswap`
  * `swapon`
  * `filefrag`
  * `findmnt`
  * `mkinitcpio`
  * `update-grub`
* Root privileges

No external Python packages are required.

---

## 👤 Author

Developed by **Kevin Veen-Birkenbach**
🌐 [https://www.veen.world](https://www.veen.world)

---

## 📄 License

This project is licensed under the **MIT License**.
See [LICENSE](./LICENSE) for details.
