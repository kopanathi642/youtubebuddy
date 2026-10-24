export function backendConfiguration(value:string|undefined,production:boolean){
 if(!value?.trim())return {available:!production,url:production?'':'http://localhost:8000',reason:production?'The processing server is not connected. Use the local tools, or finish server setup.':''};
 try{const url=new URL(value);if(!['http:','https:'].includes(url.protocol)||url.username||url.password||url.search||url.hash||url.pathname!=='/'&&url.pathname!=='')throw Error();if(production&&url.protocol!=='https:'&&!['localhost','127.0.0.1','[::1]'].includes(url.hostname))throw Error();return {available:true,url:url.origin,reason:''};}catch{return {available:false,url:'',reason:'The processing server address is invalid. Configure a valid HTTPS origin.'};}
}
export const backend=backendConfiguration(process.env.NEXT_PUBLIC_API_URL,process.env.NODE_ENV==='production');
export function requireProcessingServer(){if(!backend.available)throw Error(backend.reason);}
