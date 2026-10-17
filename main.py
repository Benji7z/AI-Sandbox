import subprocess, pathlib, shlex

SANDBOX = pathlib.Path("sandbox").resolve()
SANDBOX.mkdir(exist_ok=True)

ALLOWED_CMDS = {"ls", "cat", "echo", "mkdir", "touch", "grep", "wc", "head", "tail"}

def run_command(cmd: str):
    parts = shlex.split(cmd)
    if not parts or parts[0] not in ALLOWED_CMDS:
        return f"denied: {parts[0] if parts else cmd}"

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