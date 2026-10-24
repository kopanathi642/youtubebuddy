'use client';
import {useEffect,useState} from 'react';
import {isBrowserDemo,DEMO_DESTINATION} from './demo';
// Resolve the remembered public-demo preference before painting a login form.
export function useDemoEntry(){const [checked,setChecked]=useState(false);useEffect(()=>{try{if(new URLSearchParams(location.search).get('account')!=='1'&&isBrowserDemo(localStorage,sessionStorage)){location.replace(DEMO_DESTINATION);return;}}catch{/* A blocked preference store must not break the sign-in form. */}setChecked(true);},[]);return checked;}
