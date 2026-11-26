from pathlib import Path
import difflib
p=Path('task_B_input/handoff_20261117_B/04_B_audit/code_snapshot')
o=Path('submissions/B');o.mkdir(parents=True,exist_ok=True)
a=p/'train_classifier_HEAD_c663fb3.py';b=p/'train_classifier_current.py'
(o/'snapshot_diff.txt').write_text(''.join(difflib.unified_diff(a.read_text(encoding='utf8').splitlines(True),b.read_text(encoding='utf8').splitlines(True),fromfile=a.name,tofile=b.name)),encoding='utf8')
for f in [a,b]:
 (o/(f.stem+'_numbered.txt')).write_text(''.join(f'{i}: {s}\n' for i,s in enumerate(f.read_text(encoding='utf8').splitlines(),1)),encoding='utf8')
