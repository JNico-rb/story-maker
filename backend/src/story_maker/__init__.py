"""story-maker: novelas personalizadas de regalo, generadas por un harness agéntico."""

import os
import sys

if sys.platform == "win32":
    # Sin el VC++ Redistributable, msvc-runtime deja sus DLL en la raíz del venv, que Windows no
    # busca al cargar extensiones como la de onnxruntime (fastembed); architecture.md §15.3.
    os.add_dll_directory(sys.prefix)
