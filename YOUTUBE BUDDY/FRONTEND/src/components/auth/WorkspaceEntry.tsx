'use client';
import {useEffect,useState} from 'react';
import {useAuth} from '@/context/AuthContext';
import {isBrowserDemo} from '@/lib/studio/demo';
import {loginHref} from '@/lib/studio/entry';
// A public demo preference gates local UI only. API access still needs real auth.
export function WorkspaceEntry({children}:{children:React.ReactNode}){const {user,loading}=useAuth();const [demo,setDemo]=useState<boolean|null>(null);useEffect(()=>{try{setDemo(isBrowserDemo(localStorage,sessionStorage));}catch{setDemo(false);}},[]);useEffect(()=>{if(!loading&&demo===false&&!user)location.replace(loginHref(location.pathname+location.search+location.hash));},[loading,demo,user]);if(loading||demo===null||(!user&&!demo))return <main className="min-h-dvh bg-[#08090b] text-white flex items-center justify-center" role="status">Opening your workspace…</main>;return <>{children}</>;}
