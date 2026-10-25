import {readdir,readFile,stat} from 'node:fs/promises';
import path from 'node:path';
const root=path.resolve(process.argv[2]||'out');
async function walk(p){const files=[];for(const e of await readdir(p,{withFileTypes:true})){const n=path.join(p,e.name);if(e.isDirectory())files.push(...await walk(n));else if(e.name.endsWith('.html'))files.push(n);}return files;}
const files=await walk(root),broken=new Map();let checked=0;
for(const file of files){const html=await readFile(file,'utf8');for(const match of html.matchAll(/href="(\/[^"<>]*)"/g)){const href=match[1].replace(/&amp;/g,'&');if(href.startsWith('//')||href.startsWith('/_next/'))continue;const url=new URL(href,'https://local.test'),pathname=decodeURIComponent(url.pathname);if(pathname.startsWith('/api/'))continue;const p=path.join(root,pathname),exists=await Promise.all([p,path.join(p,'index.html'),p+'.html'].map(n=>stat(n).then(s=>s.isFile()).catch(()=>false)));checked++;if(!exists.some(Boolean))broken.set(pathname,(broken.get(pathname)||new Set()).add(path.relative(root,file)));}}
console.log(JSON.stringify({pages:files.length,internalLinksChecked:checked,broken:[...broken].map(([route,from])=>({route,from:[...from].slice(0,4)}))},null,2));if(broken.size)process.exitCode=1;
