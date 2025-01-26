from src import ahc_download_tools
from src import ahc_analyze

import subprocess
import toml
import sys
import os
from pathlib import Path
import webbrowser
import asyncio


RESOURCEDIR = "src"
CONTEST_SOURCECODEDIR = "contest"
CONTEST_TEMPLATEDIR = "template"
CONTEST_RESOURCE = "contest"

PALLALEL = 10
TIMEOUT = "timeout 5s"

USAGE  ="""
# usage: 
# python manage.py abc301 new
# python manage.py abc301 open a
# python manage.py abc301 python test a
# python manage.py ahc024 python test
"""

# 一番上のインタプリタがデフォルトになる
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

os.chdir(os.path.dirname(os.path.abspath(__file__)))

argv = sys.argv
if len(argv) < 3:
    print("invalid argument")
    print(USAGE)
    exit()

contest_name = sys.argv[1]
argv = sys.argv[2:]

interpreter = ""

class Contest:
    def __init__(self, contest_name, interpreter, taskname):
        self.__contest_name = contest_name
        self.__interpreter = interpreter
        self.__contest_name = contest_name
        self.__taskname = taskname
        
    @property
    def contest_name(self):
        return self.__contest_name
    
    @property
    def interpreter(self):
        return self.__interpreter
    
    @property
    def taskname(self):
        return self.__taskname
    
    @property
    def contest_resource_path(self):
        return Path(CONTEST_RESOURCE) / self.__contest_name / self.__taskname
    
    @property
    def source_path(self):
        return Path(CONTEST_SOURCECODEDIR) / self.__contest_name / f"{self.__taskname}.{EXTENSIONS[self.__interpreter]}"
    
    def __change_cargoyaml(self):
        cargopath = (Path(CONTEST_SOURCECODEDIR) / "Cargo.toml")
        with open(cargopath, "r") as f:
            data = toml.load(f)
        for bin_section in data.get('bin', []):
            if 'name' in bin_section and 'path' in bin_section:
                bin_section['name'] = contest_name + "_" + self.__taskname
                bin_section['path'] = contest_name + "/" + self.__taskname + ".rs"
                
        with open(cargopath, "w") as f:
            toml.dump(data, f)
    
    def open_task(self, *args):
        url = f"https://atcoder.jp/contests/{self.__contest_name}/tasks/{self.__contest_name}_{self.__taskname}"
        webbrowser.open(url)
        if not self.source_path.exists():
            self.source_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.source_path, "w") as f:
                temp = Path(CONTEST_SOURCECODEDIR) / CONTEST_TEMPLATEDIR / f"{self.__interpreter}.{EXTENSIONS[self.__interpreter]}"
                if temp.exists():
                    with open(temp, "r") as template:
                        f.write(template.read())
                else:
                    f.write("")
        if "code" in os.environ["PATH"]:
            subprocess.call(f"code {self.source_path}", shell=True)
        else:
            subprocess.call(f"cursor {self.source_path}", shell=True)
        
        if self.__interpreter == "rust":
            self.__change_cargoyaml()
                
        if not (self.contest_resource_path / "test").exists():
            self.contest_resource_path.mkdir(parents=True, exist_ok=True)
            subprocess.call(f"cd {self.contest_resource_path}\noj download {url}", shell=True)
            
        if "ahc" in self.__contest_name:
            # gitinit
            if not (self.source_path.parent / ".git").exists():
                subprocess.call(f"cd {self.source_path.parent}\ngit init\ngit branch -m main\ngit add *", shell=True)
            if not (self.contest_resource_path / "tools").exists():
                tools, webvis = ahc_download_tools.main(url)
                if tools:
                    toolsdir = Path(CONTEST_RESOURCE) / self.__contest_name / self.__taskname / "tools"
                    subprocess.call(f"mv {tools} {toolsdir}", shell=True)
                if webvis:
                    webvisdir = Path(CONTEST_RESOURCE) / self.__contest_name / self.__taskname / "webvis"
                    subprocess.call(f"mv {webvis} {webvisdir}", shell=True)
        
    def test(self):
        if not self.contest_resource_path.exists():
            print("testcase not found")
            return
        if not self.source_path.exists():
            print("source code not found")
            return
        
        if not Path(".temp").exists():
            Path(".temp").mkdir(exist_ok=True)
            
        if self.__interpreter == "python":
            import shutil
            path = Path(CONTEST_SOURCECODEDIR) / self.__contest_name / (self.__taskname + ".py")
            path = shutil.copy(path, ".temp/run")
            isok = 0
            runcommand = f"python {path}"
        if self.__interpreter == "pypy":
            import shutil
            path = Path(CONTEST_SOURCECODEDIR) / self.__contest_name / (self.__taskname + ".py")
            path = shutil.copy(path, ".temp/run")
            isok = 0
            runcommand = f"pypy3 {path}"
        if self.__interpreter == "rust":
            self.__change_cargoyaml()
            command = f"docker compose exec rust cargo build --manifest-path {CONTEST_SOURCECODEDIR}/Cargo.toml --release --bin {self.__contest_name}_{self.__taskname}"
            isok = subprocess.call(command, shell=True)
            runcommand = f'{CONTEST_SOURCECODEDIR}/target/release/{self.__contest_name}_{self.__taskname}'

        if isok != 0:
            raise Exception("build error")
        
        command = f'cd {self.contest_resource_path}\noj test -j {PALLALEL} -c "docker compose exec {self.__interpreter} {TIMEOUT} {runcommand}"'
        isok = subprocess.call(command, shell=True)

        return isok == 0
    
    async def ahctest(self, n):
        if not (self.contest_resource_path / "tools").exists():
            print("tools not found")
            return
        if not self.source_path.exists():
            print("source code not found")
            return
        
        seeds_path = Path(self.contest_resource_path) / "tools" / "seeds.txt"
        if seeds_path.exists():
            with open(seeds_path) as f:
                seeds = f.read().split("\n")
        else:
            seeds = [""]
                
        if seeds[-1] != str(n - 1):
            with open(self.contest_resource_path / "tools" / "seeds.txt", "w") as f:
                f.write("\n".join([str(i) for i in range(n)]))
            command = f"cargo run --manifest-path {self.contest_resource_path}/tools/Cargo.toml --bin gen {self.contest_resource_path}/tools/seeds.txt"
            subprocess.call(command, shell=True)
        
        seeds = [str(i).zfill(4) + ".txt" for i in range(n)]
        
        intxt = (Path(self.contest_resource_path) / "tools" / "in")
        outtxt = (Path(self.contest_resource_path) / "tools" / "out")
        othertxt = (Path(self.contest_resource_path) / "tools" / "other")
        for txt in [intxt, outtxt, othertxt]:
            txt.mkdir(parents=True, exist_ok=True)
        for seed in seeds:
            open(othertxt / seed, "w").close()
        
        (Path(self.contest_resource_path) / "tools" / "out").mkdir(parents=True, exist_ok=True)
        
        if (Path(self.contest_resource_path) / "tools" / "src" / "bin" / "tester.rs").exists():
            command = f"cargo build --manifest-path {self.contest_resource_path}/tools/Cargo.toml --release --bin tester"
            subprocess.call(command, shell=True)

        if self.__interpreter == "python":
            import shutil
            path = Path(CONTEST_SOURCECODEDIR) / self.__contest_name / (self.__taskname + ".py")
            path = shutil.copy(path, "temp")
            isok = 0
            runcommand = f"python {path}"
        if self.__interpreter == "pypy":
            import shutil
            path = Path(CONTEST_SOURCECODEDIR) / self.__contest_name / (self.__taskname + ".py")
            path = shutil.copy(path, "temp")
            isok = 0
            runcommand = f"pypy3 {path}"
        if self.__interpreter == "rust":
            self.__change_cargoyaml()
            command = f"docker compose exec rust cargo build --manifest-path {CONTEST_SOURCECODEDIR}/Cargo.toml --release --bin {self.__contest_name}_{self.__taskname}"
            isok = subprocess.call(command, shell=True)
            runcommand = f'{CONTEST_SOURCECODEDIR}/target/release/{self.__contest_name}_{self.__taskname}'

        if isok != 0:
            raise Exception("build error")
        
        async def test(seed):
            command = f"docker compose exec {self.__interpreter} {runcommand}"
            testerexe = Path(self.contest_resource_path) / "tools" / "target" / "release" / "tester"
            if testerexe.exists():
                command = str(testerexe) + " " + command
            command = command + f' < {intxt / seed} 1> {outtxt / seed} 2>> {othertxt / seed}'
            subprocess.call(command, shell=True)
            
        tasks = [test(seed) for seed in seeds]
        await asyncio.gather(*tasks)
        
        visexe = Path(self.contest_resource_path) / "tools" / "target" / "release" / "vis"
        if not visexe.exists():
            command = f"cargo build --manifest-path {self.contest_resource_path}/tools/Cargo.toml --release --bin vis"
            subprocess.call(command, shell=True)

        async def vis(seed):
            command = f"./{visexe} {intxt / seed} {outtxt / seed} 1>> {othertxt / seed} 2>> {othertxt / seed}"
            subprocess.call(command, shell=True)  
            
        tasks = [vis(seed) for seed in seeds]
        await asyncio.gather(*tasks)  
        
        vishtml = Path("vis.html")
        if vishtml.exists():
            vishtml.unlink()
            
        if not Path(self.contest_resource_path).exists():
            Path(self.contest_resource_path).mkdir(parents=True, exist_ok=True)
        
        print("Test Done!!")

        result_path = ahc_analyze.main(str(self.source_path), str(self.contest_resource_path))
        resultpath = Path(result_path)
        if not resultpath.exists():
            return

        # subprocess.call(f"code {resultpath / "summary.txt"}", shell=True)
        webvis = Path(self.contest_resource_path) / "webvis"
        # print("webvis", webvis, "result_path", result_path)
        if webvis.exists():
            with open(webvis, "r") as f:
                webvisurl = f.read().split("\n")[0]

            with open(Path(result_path) / "out" / "0000.txt", "r") as f:
                import urllib
                webvisurl = webvisurl + "&output=" + urllib.parse.quote(f.read())
            
            # print("webvisurl", webvisurl)
            webbrowser.open(webvisurl)
        
        
    def submit(self):
        if not self.source_path.exists():
            print("source code not found")
            return
        
        if not self.test():
            print("テストに失敗しました、提出しますか？[y/n]")
            if input()[0] != "y":
                return
            
        url = f"https://atcoder.jp/contests/{self.__contest_name}/tasks/{self.__contest_name}_{self.__taskname}"
        
        command = f'oj submit -y -l {LANGUAGE_CODE[self.__interpreter]} {url} {self.source_path}'
        with open('/dev/null', 'w') as devnull:
            subprocess.Popen(command, shell=True, stdout=devnull, stderr=devnull)

    def ahcsubmit(self):
        if not self.source_path.exists():
            print("source code not found")
            return
        
        resultpath = Path(CONTEST_RESOURCE) / self.__contest_name / self.__taskname / "result"
        import pandas as pd
        # [0] = date(str), , [1] = score(float)
        scores = pd.read_csv(resultpath / "score.txt", header=None, delimiter=" = ", dtype={0: str, 1: float})  
        
        choices = {
            "min": scores[1].min(),
            "max": scores[1].max(),
            "latest": scores[1].iloc[-1],
        }
        print("choose tag")
        for k, v in choices.items():
            print(f"{k}: {v}")
        tag = input()
        if tag not in choices:
            print("invalid tag")
            return
        
        choice = scores[scores[1] == choices[tag]].iloc[0]
        choicepath = resultpath / str(choice[0]) / self.source_path.name
        if not choicepath.exists():
            print("source code not found")
            return

        url = f"https://atcoder.jp/contests/{self.__contest_name}/tasks/{self.__contest_name}_{self.__taskname}"
        
        command = f'oj submit -y -l {LANGUAGE_CODE[self.__interpreter]} {url} {choicepath}'
        with open('/dev/null', 'w') as devnull:
            subprocess.Popen(command, shell=True, stdout=devnull, stderr=devnull)
        
        
