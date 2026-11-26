import argparse,csv,json,hashlib,platform,collections
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def writecsv(path, rows):
    if not rows:return
    with path.open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--input',type=Path,default=Path('task_B_input/handoff_20261117_B'));ap.add_argument('--output',type=Path,default=Path('submissions/B'));a=ap.parse_args();o=a.output;o.mkdir(parents=True,exist_ok=True);(o/'figs').mkdir(exist_ok=True)
    cl=['normal','mild','moderate','severe'];summary=[];bins=[];matrows=[];runs={};report=['# B1 错误分析与校准报告','提交日期：2026-11-24。仅覆盖 2026-11-15 重跑；11-12 主结果无逐图预测。','全部结果为探索性。类别顺序 normal/mild/moderate/severe；矩阵行为真实类别、列为预测类别，比例以真实类别样本数为分母。','ECE 使用文件 probs 的最大值作为置信度，10 个等宽箱，边界 0,0.1,…,1；箱号 min(int(conf*10),9)，左闭右开，末箱含 1。ECE=Σ(n_b/N)|acc_b-conf_b|。空箱均值留空且不连线。','test=71，各类 18/20/20/13。不能确认患者独立；已知官方 split 跨集合重复，未提供重复组映射，不能据本分析排除泄露影响。未拟合校准器、未选模型。']
    ref=None
    for p in sorted((a.input/'00_common/predictions').glob('*.json')):
        d=json.loads(p.read_text(encoding='utf8'));im=d['images'];y=np.array([x['y_true'] for x in im]);z=np.array([x['logits'] for x in im]);pr=np.array([x['probs'] for x in im]);yp=z.argmax(1);paths=[x['path'] for x in im]
        assert d['classes']==cl and len(im)==d['n']==71 and len(set(paths))==71
        assert np.array_equal(yp,[x['y_pred'] for x in im]) and np.array_equal(yp,pr.argmax(1))
        zz=z-z.max(1,keepdims=True);sp=np.exp(zz);sp/=sp.sum(1,keepdims=True)
        assert np.allclose(pr,sp,atol=2e-6) and np.allclose(pr.sum(1),1,atol=2e-6)
        labels=dict(zip(paths,y.tolist()))
        if ref is None:ref=labels
        assert ref==labels
        key=f"{d['arm']}_seed{d['seed']}";runs[key]=dict(zip(paths,yp.tolist()));cm=np.zeros((4,4),int);np.add.at(cm,(y,yp),1);rat=cm/cm.sum(1,keepdims=True)
        local=[]
        for i in range(4):
            for j in range(4):local.append(dict(arm=d['arm'],seed=d['seed'],true=cl[i],pred=cl[j],count=int(cm[i,j]),row_fraction=float(rat[i,j])))
        writecsv(o/f'{key}_confusion.csv',local);matrows+=local
        conf=pr.max(1);ix=np.minimum((conf*10).astype(int),9);correct=yp==y;ece=0;bb=[]
        for b in range(10):
            m=ix==b;n=int(m.sum());c=float(conf[m].mean()) if n else None;acc=float(correct[m].mean()) if n else None
            if n:ece+=n/71*abs(acc-c)
            row=dict(arm=d['arm'],seed=d['seed'],bin=b,left=b/10,right=(b+1)/10,n=n,mean_conf=c,accuracy=acc);bins.append(row);bb.append(row)
        tp=cm[2,2];prec=tp/cm[:,2].sum() if cm[:,2].sum() else 0;rec=rat[2,2]
        s=dict(arm=d['arm'],seed=d['seed'],accuracy=float(correct.mean()),ECE=ece,moderate_precision=float(prec),moderate_recall=float(rec),moderate_F1=float(2*prec*rec/(prec+rec)) if prec+rec else 0)
        for i,c in enumerate(cl):s[f'severe_to_{c}_n']=int(cm[3,i]);s[f'severe_to_{c}_fraction']=float(rat[3,i]);s[f'moderate_to_{c}_n']=int(cm[2,i])
        summary.append(s)
        fig,ax=plt.subplots(figsize=(5,4));ax.plot([0,1],[0,1],'--',color='gray');non=[x for x in bb if x['n']];ax.scatter([x['mean_conf'] for x in non],[x['accuracy'] for x in non])
        for x in non:ax.annotate(f"n={x['n']}",(x['mean_conf'],x['accuracy']),fontsize=8)
        ax.set(xlim=(0,1),ylim=(0,1.05),xlabel='Mean confidence',ylabel='Accuracy',title=f'{key} | ECE={ece:.4f} | exploratory');fig.text(.05,.01,f'Source: {p.name}; images[].probs/y_true; M=10',fontsize=7);fig.tight_layout(rect=(0,.04,1,1));fig.savefig(o/'figs'/f'{key}_reliability.png',dpi=180);plt.close(fig)
        report += [f'## {key}',f'来源：00_common/predictions/{p.name}，images[].y_true/logits/probs/path。',f"ECE={ece:.4f}；moderate precision={prec:.3f}, recall={rec:.3f}, F1={s['moderate_F1']:.3f}。",'|真实/预测|normal|mild|moderate|severe|','|---|---|---|---|---|']
        report += ['|'+cl[i]+'|'+'|'.join(f'{cm[i,j]} ({rat[i,j]:.1%})' for j in range(4))+'|' for i in range(4)]
        report += ['逐箱结果（空箱为 NA）：','|箱|n|平均置信度|准确率|','|---|---|---|---|']+[f"|{x['bin']}|{x['n']}|{x['mean_conf'] if x['n'] else 'NA'}|{x['accuracy'] if x['n'] else 'NA'}|" for x in bb]
    writecsv(o/'metrics.csv',summary);writecsv(o/'calibration_bins.csv',bins);writecsv(o/'confusion_all.csv',matrows)
    stable=[]
    report+=['## C1 跨 seed 错误模式','同一 arm、同一路径在至少 2/3 seed 预测错误定义为重复错误；相同错误目标另行计数。三个 seed 是同一 test 的重复评估，不能合并为 213 个独立样本。']
    for arm in ['A0','A1','A2']:
        ss=[s for s in summary if s['arm']==arm];report += [f"{arm}：severe→normal/mild/moderate（seed 42/52/62）="+str([[s[f'severe_to_{c}_n'] for c in cl[:3]] for s in ss])+f"；moderate recall={[round(s['moderate_recall'],3) for s in ss]}；ECE={[round(s['ECE'],4) for s in ss]}。"]
        for path,yt in ref.items():
            preds=[runs[f'{arm}_seed{s}'][path] for s in [42,52,62]];wrong=sum(x!=yt for x in preds);cnt=collections.Counter(x for x in preds if x!=yt)
            stable.append(dict(arm=arm,path=path,true=cl[yt],pred42=cl[preds[0]],pred52=cl[preds[1]],pred62=cl[preds[2]],wrong_seeds=wrong,repeated_wrong=wrong>=2,same_wrong_target=cl[cnt.most_common(1)[0][0]] if cnt and cnt.most_common(1)[0][1]>=2 else ''))
        rr=[x for x in stable if x['arm']==arm];report += [f"{arm}：≥2 seed 错误 {sum(x['repeated_wrong'] for x in rr)} 张；3 seed 均错 {sum(x['wrong_seeds']==3 for x in rr)} 张；逐图见 stable_errors.csv。"]
    writecsv(o/'stable_errors.csv',stable)
    report+=['## C2 校准边界','ECE 仅为固定分箱下的描述值。71 张分到 10 箱，逐箱估计不稳定；未计算支持 arm 排序的校准不确定性，细微 ECE 变化不能称为可靠改善。所有 seed 均已报告。','复运行：python submissions/B/analyze.py --input task_B_input/handoff_20261117_B --output submissions/B。输入哈希见 input_sha256.csv，版本见 环境.txt。']
    report += ['## C1 类别比较补充','所有9组 severe→normal 均为0/13；severe→mild为0或1/13，severe→moderate为0至2/13。moderate主要误判目标在全部9组均为mild（5–11/20）。A1和A2的moderate召回相对A0均在seed42/52上升、62下降，不构成跨seed一致提升。无图像与病例信息，无法解释具体病变机制。']
    (o/'B1_错误分析与校准报告.md').write_text('\n\n'.join(report),encoding='utf8')
    writecsv(o/'input_sha256.csv',[dict(path=str(p.relative_to(a.input)),sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in sorted(a.input.rglob('*')) if p.is_file()])
    (o/'环境.txt').write_text(f'Python {platform.python_version()}\nnumpy {np.__version__}\nmatplotlib {matplotlib.__version__}\n运行：python submissions/B/analyze.py --input task_B_input/handoff_20261117_B --output submissions/B\n无需 torch，不导入或执行训练代码。',encoding='utf8')
    print(json.dumps(summary,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
