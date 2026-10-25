"""Bounded CPU processing. Paths are resolved by the authenticated API, never by user JSON."""
import json, math, shutil, subprocess
from pathlib import Path
from uuid import uuid4
from app.tools.registry import require_tool
from app.ai.providers.errors import UnsupportedCapability


def probe(path):
    r=subprocess.run(['ffprobe','-v','error','-show_format','-show_streams','-of','json',str(path)],capture_output=True,text=True,timeout=15,check=True)
    result=json.loads(r.stdout)
    duration=float(result.get('format',{}).get('duration') or 0)
    if not math.isfinite(duration) or duration<=0:raise ValueError('Media duration is unavailable or invalid.')
    if duration>300:raise ValueError('This CPU tool accepts at most 300 seconds of media.')
    return result


def number(value,default,minimum,maximum):
    v=default if value is None else float(value)
    if not math.isfinite(v) or not minimum<=v<=maximum:raise ValueError('Numeric parameter is outside supported limits.')
    return v


def _run(args):
    r=subprocess.run(['ffmpeg','-nostdin','-hide_banner','-loglevel','error','-y',*args],capture_output=True,text=True,timeout=120)
    if r.returncode:raise RuntimeError('FFmpeg processing failed: '+r.stderr[-500:])


def execute(tool_id,source,output_dir,options=None):
    tool=require_tool(tool_id)
    if tool['engine']!='ffmpeg' or tool['status']!='implemented':raise UnsupportedCapability('No implemented server engine for this capability.',tool_id)
    if not shutil.which('ffmpeg') or not shutil.which('ffprobe'):raise UnsupportedCapability('Install FFmpeg and ffprobe on the CPU worker.',tool_id)
    options=options or {}
    allowed={'video.trim_split':{'ranges'},'video.slow_motion':{'speed'},'video.freeze_frame':{'at'},'video.crop_portrait':set(),'video.crop_square':set(),'video.crop_landscape':set(),'audio.normalize':set(),'media.inspect':set(),'media.validate_ratio':{'ratio'},'media.check_corruption':set(),'media.validate_export':set()}[tool_id]
    if set(options)-allowed:raise ValueError('Unsupported option for selected tool.')
    source=Path(source).resolve()
    if not source.is_file():raise FileNotFoundError('Source media is missing.')
    metadata=probe(source);duration=float(metadata['format']['duration']);video=next((s for s in metadata['streams'] if s.get('codec_type')=='video'),None)
    output_dir=Path(output_dir).resolve();output_dir.mkdir(parents=True,exist_ok=True)
    files=[]
    def dest(ext='mp4'):return output_dir/(uuid4().hex+'.'+ext)
    try:
        if tool_id in {'media.inspect','media.validate_export'}:return {'files':[],'metadata':metadata}
        if tool_id=='media.check_corruption':
            _run(['-i',str(source),'-f','null','-']);return {'files':[],'metadata':{'decoded_without_error':True,'duration':duration}}
        if tool_id=='media.validate_ratio':
            if not video:raise ValueError('Video stream required.')
            ratio=options.get('ratio','16:9')
            if ratio not in {'16:9','9:16','1:1','4:5'}:raise ValueError('Unsupported ratio.')
            w,h=map(float,ratio.split(':'));actual=video['width']/video['height'];return {'files':[],'metadata':{'ratio':ratio,'matches':abs(actual-w/h)<.015,'width':video['width'],'height':video['height']}}
        if tool_id=='video.trim_split':
            ranges=options.get('ranges',[[0,min(10,duration)]])
            if not isinstance(ranges,list) or not 1<=len(ranges)<=10:raise ValueError('Provide 1–10 time ranges.')
            for pair in ranges:
                if not isinstance(pair,list) or len(pair)!=2:raise ValueError('Each range is [start,end].')
                start=number(pair[0],0,0,duration);end=number(pair[1],duration,0,duration)
                if end<=start:raise ValueError('Range end must follow start.')
                path=dest();files.append(str(path));_run(['-ss',str(start),'-i',str(source),'-t',str(end-start),'-c:v','libx264','-preset','veryfast','-c:a','aac','-movflags','+faststart',str(path)])
        else:
            path=dest('png' if tool_id=='video.freeze_frame' else 'm4a' if tool_id=='audio.normalize' else 'mp4');files.append(str(path))
            if tool_id=='video.freeze_frame':
                at=number(options.get('at'),0,0,max(0,duration-.01));_run(['-ss',str(at),'-i',str(source),'-frames:v','1',str(path)])
            elif tool_id=='audio.normalize':
                if not any(s.get('codec_type')=='audio' for s in metadata['streams']):raise ValueError('Audio stream required.')
                _run(['-i',str(source),'-vn','-af','loudnorm=I=-16:TP=-1.5:LRA=11','-c:a','aac',str(path)])
            else:
                if not video:raise ValueError('Video stream required.')
                if tool_id=='video.slow_motion':
                    speed=number(options.get('speed'),.5,.25,1);vf=f'setpts=PTS/{speed}';extra=['-an']
                else:
                    a={'video.crop_portrait':9/16,'video.crop_square':1,'video.crop_landscape':16/9}[tool_id]
                    w=video['width'];h=video['height'];cw=int(min(w,h*a))//2*2;ch=int(min(h,w/a))//2*2
                    if min(cw,ch)<2:raise ValueError('Video is too small to crop.')
                    vf=f'crop={cw}:{ch},setsar=1';extra=['-c:a','aac']
                _run(['-i',str(source),'-vf',vf,'-c:v','libx264','-preset','veryfast',*extra,'-movflags','+faststart',str(path)])
        outputs=[]
        for file in files:
            p=Path(file)
            if not p.is_file() or p.stat().st_size<32:raise RuntimeError('Engine produced an empty output.')
            if p.suffix!='.png':probe(p)
            else:
                from PIL import Image
                with Image.open(p) as image:image.verify()
            outputs.append({'filename':p.name,'bytes':p.stat().st_size})
        return {'files':outputs,'metadata':{'source_duration':duration,'engine':'ffmpeg','operation':tool_id,'audio_policy':'muted for slow motion' if tool_id=='video.slow_motion' else 'source when supported'}}
    except Exception:
        for f in files:Path(f).unlink(missing_ok=True)
        raise
