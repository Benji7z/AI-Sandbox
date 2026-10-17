import subprocess, pathlib, shlex

SANDBOX = pathlib.Path("sandbox").resolve()
SANDBOX.mkdir(exist_ok=True)

ALLOWED_CMDS = {"ls", "cat", "echo", "mkdir", "touch", "grep", "wc", "head", "tail", "pwd"}

def run_command(cmd: str):
    if ">" in cmd:
        left, _, filename = cmd.partition(">")
        filename = filename.strip()
        if not filename:
            return "denied: no filename after >"

        output = run_command(left.strip())  # recurse to run the actual command
        if output.startswith("denied") or output == "timed out":
            return output  # don't write failed/denied output to a file

        target = (SANDBOX / filename).resolve()
        if SANDBOX not in target.parents:
            return f"denied: {filename} resolves outside sandbox"

        target.write_text(output)
        return f"wrote to {filename}"

    parts = shlex.split(cmd)
    if not parts or parts[0] not in ALLOWED_CMDS:
        return f"denied: {parts[0] if parts else cmd}"
    # ... rest stays the same (bwrap call)

    bwrap_cmd = [
        "bwrap",
        "--ro-bind", "/usr", "/usr",
        "--ro-bind", "/lib", "/lib",
        "--ro-bind", "/lib64", "/lib64",
        "--symlink", "usr/bin", "/bin",
        "--bind", str(SANDBOX), "/sandbox",
        "--chdir", "/sandbox",
        "--unshare-all",          # no net, no pid, no ipc namespace sharing
        "--die-with-parent",
        "--new-session",
        "--proc", "/proc",
        "--dev", "/dev",
        *parts,
    ]

    try:
        result = subprocess.run(
            bwrap_cmd,
            capture_output=True,
            text=True,
            timeout=10,
        )
        return result.stdout + result.stderr
    except subprocess.TimeoutExpired:
        return "timed out"
    
if __name__ == "__main__":
    while True:
        cmd = input("sandbox> ").strip()
        if cmd in ("exit", "quit"):
            break
        print(run_command(cmd))