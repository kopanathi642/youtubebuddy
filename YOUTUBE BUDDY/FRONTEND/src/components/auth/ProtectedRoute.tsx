'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/context/AuthContext';

interface ProtectedRouteProps {
  children: React.ReactNode;
  redirectTo?: string;
}

export function ProtectedRoute({ children, redirectTo = '/login' }: ProtectedRouteProps) {
  const { user, loading } = useAuth();
  const router = useRouter();
  const [isMounted, setIsMounted] = useState(false);

  useEffect(() => {
    setIsMounted(true);
  }, []);

  useEffect(() => {
    if (isMounted && !loading && !user) {
      router.push(redirectTo);
    }
  }, [isMounted, user, loading, router, redirectTo]);

  if (!isMounted || loading) {
    return (
      <div className="min-h-screen bg-bg-primary flex items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <div className="w-12 h-12 border-2 border-neon-lime/30 border-t-neon-lime rounded-full animate-spin" />
          <p className="text-white/50 text-sm font-mono">Authenticating...</p>
        </div>
      </div>
    );
  }

  if (!user) return null;

  return <>{children}</>;
}
