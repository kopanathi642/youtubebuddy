'use client';
import {useEffect,useState} from 'react';
import {Download} from 'lucide-react';
export function DownloadArtifact({filename,body,type='text/plain',label,className='sx-secondary'}:{filename:string;body:string;type?:string;label:string;className?:string}){const [url,setUrl]=useState('');useEffect(()=>{const next=URL.createObjectURL(new Blob([body],{type}));setUrl(next);return()=>URL.revokeObjectURL(next);},[body,type]);return <a href={url||undefined} download={filename} aria-disabled={!url} onClick={e=>{if(!url)e.preventDefault();}} className={className}><Download size={15}/>{label}</a>;}
