# Setting Docker's Memory Limit

## A. Windows (Docker Desktop with the WSL 2 backend)

With WSL 2, Docker Desktop does not show a memory slider. The limit is set for the WSL 2 virtual machine instead, and it applies to **all** WSL distributions, not only Docker.

1. Close Docker Desktop.

2. Press `Win + R`, type `%UserProfile%`, and press Enter.

3. In that folder, create or open a file named exactly **`.wslconfig`**
   > Make sure it is **NOT** saved as `.wslconfig.txt`. In Notepad, choose *Save as type: All files*.

4. Add the following, adjusting the values to suit your machine:

```ini
[wsl2]
memory=4GB      # Maximum RAM for WSL 2 (and therefore Docker) - 75% of RAM
processors=2    # Optional: number of CPU cores
swap=2GB        # Optional: swap size
```

5. Open PowerShell and shut down WSL so the new settings take effect:

```powershell
wsl --shutdown
```

6. Start Docker Desktop again.

7. Verify the limit:

```powershell
docker info | findstr "Total Memory"
```

> **Note:** If you do not set `memory`, WSL 2 uses up to 50% of your computer's RAM by default.

## B. Windows (Docker Desktop with the Hyper-V backend) and macOS

Docker Desktop runs a virtual machine whose size you control from the settings.

1. Open Docker Desktop.
2. Go to **Settings → Resources → Advanced**.
3. Move the **Memory** slider to the desired value (for example, 4 GB).
4. Click **Apply & restart**.
5. Verify the limit:

```bash
   docker info | grep "Total Memory"
```

## C. Linux

**If you use Docker Desktop for Linux:** follow Section B. It also runs a virtual machine.

**If you use Docker Engine directly (the usual case on Linux):** there is no virtual machine. Containers share the host's memory and have no overall cap by default, so you limit memory **per container**.

1. Using `docker run`:
```bash
   docker run -d --name my-db --memory=2g --memory-swap=2g postgres:16
```
   `--memory-swap` equal to `--memory` prevents the container from using additional swap.
2. Using Docker Compose (`compose.yaml`):
```yaml
   services:
     db:
       image: postgres:16
       deploy:
         resources:
           limits:
             memory: 2g
```
3. Verify the limit (see the `MEM USAGE / LIMIT` column):
```bash
   docker stats --no-stream
```

> **Tip:** The per-container limits in Section C also work on Windows and macOS, inside whatever overall limit Sections A or B set.