 'use client';
import {useState,useRef,useEffect} from 'react';
import Link from 'next/link';
import {Sidebar} from '@/components/layout/Sidebar';
import {ProcessingAccess} from '@/components/auth/ProcessingAccess';
import {backend} from '@/lib/studio/runtime';
import {api} from '@/lib/api';
import {getErrorMessage} from '@/lib/errors';
import {Sparkles,ArrowUpRight,Plus,SlidersHorizontal,Upload,Clapperboard,ArrowRight,Check,Loader2,Download,Bookmark,Layers,Camera} from 'lucide-react';
import './workspace.css';
type ToolType = 'video' | 'image' | 'audio';

interface ToolConfig {
  id: string;
  name: string;
  desc: string;
  type: ToolType;
  requiresUpload: boolean;
  requiresPrompt: boolean;
  hasStyles: boolean;
}

// Giant map of all tools to simple names and simple configs
const toolConfigs: Record<string, ToolConfig> = {
  // === VIDEO TOOLS ===
  create: { id: 'create', name: 'AI Video Generator', desc: 'Type an idea, get a video.', type: 'video', requiresPrompt: true, requiresUpload: false, hasStyles: true },
  cinematic: { id: 'cinematic', name: 'Cinematic Video', desc: 'Control the camera and action.', type: 'video', requiresPrompt: true, requiresUpload: false, hasStyles: true },
  canvas: { id: 'canvas', name: 'Video Idea Canvas', desc: 'Visual workflow for video ideas.', type: 'video', requiresPrompt: true, requiresUpload: true, hasStyles: false },
  mixed: { id: 'mixed', name: 'Style Blender', desc: 'Mix images and video together.', type: 'video', requiresPrompt: true, requiresUpload: true, hasStyles: true },
  edit: { id: 'edit', name: 'AI Video Editor', desc: 'Edit clips using AI text commands.', type: 'video', requiresPrompt: true, requiresUpload: true, hasStyles: false },
  ads: { id: 'ads', name: 'Video Ad Maker', desc: 'Paste a link, get a video ad.', type: 'video', requiresPrompt: true, requiresUpload: false, hasStyles: true },
  trends: { id: 'trends', name: 'Trending Topics', desc: 'Generate videos based on trends.', type: 'video', requiresPrompt: true, requiresUpload: false, hasStyles: true },
  lipsync: { id: 'lipsync', name: 'Lip Sync AI', desc: 'Match lip movements to audio.', type: 'video', requiresPrompt: false, requiresUpload: true, hasStyles: false },
  draw: { id: 'draw', name: 'Sketch to Video', desc: 'Turn your sketch into a video.', type: 'video', requiresPrompt: true, requiresUpload: true, hasStyles: true },
  sketch: { id: 'sketch', name: 'Drawing to Video', desc: 'Animate your drawings.', type: 'video', requiresPrompt: true, requiresUpload: true, hasStyles: true },
  ugc: { id: 'ugc', name: 'AI Human Presenter', desc: 'Create AI actors for your videos.', type: 'video', requiresPrompt: true, requiresUpload: false, hasStyles: true },
  upscale: { id: 'upscale', name: '4K Video Upscaler', desc: 'Make videos sharper and larger.', type: 'video', requiresPrompt: false, requiresUpload: true, hasStyles: false },
  animate: { id: 'animate', name: 'Video Animation', desc: 'Transform and animate objects.', type: 'video', requiresPrompt: true, requiresUpload: true, hasStyles: true },
  motion: { id: 'motion', name: 'Motion Graphics', desc: 'Professional motion graphics.', type: 'video', requiresPrompt: true, requiresUpload: false, hasStyles: true },
  recast: { id: 'recast', name: 'Replace Actor', desc: 'Change the actor in the video.', type: 'video', requiresPrompt: true, requiresUpload: true, hasStyles: false },

  // === IMAGE TOOLS ===
  cineshot: { id: 'cineshot', name: 'Cinematic Photos', desc: 'Generate cinematic photos.', type: 'image', requiresPrompt: true, requiresUpload: false, hasStyles: true },
  moodboard: { id: 'moodboard', name: 'AI Moodboard', desc: 'Create a visual idea board.', type: 'image', requiresPrompt: true, requiresUpload: true, hasStyles: true },
  character: { id: 'character', name: 'Character Designer', desc: 'Design a unique character.', type: 'image', requiresPrompt: true, requiresUpload: true, hasStyles: true },
  persona: { id: 'persona', name: 'Influencer Creator', desc: 'Create an AI influencer face.', type: 'image', requiresPrompt: true, requiresUpload: true, hasStyles: true },
  aesthetic: { id: 'aesthetic', name: 'Style Finder', desc: 'Find your visual style.', type: 'image', requiresPrompt: true, requiresUpload: false, hasStyles: true },
  relight: { id: 'relight', name: 'Photo Lighting', desc: 'Change the lighting on a photo.', type: 'image', requiresPrompt: false, requiresUpload: true, hasStyles: false },
  inpaint: { id: 'inpaint', name: 'Object Eraser', desc: 'Erase and replace parts of a photo.', type: 'image', requiresPrompt: true, requiresUpload: true, hasStyles: false },
  faceswap: { id: 'faceswap', name: 'Face Swapper', desc: 'Swap faces seamlessly.', type: 'image', requiresPrompt: false, requiresUpload: true, hasStyles: false },
  charswap: { id: 'charswap', name: 'Replace Character', desc: 'Swap the whole character.', type: 'image', requiresPrompt: true, requiresUpload: true, hasStyles: false },
  fashion: { id: 'fashion', name: 'Fashion Designer', desc: 'Generate fashion and clothing.', type: 'image', requiresPrompt: true, requiresUpload: true, hasStyles: true },

  // === AUDIO TOOLS ===
  voiceover: { id: 'voiceover', name: 'AI Voice Generator', desc: 'Turn text into realistic speech.', type: 'audio', requiresPrompt: true, requiresUpload: false, hasStyles: false },
  changevoice: { id: 'changevoice', name: 'Voice Changer', desc: 'Change the voice in an audio file.', type: 'audio', requiresPrompt: false, requiresUpload: true, hasStyles: false },
  translation: { id: 'translation', name: 'Audio Translator', desc: 'Translate audio to another language.', type: 'audio', requiresPrompt: false, requiresUpload: true, hasStyles: false },
};

