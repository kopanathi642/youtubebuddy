'use client';
import Link from 'next/link';
import {ProtectedRoute} from './ProtectedRoute';
import {backend} from '@/lib/studio/runtime';
export function ProcessingAccess({children}:{children:React.ReactNode}){if(backend.available)return <ProtectedRoute>{children}</ProtectedRoute>;return <><div role="status" className="fixed bottom-4 left-1/2 -translate-x-1/2 z-50 max-w-xl rounded-xl border border-amber-300/30 bg-[#171a12] p-4 text-xs text-amber-100 shadow-xl">{backend.reason} <Link className="underline text-lime-300" href="/studios/reframe/">Open working local tools</Link> · <Link className="underline text-lime-300" href="/studios/security/">Setup details</Link></div>{children}</>;}
