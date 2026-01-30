import os
from pathlib import Path
import json
import shutil
import subprocess

# Define the root of the workspace (Safety Sandbox)
WORKSPACE_ROOT = Path(__file__).parent.parent / "workspace"

# Define the root for memory/manifest
MIND_ROOT = Path(__file__).parent.parent / "mind"

# --- WORKSPACE TOOLS (Safe File Operations) ---

def read_file(filepath: str) -> str:
    """Safely read a file from workspace with UTF-8 encoding and fallback."""
    full_path = WORKSPACE_ROOT / filepath
    
    # Security: Prevent path traversal
    if not full_path.resolve().is_relative_to(WORKSPACE_ROOT.resolve()):
        raise ValueError(f"Access denied: {filepath} outside workspace")
    
    if not full_path.exists():
        raise FileNotFoundError(f"{filepath} not found")
    
    # Try UTF-8 first, fallback to latin-1 if it fails
    try:
        return full_path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        print(f"   > ⚠️ Warning: {filepath} has encoding issues, using latin-1 fallback")
        try:
            return full_path.read_text(encoding="latin-1")
        except Exception as e:
            print(f"   > ❌ Could not read {filepath}: {e}")
            return f"[FILE READ ERROR: {filepath}]"

def write_file(filepath: str, content: str) -> None:
    """Safely write a file to workspace with UTF-8 encoding."""
    full_path = WORKSPACE_ROOT / filepath
    
    # Security check
    if not full_path.resolve().is_relative_to(WORKSPACE_ROOT.resolve()):
        raise ValueError(f"Access denied: {filepath} outside workspace")
    
    # Create parent directories if needed
    full_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Try to clean the content of problematic characters
    try:
        # Ensure content is valid UTF-8
        content.encode('utf-8')
        full_path.write_text(content, encoding="utf-8")
    except UnicodeEncodeError:
        # If content has weird characters, clean them
        print(f"   > ⚠️ Warning: Cleaning non-UTF-8 characters from {filepath}")
        clean_content = content.encode('utf-8', errors='ignore').decode('utf-8')
        full_path.write_text(clean_content, encoding="utf-8")

def list_files(directory: str = ".") -> list[str]:
    """List files in workspace directory."""
    full_path = WORKSPACE_ROOT / directory
    
    if not full_path.resolve().is_relative_to(WORKSPACE_ROOT.resolve()):
        raise ValueError(f"Access denied: {directory} outside workspace")
    
    if not full_path.exists():
        return []
    
    # Return relative paths
    return [str(p.relative_to(WORKSPACE_ROOT)) for p in full_path.rglob("*") if p.is_file()]

# --- MIND TOOLS (Internal System Use Only) ---

def load_mind_files() -> tuple[dict, dict]:
    """Loads both manifest and memory."""
    manifest_path = MIND_ROOT / "manifest.json"
    memory_path = MIND_ROOT / "memory.json"
    
    # Defaults if missing
    if not manifest_path.exists():
        manifest = {}
    else:
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            print("   > ⚠️ Warning: manifest.json has errors, using empty dict")
            manifest = {}

    if not memory_path.exists():
        memory = {}
    else:
        try:
            memory = json.loads(memory_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            print("   > ⚠️ Warning: memory.json has errors, using empty dict")
            memory = {}

    return manifest, memory

def update_memory(new_memory: dict) -> None:
    """Used by Finalizer to save state."""
    MIND_ROOT.mkdir(parents=True, exist_ok=True)
    memory_path = MIND_ROOT / "memory.json"
    memory_path.write_text(json.dumps(new_memory, indent=2), encoding="utf-8")

def reset_project_memory() -> str:
    """Wipes workspace and resets Mind files."""
    if WORKSPACE_ROOT.exists():
        shutil.rmtree(WORKSPACE_ROOT)
    WORKSPACE_ROOT.mkdir(exist_ok=True)
    
    MIND_ROOT.mkdir(parents=True, exist_ok=True)

    default_manifest = {
        "project_name": "New Project",
        "tech_stack": [],
        "rules": []
    }
    (MIND_ROOT / "manifest.json").write_text(json.dumps(default_manifest, indent=2), encoding="utf-8")

    default_memory = {
        "pending_tasks": [],
        "completed_tasks": [],
        "known_files": [],
        "error_log": []
    }
    (MIND_ROOT / "memory.json").write_text(json.dumps(default_memory, indent=2), encoding="utf-8")
    
    return "Memory wiped. Workspace cleared. Ready for new project."

def run_command(command: str) -> str:
    """Executes a terminal command in the workspace with robust encoding handling."""
    forbidden = ["rm -rf /", "format", "sudo"]
    if any(bad in command for bad in forbidden):
        return "Error: Command blocked for security."
        
    try:
        result = subprocess.run(
            command,
            cwd=WORKSPACE_ROOT,
            shell=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors='replace',  # Replace bad chars instead of crashing
            timeout=10 
        )
        
        # Clean output to ensure it's safe
        stdout = result.stdout if result.stdout else ""
        stderr = result.stderr if result.stderr else ""
        
        output = f"EXIT CODE: {result.returncode}\nSTDOUT:\n{stdout}\nSTDERR:\n{stderr}"
        return output
        
    except subprocess.TimeoutExpired:
        return "Error: Execution timed out (infinite loop?)."
    except Exception as e:
        return f"System Error: {str(e)}"
