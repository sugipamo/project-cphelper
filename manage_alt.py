import subprocess
import toml
import sys
import os
from pathlib import Path
import webbrowser
import asyncio

# Constants
RESOURCEDIR = "src"
CONTEST_SOURCECODEDIR = "contest_src"
CONTEST_TEMPLATEDIR = "template"
CONTEST_RESOURCE = "contest_resource"
PARALLEL = 10
TIMEOUT = "timeout 5s"
USAGE = """
# usage:
# python manage.py abc301 new
# python manage.py abc301 open a
# python manage.py abc301 python test a
# python manage.py ahc024 python test
"""

INTERPRETER = {
    "pypy": "pypy",
    "python": "python",
    "rust": "rust",
    "py": "pypy",
    "rs": "rust",
}

EXTENSIONS = {
    "python": "py",
    "pypy": "py",
    "rust": "rs",
}

LANGUAGE_CODE = {
    "python": "5082",
    "pypy": "5078",
    "rust": "5054",
}

# Utils
def load_toml_file(filepath):
    """Load TOML file and return the data."""
    with open(filepath, "r") as f:
        return toml.load(f)

def save_toml_file(filepath, data):
    """Save TOML data to file."""
    with open(filepath, "w") as f:
        toml.dump(data, f)

def execute_command(command):
    """Execute a shell command."""
    return subprocess.call(command, shell=True)

def open_url(url):
    """Open a URL in the default web browser."""
    webbrowser.open(url)

def ensure_directory_exists(path):
    """Ensure the directory exists, create it if it doesn't."""
    Path(path).mkdir(parents=True, exist_ok=True)

class Contest:
    def __init__(self, contest_name, interpreter, taskname):
        self.contest_name = contest_name
        self.interpreter = interpreter
        self.taskname = taskname

    @property
    def contest_resource_path(self):
        return Path(CONTEST_RESOURCE) / self.contest_name / self.taskname

    @property
    def source_path(self):
        return Path(CONTEST_SOURCECODEDIR) / self.contest_name / f"{self.taskname}.{EXTENSIONS[self.interpreter]}"

    def update_cargo_toml(self):
        """Update the Cargo.toml file for Rust."""
        cargopath = Path(CONTEST_SOURCECODEDIR) / "Cargo.toml"
        data = load_toml_file(cargopath)

        for bin_section in data.get('bin', []):
            if 'name' in bin_section and 'path' in bin_section:
                bin_section['name'] = f"{self.contest_name}_{self.taskname}"
                bin_section['path'] = f"{self.contest_name}/{self.taskname}.rs"

        save_toml_file(cargopath, data)

    def open_task(self):
        """Open the contest task in a browser and set up local files."""
        url = f"https://atcoder.jp/contests/{self.contest_name}/tasks/{self.contest_name}_{self.taskname}"
        ensure_directory_exists(self.contest_resource_path)

        if not self.source_path.exists():
            ensure_directory_exists(self.source_path.parent)
            template_path = Path(CONTEST_SOURCECODEDIR) / CONTEST_TEMPLATEDIR / f"{self.interpreter}.{EXTENSIONS[self.interpreter]}"
            with open(self.source_path, "w") as f:
                if template_path.exists():
                    f.write(template_path.read_text())
                else:
                    f.write("")
        execute_command(f"code {self.source_path}")
        open_url(url)

        if self.interpreter == "rust":
            self.update_cargo_toml()

    def run_tests(self):
        """Run the tests for the task."""
        if not self.contest_resource_path.exists() or not self.source_path.exists():
            print("Test resources or source code not found")
            return False

        run_command = self.build_run_command()
        if run_command is None:
            return False

        test_command = f'cd {self.contest_resource_path} && oj test -j {PARALLEL} -c "docker compose exec {self.interpreter} {TIMEOUT} {run_command}"'
        result = execute_command(test_command)
        return result == 0

    def build_run_command(self):
        """Build the run command based on the interpreter."""
        if self.interpreter == "python":
            return f"python {self.source_path}"
        elif self.interpreter == "pypy":
            return f"pypy3 {self.source_path}"
        elif self.interpreter == "rust":
            self.update_cargo_toml()
            build_command = f"docker compose exec rust cargo build --manifest-path {CONTEST_SOURCECODEDIR}/Cargo.toml --release --bin {self.contest_name}_{self.taskname}"
            build_result = execute_command(build_command)
            if build_result != 0:
                print("Build failed")
                return None
            return f"{CONTEST_SOURCECODEDIR}/target/release/{self.contest_name}_{self.taskname}"
        return None

    def submit(self):
        """Submit the task."""
        if not self.source_path.exists():
            print("Source code not found")
            return

        if not self.run_tests():
            print("Tests failed, continue to submit? [y/n]")
            if input().lower()[0] != "y":
                return

        url = f"https://atcoder.jp/contests/{self.contest_name}/tasks/{self.contest_name}_{self.taskname}"
        submit_command = f'oj submit -y -l {LANGUAGE_CODE[self.interpreter]} {url} {self.source_path}'
        execute_command(submit_command)

# Command Functions
def open_task(args):
    taskname = args[0]
    contest = Contest(contest_name, interpreter, taskname)
    contest.open_task()

def test_task(args):
    taskname = args[0]
    contest = Contest(contest_name, interpreter, taskname)
    contest.run_tests()

def submit_task(args):
    taskname = args[0]
    contest = Contest(contest_name, interpreter, taskname)
    contest.submit()

# Main logic
if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    if len(sys.argv) < 3:
        print("Invalid argument")
        print(USAGE)
        exit()

    contest_name = sys.argv[1]
    argv = sys.argv[2:]

    interpreter = ""
    for k in INTERPRETER:
        if k in argv:
            interpreter = INTERPRETER[k]
            break

    if not interpreter:
        interpreter = list(INTERPRETER.values())[0]

    COMMANDS = {
        "test": test_task,
        "t": test_task,
        "submit": submit_task,
        "s": submit_task,
        "open": open_task,
        "o": open_task,
    }

    command = argv[0]
    if command in COMMANDS:
        COMMANDS[command](argv[1:])
    else:
        print(f"Unknown command: {command}")
        print(USAGE)
