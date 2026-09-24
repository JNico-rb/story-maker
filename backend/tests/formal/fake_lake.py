"""Sustituto de `lake` para 007-C13: ni Lean ni red. Lo lanza el modo local como `lake`.

Lee el escenario de `FAKE_LAKE_SCENARIO` (JSON): por orden (`build` o `lean`, o `por_fichero` con
una salida por nombre de fichero), el código de salida, la salida y, si se pide, una espera con un
proceso hijo que también espera. Anota cada llamada
(directorio y argumentos) en `FAKE_LAKE_LOG`, fuera del directorio de datos.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

args = sys.argv[1:]
with Path(os.environ["FAKE_LAKE_LOG"]).open("a", encoding="utf-8") as log:
    log.write(json.dumps({"cwd": os.getcwd(), "args": args, "pid": os.getpid()}) + "\n")

scenario = json.loads(Path(os.environ["FAKE_LAKE_SCENARIO"]).read_text(encoding="utf-8"))
if args[:1] == ["build"]:
    step = scenario.get("build", {"exit_code": 0, "output": ""})
elif "por_fichero" in scenario:  # una salida por fichero compilado, por su nombre
    step = scenario["por_fichero"][Path(args[-1]).name]
else:
    step = scenario["lean"]

if "sleep" in step:
    child = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(120)"])
    Path(os.environ["FAKE_LAKE_PIDS"]).write_text(f"{os.getpid()} {child.pid}", encoding="utf-8")
    time.sleep(step["sleep"])

sys.stdout.write(step["output"])
sys.exit(step["exit_code"])
