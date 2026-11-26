from pathlib import Path
import os,subprocess,sys
os.chdir(Path(__file__).resolve().parent)
subprocess.run([sys.executable,'submissions/B/analyze.py'],check=True)
subprocess.run([sys.executable,'submissions/B/reproduce_audit.py'],check=True)
print('Analysis completed; outputs: submissions/B')
