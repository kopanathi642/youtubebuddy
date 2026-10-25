export type MediaKind='image'|'video'|'audio';
// Leave space for bounded camera instructions within the server's 6,000-character schema.
export const CREATIVE_PROMPT_LIMIT=5800;
export function generationPrompt(prompt:string,kind:MediaKind,lens:string,movement:string):string {
 const base=prompt.trim();
 if(base.length>CREATIVE_PROMPT_LIMIT)throw Error('Keep your creative prompt within 5,800 characters.');
 const result=[base,kind==='video'?`Camera direction: ${movement}; lens: ${lens}.`:null].filter(Boolean).join('\n');
 if(!result||result.length>6000)throw Error('The generation instructions exceed the server limit.');
 return result;
}
export function mediaGenerationResult(raw:unknown,kind:MediaKind):{url:string} {
 if(!raw||typeof raw!=='object'||Array.isArray(raw))throw Error('The server returned an invalid generation response.');
 const value=raw as Record<string,unknown>;
 if(value.simulated===true)throw Error('Simulated output was rejected.');
 if(value.status!=='completed')throw Error('Generation is not completed. No finished media was returned.');
 if(typeof value.preview_url!=='string'||!value.preview_url.trim())throw Error(`No ${kind} file was returned. Text or a plan is not generated media.`);
 const url=value.preview_url;
 const internal=url.startsWith('/')&&!url.startsWith('//')&&!/[\\\x00-\x20]/.test(url);
 let external=false;try{const parsed=new URL(url);external=parsed.protocol==='https:'&&!parsed.username&&!parsed.password;}catch{/* Relative URLs are checked separately. */}
 const inline=new RegExp('^data:'+kind+'/[a-zA-Z0-9.+-]+;base64,[a-zA-Z0-9+/=]+$').test(url);
 if(!internal&&!external&&!inline)throw Error('The media response contains an unsupported output address.');
 const output=value.model_output;
 if(output&&typeof output==='object'&&!Array.isArray(output)){
  const declared=(output as Record<string,unknown>).type;
  if(typeof declared==='string'&&declared!==kind)throw Error(`Expected ${kind} output; the server returned ${declared}.`);
 }
 return {url};
}

export function generationSupport(kind:MediaKind,toolId:string,hasReference:boolean):{supported:boolean;reason:string} {
 if(kind!=='image')return {supported:false,reason:`The current server has no generative ${kind} adapter. Save a brief or use the local editing workspace.`};
 if(!['create','cineshot','aesthetic','fashion'].includes(toolId))return {supported:false,reason:'This specialist operation has no implemented image adapter. Your reference can be previewed locally.'};
 if(hasReference)return {supported:false,reason:'Reference-guided generation is not implemented by the current adapter. Remove the reference to use supported text-to-image generation.'};
 return {supported:true,reason:'Text-to-image requires an installed local SDXL model and a working processing server. Output quality must be reviewed.'};
}
