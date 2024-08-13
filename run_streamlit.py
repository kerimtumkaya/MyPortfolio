import subprocess
import sys

def run_streamlit():
    subprocess.run([sys.executable, "-m", "streamlit", "run", "pycaret_streamlit.py"])

if __name__ == "__main__":
    run_streamlit()