def open_task(*args):
    #[0] = taskname
    taskname = args[0]
    Contest(contest_name, interpreter, taskname).open_task()

def make_samples(*args):
    #[0] = taskname
    #[1] = n
    taskname = args[0]
    raise "not implemented"

def test(*args):
    #[0] = taskname
    #[1] = n
    taskname = args[0]
    n = args[1] if len(args) > 1 else 10
    contest = Contest(contest_name, interpreter, taskname)
    if "ahc" in contest_name:
        asyncio.run(contest.ahctest(n))
    else:
        contest.test()

    
def submit(*args):
    #[0] = taskname
    taskname = args[0]
    contest = Contest(contest_name, interpreter, taskname)
    if "ahc" in contest_name:
        contest.ahcsubmit()
    else:
        contest.submit()


for k in INTERPRETER:
    if k in argv:
        interpreter = INTERPRETER[k]
        break

if interpreter == "":
    interpreter = list(INTERPRETER.values())[0]

COMMANDS = {
    "test": (test, 1),
    "t": (test, 1),
    "submit": (submit, 1),
    "s": (submit, 1),
    "open": (open_task, 1),
    "o": (open_task, 1),
    "make_samples": (make_samples, 2),
    "mk": (make_samples, 2),
    "m": (make_samples, 2),
}

i = 0
while i < len(argv):
    if argv[i] in COMMANDS:
        command, n = COMMANDS[argv[i]]
        args = []
        for j in range(n):
            if i + j + 1 >= len(argv):
                raise Exception("invalid argument")
            args.append(argv[i + j + 1])
        i += n
        command(*args)
    i += 1      


