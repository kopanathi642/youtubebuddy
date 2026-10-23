'use client';

import { createContext, useCallback, useContext, useEffect, useMemo, useState, ReactNode } from 'react';
import { LocalUser, onAuthChange, auth } from '@/lib/firebase';
import { UserProfile } from '@/types';

type AuthUser = LocalUser;

interface AuthContextValue {
  user: AuthUser | null;
  profile: UserProfile | null;
  loading: boolean;
  isAuthenticated: boolean;
  refreshProfile: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue>({
  user: null,
  profile: null,
  loading: true,
  isAuthenticated: false,
  refreshProfile: async () => {},
});

type BackendUserProfile = Partial<UserProfile> & {
  display_name?: string | null;
  picture?: string | null;
  channel_name?: string | null;
  channel_url?: string | null;
  created_at?: string;
  updated_at?: string;
  total_videos?: number;
  total_shorts?: number;
  storage_used?: number;
  storage_limit?: number;
};

const normalizeProfile = (profile: BackendUserProfile): UserProfile => ({
  uid: profile.uid || '',
  email: profile.email || null,
  displayName: profile.displayName ?? profile.display_name ?? null,
  photoURL: profile.photoURL ?? profile.picture ?? null,
  plan: profile.plan || 'free',
  createdAt: profile.createdAt || profile.created_at || '',
  updatedAt: profile.updatedAt || profile.updated_at || '',
  channelName: profile.channelName ?? profile.channel_name ?? undefined,
  channelUrl: profile.channelUrl ?? profile.channel_url ?? undefined,
  totalVideos: profile.totalVideos ?? profile.total_videos,
  totalShorts: profile.totalShorts ?? profile.total_shorts,
  storageUsed: profile.storageUsed ?? profile.storage_used,
  storageLimit: profile.storageLimit ?? profile.storage_limit,
});

const PROFILE_CACHE_KEY = 'ytb_user_profile';

const loadCachedProfile = (): UserProfile | null => {
  if (typeof window === 'undefined') return null;
  try {
    const raw = sessionStorage.getItem(PROFILE_CACHE_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
};

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(() => (typeof window !== 'undefined' ? auth.currentUser : null));
  const [profile, setProfile] = useState<UserProfile | null>(() => loadCachedProfile());
  const [loading, setLoading] = useState<boolean>(() => {
    if (typeof window === 'undefined') return true;
    // If a token is in localStorage but currentUser hasn't settled yet, start in loading
    const hasToken = !!localStorage.getItem('ytb_auth_token');
    return hasToken && !auth.currentUser;
  });

  const loadProfileInBackground = useCallback(async () => {
    try {
      const { api } = await import('@/lib/api');
      const response = await api.user.profile();
      const normalized = normalizeProfile(response.data);
      setProfile(normalized);
      try {
        sessionStorage.setItem(PROFILE_CACHE_KEY, JSON.stringify(normalized));
      } catch {}
    } catch (error) {
      console.warn('Failed to load user profile in background:', error);
    }
  }, []);

  useEffect(() => {
    const unsubscribe = onAuthChange((currentUser) => {
      setUser(currentUser);
      setLoading(false);

      if (currentUser) {
        // Fetch or refresh profile non-blockingly
        loadProfileInBackground();
      } else {
        setProfile(null);
        try {
          sessionStorage.removeItem(PROFILE_CACHE_KEY);
        } catch {}
      }
    });

    return () => unsubscribe();
  }, [loadProfileInBackground]);

  const refreshProfile = useCallback(async () => {
    try {
      const { api } = await import('@/lib/api');
      const response = await api.user.profile();
      const normalized = normalizeProfile(response.data);
      setProfile(normalized);
      try {
        sessionStorage.setItem(PROFILE_CACHE_KEY, JSON.stringify(normalized));
      } catch {}
    } catch (error) {
      console.warn('Failed to refresh user profile:', error);
    }
  }, []);

  // Prefer the saved backend display name over the value derived at sign-in time.
  const displayUser = useMemo<AuthUser | null>(
    () => (user && profile?.displayName ? { ...user, displayName: profile.displayName } : user),
    [user, profile?.displayName]
  );

  return (
    <AuthContext.Provider
      value={{
        user: displayUser,
        profile,
        loading,
        isAuthenticated: !!user,
        refreshProfile,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error('useAuth must be used within AuthProvider');
  return context;
}
