'use client';
import Link from 'next/link';
import {ProtectedRoute} from './ProtectedRoute';
import {backend} from '@/lib/studio/runtime';
export function ProcessingAccess({children}:{children:React.ReactNode}){if(backend.available)return <ProtectedRoute>{children}</ProtectedRoute>;return <><details className="fixed bottom-3 right-3 z-50 max-w-xs rounded-lg border border-amber-300/20 bg-[#171a12] p-3 text-[10px] text-amber-100 shadow-xl"><summary className="cursor-pointer">Processing server offline · setup details</summary><p className="mt-2" role="status">{backend.reason}</p><p className="mt-2"><Link className="underline text-lime-300" href="/studios/reframe/">Open working local tools</Link> · <Link className="underline text-lime-300" href="/studios/security/">Setup details</Link></p></details>{children}</>;}
