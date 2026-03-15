import runpy
from pathlib import Path

# Streamlit Cloud default entrypoint.
runpy.run_path(str(Path(__file__).with_name("app-2.py")), run_name="__main__")