// Some routes use IDs that are also used by video tools. Keep their image
// definitions separate so these routes cannot accidentally render the video studio.
const imageToolOverrides: Record<string, ToolConfig> = {
  create: { id: 'create', name: 'AI Image Generator', desc: 'Generate stunning AI images from text.', type: 'image', requiresPrompt: true, requiresUpload: false, hasStyles: true },
  draw: { id: 'draw', name: 'Sketch to Art', desc: 'Turn a rough sketch into polished artwork.', type: 'image', requiresPrompt: true, requiresUpload: true, hasStyles: true },
  upscale: { id: 'upscale', name: 'Photo Upscaler', desc: 'Enhance an uploaded image with AI.', type: 'image', requiresPrompt: false, requiresUpload: true, hasStyles: false },
};


const starters=[{name:'Golden hour',kind:'CINEMATIC',look:'gold',prompt:'A quiet coastal road at golden hour. A lone rider approaches the horizon, warm backlight, natural texture, slow tracking shot.'},{name:'After hours',kind:'URBAN',look:'night',prompt:'Rain on an empty city street at night. Neon reflections, an intimate close-up, cool blue shadows, slow dolly in.'},{name:'Object study',kind:'PRODUCT',look:'studio',prompt:'A sculptural ceramic object on a stone pedestal. Soft studio lighting, precise shadows, neutral background, gentle orbit.'}];
export function ToolStudio({toolId,category}:{toolId:string;category:ToolType}){
 const config=(category==='image'&&imageToolOverrides[toolId])||toolConfigs[toolId];
 const [prompt,setPrompt]=useState(''),[style,setStyle]=useState('Cinematic'),[ratio,setRatio]=useState('16:9'),[duration,setDuration]=useState(6),[provider,setProvider]=useState('auto'),[busy,setBusy]=useState(false),[error,setError]=useState(''),[result,setResult]=useState<{url?:string;text?:string}|null>(null),[reference,setReference]=useState<{name:string;url:string;type:string;file:File}|null>(null),[saved,setSaved]=useState(false),[lens,setLens]=useState('35 mm'),[movement,setMovement]=useState('Slow dolly in');
 const input=useRef<HTMLInputElement>(null),urlRef=useRef('');
 useEffect(()=>()=>{if(urlRef.current)URL.revokeObjectURL(urlRef.current);},[]);
 useEffect(()=>{try{const v=JSON.parse(localStorage.getItem('buddy-generation-brief-'+category+'-'+toolId)||'null');if(!v||typeof v.prompt!=='string'||v.prompt.length>12000)return;setPrompt(v.prompt);if(['Cinematic','Realistic','Anime','3D Render'].includes(v.style))setStyle(v.style);if(['16:9','9:16','1:1'].includes(v.ratio))setRatio(v.ratio);if([4,6,8,10].includes(v.duration))setDuration(v.duration);if(['24 mm','35 mm','50 mm','85 mm'].includes(v.lens))setLens(v.lens);if(['Static','Slow dolly in','Tracking shot','Gentle orbit','Handheld'].includes(v.movement))setMovement(v.movement);setSaved(true);}catch{/* An invalid saved draft must not block the tool. */}},[category,toolId]);
 if(!config)return <div className="gx-app"><p>This tool is unavailable.</p><Link href="/studios/">Back to workspaces</Link></div>;
 const tools={...toolConfigs,...(category==='image'?imageToolOverrides:{})};
 function choose(file:File){if(!/^(image|video|audio)\//.test(file.type)||!file.size||file.size>100*1024**2){setError('Choose an image, video or audio file up to 100 MB.');return;}if(urlRef.current)URL.revokeObjectURL(urlRef.current);urlRef.current=URL.createObjectURL(file);setReference({name:file.name,url:urlRef.current,type:file.type,file});setError('');}
 async function generate(){if(!backend.available)return;setBusy(true);setError('');setResult(null);try{let uploadId:number|undefined;if(config.requiresUpload&&!reference)throw Error('Add a source reference first.');if(reference){const body=new FormData();body.append('file',reference.file);uploadId=(await api.videos.upload(body,()=>{})).data.id;}const description=[prompt.trim()||`Apply ${config.name} to the source.`,category==='video'?`Camera direction: ${movement}; lens: ${lens}.`:null].filter(Boolean).join('\n');const response=await api.studio.generate({tool_id:config.id,category,prompt:description,style,aspect_ratio:ratio,duration:category==='video'?duration:undefined,provider,upload_id:uploadId});if(response.data.simulated)throw Error('Simulated output was rejected.');if(!response.data.preview_url&&!response.data.generated_text&&!response.data.model_output)throw Error('The server returned no usable output.');setResult({url:response.data.preview_url,text:response.data.generated_text|| (response.data.model_output?JSON.stringify(response.data.model_output,null,2):undefined)});}catch(e){setError(getErrorMessage(e,'Generation failed.'));}finally{setBusy(false);}}
 function saveBrief(){try{localStorage.setItem('buddy-generation-brief-'+category+'-'+toolId,JSON.stringify({tool:config.name,prompt,style,ratio,duration,lens,movement,savedAt:new Date().toISOString()}));setSaved(true);}catch{setError('Could not save the brief on this browser.');}}
 return <ProcessingAccess><div className="gx-app"><Sidebar/><main className="gx-main"><header className="gx-header"><Link href="/studios/" className="gx-wordmark">BUDDY <b>X</b><span> / CREATE</span></Link><nav aria-label="Creative workspaces"><Link className={category==='video'?'active':''} href="/studio/create/">Video</Link><Link className={category==='image'?'active':''} href="/image/create/">Image</Link><Link className={category==='audio'?'active':''} href="/audio/voiceover/">Audio</Link><Link href="/studios/video-editor/">Editor</Link><Link href="/studios/design/">Canvas</Link></nav><Link href="/studios/director/" className="gx-director"><Sparkles size={14}/> AI Director <ArrowUpRight size={13}/></Link></header>
 <div className="gx-toolstrip" aria-label={category+' tools'}>{Object.values(tools).filter(t=>t.type===category).map(t=><Link key={t.id} className={t.id===toolId?'active':''} href={`/${category==='video'?'studio':category}/${t.id}/`}>{t.name}</Link>)}{category==='video'&&<Link href="/studio/shorts/">Shorts workflow</Link>}</div>
 <div className="gx-workspace"><aside className="gx-controls"><div className="gx-tool-title"><span className="gx-overline">{category.toUpperCase()} STUDIO</span><h1>{config.name}</h1><p>{config.desc}</p></div><div className="gx-step"><span>01</span><h2>Describe your vision</h2><Bookmark size={14}/></div><textarea aria-label="Generation prompt" maxLength={12000} value={prompt} onChange={e=>{setPrompt(e.target.value);setSaved(false);}} placeholder={category==='audio'?'Write your narration or describe the audio…':'Describe your subject, scene, lighting and movement…'}/><div className="gx-prompt-foot"><span>{prompt.length} / 12,000</span><button onClick={()=>setPrompt(starters[0].prompt)}><Sparkles size={12}/> Try a prompt</button></div>
 <div className="gx-step"><span>02</span><h2>{config.requiresUpload?'Source media':'Reference media'}</h2><span className="gx-optional">{config.requiresUpload?'Required':'Optional'}</span></div><input ref={input} hidden type="file" accept="image/*,video/*,audio/*" onChange={e=>{if(e.target.files?.[0])choose(e.target.files[0]);e.target.value='';}}/><button className="gx-upload" onClick={()=>input.current?.click()}><Plus size={22}/><b>{reference?reference.name:'Add a reference'}</b><small>{reference?'Click to replace · stays on your device until Generate':'Image, video or audio · up to 100 MB'}</small></button>
 <div className="gx-step"><span>03</span><h2>Make it yours</h2><SlidersHorizontal size={14}/></div><label className="gx-field">Look<select value={style} onChange={e=>{setStyle(e.target.value);setSaved(false);}}>{['Cinematic','Realistic','Anime','3D Render'].map(s=><option key={s}>{s}</option>)}</select></label>{category!=='audio'&&<div className="gx-field"><span>Frame</span><div className="gx-segment">{['16:9','9:16','1:1'].map(r=><button aria-pressed={ratio===r} onClick={()=>{setRatio(r);setSaved(false);}} key={r}>{r}</button>)}</div></div>}{category==='video'&&<><div className="gx-control-pair"><label className="gx-field">Length<select value={duration} onChange={e=>{setDuration(Number(e.target.value));setSaved(false);}}>{[4,6,8,10].map(d=><option key={d} value={d}>{d} seconds</option>)}</select></label><label className="gx-field">Lens<select value={lens} onChange={e=>{setLens(e.target.value);setSaved(false);}}>{['24 mm','35 mm','50 mm','85 mm'].map(l=><option key={l}>{l}</option>)}</select></label></div><label className="gx-field">Camera movement<select value={movement} onChange={e=>{setMovement(e.target.value);setSaved(false);}}>{['Static','Slow dolly in','Tracking shot','Gentle orbit','Handheld'].map(m=><option key={m}>{m}</option>)}</select></label></>}
 <details className="gx-model"><summary>Processing provider <span>{provider==='auto'?'Automatic':provider}</span></summary><label className="gx-field">Configured server provider<select value={provider} onChange={e=>setProvider(e.target.value)}>{['auto','ollama','huggingface','openai','gemini','groq','openrouter'].map(p=><option key={p} value={p}>{p}</option>)}</select></label><p>Availability depends on the server. Text providers do not automatically provide image, video or voice models.</p></details>
 <div className="gx-submit"><button className="gx-generate" disabled={!backend.available||busy||(config.requiresPrompt&&!prompt.trim())||(config.requiresUpload&&!reference)} onClick={generate}>{busy?<Loader2 className="gx-spin" size={17}/>:<Sparkles size={17}/>} {busy?'Waiting for server':backend.available?'Generate '+category:'Processing server setup required'}<ArrowRight size={16}/></button><button className="gx-save" onClick={saveBrief}>{saved?<Check size={13}/>:<Bookmark size={13}/>} {saved?'Brief saved on this device':'Save creative brief'}</button></div></aside>
 <section className="gx-stage"><div className="gx-stage-top"><div><span className="gx-overline">YOUR CREATIVE SPACE</span><h2>{result?'Your result':reference?'Reference preview':'From an idea to a frame.'}</h2></div><span className="gx-status"><i/>{backend.available?'Server configured':'Local planning mode'}</span></div>{error&&<p className="gx-error" role="alert">{error}</p>}<div className={'gx-monitor '+(!result&&!reference?'gx-monitor-empty':'')}>
 {result?.url?(category==='image'?<img src={result.url} alt="Server-generated result"/>:category==='video'?<video controls src={result.url}/>:<audio controls src={result.url}/>):result?.text?<pre>{result.text}</pre>:reference?(reference.type.startsWith('image/')?<img src={reference.url} alt="Uploaded reference, not generated output"/>:reference.type.startsWith('video/')?<video controls src={reference.url}/>:<audio controls src={reference.url}/>):<><div className="gx-frame-art"><div/><Clapperboard size={44} strokeWidth={1}/><span>YOUR NEXT SCENE</span></div><h3>Make room for the unexpected.</h3><p>Start with a prompt or your own reference.<br/>Your result will appear here after a real generation.</p><button onClick={()=>input.current?.click()}><Upload size={14}/> Add your first reference</button></>}
 {(result||reference)&&<span className="gx-preview-label">{result?'SERVER OUTPUT · REVIEW BEFORE USE':'YOUR REFERENCE · NOT GENERATED'}</span>}</div><div className="gx-stage-caption"><span><Layers size={13}/> {result?'Review the returned file before delivery':reference?reference.name:'Nothing generated yet'}</span>{result?.url&&<a href={result.url} download><Download size={14}/> Download</a>}<Link href="/studios/video-editor/">Open edit workspace <ArrowUpRight size={13}/></Link></div>
 <div className="gx-inspiration-head"><h2>A little direction goes a long way.</h2><span>Prompt starters · not generated results</span></div><div className="gx-starters">{starters.map(s=><button key={s.name} onClick={()=>{setPrompt(s.prompt);setStyle(s.kind==='CINEMATIC'?'Cinematic':'Realistic');setSaved(false);}}><div className={'gx-look '+s.look}><Camera size={25} strokeWidth={1}/><span>+</span></div><div><small>{s.kind}</small><b>{s.name}</b><ArrowUpRight size={13}/></div></button>)}</div><p className="gx-hint">Choose a tool above. Each tool keeps its own purpose clear; media generation requires the matching model on your processing server.</p></section></div></main></div></ProcessingAccess>;
}
