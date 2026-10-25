'use client';
import {useEffect} from 'react';
import {isBrowserDemo,DEMO_DESTINATION} from '@/lib/studio/demo';
export function RememberedEntry(){useEffect(()=>{try{if(isBrowserDemo(localStorage,sessionStorage))location.replace(DEMO_DESTINATION);}catch{/* The public landing page remains usable if site storage is blocked. */}},[]);return null;}
