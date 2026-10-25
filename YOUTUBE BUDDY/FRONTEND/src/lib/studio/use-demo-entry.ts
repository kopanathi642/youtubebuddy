 'use client';
import {useEffect,useState} from 'react';
import {useAuth} from '@/context/AuthContext';
import {isBrowserDemo} from './demo';
import {workspaceDestination} from './entry';
export function useDemoEntry(){const [checked,setChecked]=useState(false);const {user,loading}=useAuth();useEffect(()=>{if(loading)return;try{const params=new URLSearchParams(location.search);if(params.get('account')!=='1'&&(user||isBrowserDemo(localStorage,sessionStorage))){location.replace(workspaceDestination(params.get('next')));return;}}catch{/* Storage errors must leave the form usable. */}setChecked(true);},[loading,user]);return checked;}
