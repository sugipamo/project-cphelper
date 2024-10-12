import os
import pandas as pd
from pathlib import Path

GROUPS = []

def main(source_path, contest_resource_path):
    source_path = Path(source_path)
    contest_resource_path = Path(contest_resource_path)
    outputs = []
    with open(contest_resource_path / "tools" / "seeds.txt", "r") as f:
        paths = f.read().split("\n")
        paths = [p.zfill(4) + ".txt" for p in paths]
    for path in paths:
        output = {}
        for name in ["out", "other"]:
            with open(contest_resource_path / "tools" / name / path, "r") as f:
                for l in f.read().split("\n"):
                    if not " = " in l:
                        continue
                    x = l.split(" = ")[0]
                    y = l.split(" = ")[1].replace("\n", "")
                    try:
                        y = float(y)
                    except:
                        pass
                    output[x] = y

        import math

        if "score" in output:
            output["Score"] = output["score"]
        if "Score" in output:
            output["logscore"] = math.log(output["Score"] + 1)

        outputs.append(output)

    outputs = pd.DataFrame(outputs)
    outputs.index = paths

    pd.options.display.float_format = '{:.2f}'.format

    resultpath = contest_resource_path / "result"
    

    import datetime
    date = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    if not (resultpath / "score.txt").exists():
        resultpath.mkdir(exist_ok=True, parents=True)
    with open(resultpath / "score.txt", "a") as f:
        f.write(date + " = " + str(outputs["Score"].mean()))
        f.write("\n")
    
    resultpath = resultpath / date
    if not resultpath.exists():
        resultpath.mkdir(exist_ok=True, parents=True)
        
    with open(resultpath / "summary.txt", "w") as f:        
        f.write("\n\n")
        f.write("all data\n")
        f.write(outputs.describe().to_string())
        f.write("\n\n\n")

        def group(name):
            outputss = outputs.groupby(name)
            for d, outputs_ in outputss:
                f.write(name + " = " + str(d) + "\n")
                f.write(outputs_.drop(columns=name).describe().to_string())
                f.write("\n\n\n")

        [group(g) for g in GROUPS]

        f.write(outputs.to_string())
        
    import shutil        
    shutil.move(contest_resource_path.absolute() / "tools" / "out", resultpath)
    shutil.move(contest_resource_path.absolute() / "tools" / "other", resultpath)
    shutil.copy(source_path.absolute(), resultpath.absolute())
        
    print("Analyze Done!!")

    return str(resultpath)