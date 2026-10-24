export const PROJECT_SCHEMA=1;
export type Asset={id:string;name:string;type:string;size:number;createdAt:string;source:string;width?:number;height?:number;duration?:number};
export type Shot={id:string;title:string;description:string;duration:number;camera:string;lighting:string};
export type Task={id:string;title:string;due:string;status:'To do'|'In progress'|'Review'|'Done'};
export type Rights={assetId:string;source:string;license:string;consent:string;notes:string};
export type Project={schema:1;id:string;title:string;brief:string;createdAt:string;updatedAt:string;fields:Record<string,string>;shots:Shot[];tasks:Task[];rights:Rights[];assets:Asset[]};
export type Revision={savedAt:string;project:Project};
// Identifiers for local records only; these are never authentication credentials.
export const uid=()=>globalThis.crypto?.randomUUID?.()||`local-${Date.now().toString(36)}-${Math.random().toString(36).slice(2)}-${Math.random().toString(36).slice(2)}`;
export function newProject(title:string):Project{const now=new Date().toISOString();return {schema:1,id:uid(),title:title.trim().slice(0,160)||'Untitled production',brief:'',createdAt:now,updatedAt:now,fields:{},shots:[],tasks:[],rights:[],assets:[]};}
const record=(v:unknown):v is Record<string,unknown>=>!!v&&typeof v==='object'&&!Array.isArray(v);
const text=(v:unknown,max=200000):v is string=>typeof v==='string'&&v.length<=max;
const list=(v:unknown):v is unknown[]=>Array.isArray(v)&&v.length<=2000;
export function validateProject(v:unknown):Project{
 if(!record(v)||v.schema!==1||!text(v.id,100)||!v.id||!text(v.title,160)||!v.title.trim()||!text(v.brief)||!text(v.createdAt,40)||!text(v.updatedAt,40)||!Number.isFinite(Date.parse(v.createdAt))||!Number.isFinite(Date.parse(v.updatedAt))||!record(v.fields)||Object.keys(v.fields).length>200||!Object.entries(v.fields).every(([k,x])=>text(k,100)&&!['__proto__','constructor','prototype'].includes(k)&&text(x))||!list(v.shots)||!list(v.tasks)||!list(v.rights)||!list(v.assets))throw Error('This is not a supported Buddy project. Import a version 1 project JSON file.');
 const ids=new Set<string>();
 for(const a of v.assets){if(!record(a)||!text(a.id,100)||!a.id||ids.has(a.id)||!text(a.name,300)||!text(a.type,150)||!Number.isSafeInteger(a.size)||Number(a.size)<0||Number(a.size)>100*1024**2||!text(a.createdAt,40)||!text(a.source,1000)||['width','height','duration'].some(k=>a[k]!==undefined&&(typeof a[k]!=='number'||!Number.isFinite(a[k])||Number(a[k])<0)))throw Error('Project asset metadata is invalid.');ids.add(a.id);}
 for(const s of v.shots)if(!record(s)||!text(s.id,100)||!text(s.title,300)||!text(s.description)||typeof s.duration!=='number'||!Number.isFinite(s.duration)||s.duration<=0||s.duration>3600||!text(s.camera,500)||!text(s.lighting,500))throw Error('Project contains an invalid shot.');
 for(const t of v.tasks)if(!record(t)||!text(t.id,100)||!text(t.title,500)||!text(t.due,10)||(t.due!==''&&!/^\d{4}-\d{2}-\d{2}$/.test(t.due))||!['To do','In progress','Review','Done'].includes(String(t.status)))throw Error('Project contains an invalid task.');
 for(const r of v.rights)if(!record(r)||!text(r.assetId,100)||!text(r.source,2000)||!text(r.license,1000)||!text(r.consent,1000)||!text(r.notes,10000))throw Error('Project contains an invalid rights record.');
 return JSON.parse(JSON.stringify(v)) as Project;
}
export function buildPrompt(p:Project):string{
 if(!p.brief.trim())throw Error('Add a project brief first.');
 return [p.brief.trim(),p.fields.style&&`Style: ${p.fields.style}`,p.fields.ratio&&`Output ratio: ${p.fields.ratio}`,p.fields.camera&&`Camera direction: ${p.fields.camera}`,p.fields.lighting&&`Lighting: ${p.fields.lighting}`,p.fields.negative&&`Avoid: ${p.fields.negative}`].filter(Boolean).join('\n');
}
export function shotsFromScript(script:string):Shot[]{
 const paragraphs=script.split(/\n\s*\n/).map(x=>x.trim()).filter(Boolean);
 if(!paragraphs.length)throw Error('Write a script first. Separate scenes with a blank line.');
 if(paragraphs.length>100)throw Error('Use no more than 100 scenes per breakdown.');
 return paragraphs.map((description,i)=>({id:uid(),title:`Scene ${i+1}`,description,duration:5,camera:'Medium shot · eye level',lighting:'Natural'}));
}
export function qualityReport(p:Project):{level:'pass'|'warning'|'error';message:string}[]{
 const issues:{level:'pass'|'warning'|'error';message:string}[]=[];
 if(!p.brief.trim())issues.push({level:'error',message:'The production brief is empty.'});
 if(!p.assets.length)issues.push({level:'warning',message:'No media assets are saved to this project.'});
 for(const a of p.assets){const r=p.rights.find(r=>r.assetId===a.id);if(!r?.source.trim()||!r.license.trim())issues.push({level:'warning',message:`${a.name}: source and license information is incomplete.`});if(a.size===0)issues.push({level:'error',message:`${a.name}: file is empty.`});}
 if(!p.fields.publishTitle?.trim())issues.push({level:'warning',message:'The publishing title is empty.'});
 if((p.fields.publishTitle?.length||0)>100)issues.push({level:'error',message:'YouTube titles must be 100 characters or fewer.'});
 if((p.fields.publishDescription?.length||0)>5000)issues.push({level:'error',message:'YouTube descriptions must be 5,000 characters or fewer.'});
 if(!issues.length)issues.push({level:'pass',message:'Recorded metadata checks passed. This does not certify rights or perform frame/audio inspection.'});
 return issues;
}
export function publishingManifest(p:Project){return {schema:1,projectId:p.id,project:p.title,preparedAt:new Date().toISOString(),title:p.fields.publishTitle||'',description:p.fields.publishDescription||'',tags:(p.fields.publishTags||'').split(',').map(t=>t.trim()).filter(Boolean),assets:p.assets,rights:p.rights,quality:qualityReport(p),uploadStatus:'not_uploaded',note:'Manual publishing package. No account is connected or upload performed.'};}
export type PipelineStep={id:string;name:string;status:'succeeded'|'blocked'|'awaiting_approval';detail:string;output?:string};
export function runPreparation(p:Project):PipelineStep[]{
 const steps:PipelineStep[]=[];
 try{steps.push({id:'prompt',name:'Compile production prompt',status:'succeeded',detail:'Combined your brief and saved direction using fixed formatting; no model called.',output:buildPrompt(p)});}catch(e){steps.push({id:'prompt',name:'Compile production prompt',status:'blocked',detail:(e as Error).message});}
 steps.push(p.shots.length?{id:'shots',name:'Prepare shot list',status:'succeeded',detail:`Serialized ${p.shots.length} saved shots.`,output:JSON.stringify(p.shots,null,2)}:{id:'shots',name:'Prepare shot list',status:'blocked',detail:'Add scenes in Story & Film first.'});
 steps.push({id:'generation',name:'Generate scene media',status:'blocked',detail:'No verified image/video model is connected to this local workflow.'});
 const checks=qualityReport(p);steps.push({id:'quality',name:'Check project metadata',status:'succeeded',detail:`Ran ${checks.length} checks. Review warnings; this is not a rendered-file inspection.`,output:JSON.stringify(checks,null,2)});
 steps.push({id:'approval',name:'Approve manual export package',status:'awaiting_approval',detail:'Review the assets, licenses and metadata before exporting.'});
 return steps;
}
