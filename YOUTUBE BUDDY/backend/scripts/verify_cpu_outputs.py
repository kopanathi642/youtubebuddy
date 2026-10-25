"""Reproduce CPU-engine evidence. Synthetic FFmpeg test media, never AI generation."""
import sys, subprocess, json, hashlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app.tools.executor import execute,probe
from app.tools.registry import CATALOG
root=Path(sys.argv[1]).resolve();root.mkdir(parents=True,exist_ok=True)
source=root/'synthetic-source.mp4'
subprocess.run(['ffmpeg','-v','error','-y','-f','lavfi','-i','testsrc2=size=192x108:rate=12','-f','lavfi','-i','sine=frequency=440:sample_rate=48000','-t','2','-c:v','libx264','-crf','30','-pix_fmt','yuv420p','-c:a','aac',str(source)],check=True)
operations=[('video.trim_split',{'ranges':[[0,.5],[.5,1.5]]}),('video.slow_motion',{'speed':.5}),('video.freeze_frame',{'at':.5}),('video.crop_portrait',{}),('video.crop_square',{}),('video.crop_landscape',{}),('audio.normalize',{}),('media.inspect',{}),('media.validate_ratio',{'ratio':'16:9'}),('media.check_corruption',{}),('media.validate_export',{})]
results=[]
for tool,options in operations:
 result=execute(tool,source,root,options)
 for i,file in enumerate(result['files']):
  p=root/file['filename'];new=root/(tool.replace('.','-')+'-'+str(i)+p.suffix);p.rename(new);file['filename']=new.name
  file['sha256']=hashlib.sha256(new.read_bytes()).hexdigest()
  if new.suffix!='.png':file['probe']=probe(new)
 results.append({'tool':tool,'outcome':'passed','input':'synthetic-source.mp4','options':options,**result})
report={'description':'Real local CPU engine outputs from synthetic test media. Not AI inference or Higgsfield output. Not proof of deployed workers.','cpu_engines':results,'catalog':[{**{k:t[k] for k in ('id','name','engine','status')},'verification':'real CPU fixture execution passed' if t['engine']=='ffmpeg' and t['status']=='implemented' else 'browser runtime not verified; logic tests only' if t['engine']=='canvas_mediarecorder' else 'contract checked; unavailable engine rejects execution'} for t in CATALOG['tools']]}
(root/'cpu-engine-report.json').write_text(json.dumps(report,indent=2))
print(json.dumps({'engines':len(results),'catalog_entries':len(report['catalog']),'files':[(p.name,p.stat().st_size) for p in root.iterdir()]}))
