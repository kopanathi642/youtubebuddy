'use client';
import { useCallback, useEffect, useState } from 'react';
import { Settings, Bell, Key, Globe, Moon, Monitor } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { api } from '@/lib/api';
import { getErrorMessage } from '@/lib/errors';
import toast from 'react-hot-toast';

type Theme = 'dark' | 'system';
interface Preferences {
  theme: Theme;
  language: string;
  generationComplete: boolean;
  marketingUpdates: boolean;
  browserNotifications: boolean;
}
interface ApiKeyItem {
  id: number;
  name: string;
  prefix: string;
  createdAt: string | null;
}

const PREFS_KEY = 'ytb_settings';
const DEFAULT_PREFS: Preferences = {
  theme: 'dark',
  language: 'English (US)',
  generationComplete: true,
  marketingUpdates: false,
  browserNotifications: true,
};

export default function SettingsPage() {
  const [prefs, setPrefs] = useState<Preferences>(DEFAULT_PREFS);
  const [keys, setKeys] = useState<ApiKeyItem[]>([]);
  const [keysLoading, setKeysLoading] = useState(true);
  const [creatingKey, setCreatingKey] = useState(false);
  const [newKey, setNewKey] = useState<string | null>(null);

  useEffect(() => {
    try {
      const raw = window.localStorage.getItem(PREFS_KEY);
      if (raw) setPrefs({ ...DEFAULT_PREFS, ...JSON.parse(raw) });
    } catch {
      // corrupt or unavailable storage — fall back to defaults
    }
  }, []);

  const loadKeys = useCallback(async () => {
    try {
      const response = await api.user.apiKeys();
      setKeys(Array.isArray(response.data?.data) ? response.data.data : []);
    } catch (error) {
      toast.error(getErrorMessage(error, 'Could not load API keys.'));
    } finally {
      setKeysLoading(false);
    }
  }, []);

  useEffect(() => {
    loadKeys();
  }, [loadKeys]);

  const savePrefs = () => {
    try {
      window.localStorage.setItem(PREFS_KEY, JSON.stringify(prefs));
      toast.success('Preferences saved on this device.');
    } catch {
      toast.error('Could not save preferences (browser storage is unavailable).');
    }
  };

  const createKey = async () => {
    setCreatingKey(true);
    try {
      const response = await api.user.createApiKey('Production Key');
      setNewKey(response.data?.data?.key ?? null);
      await loadKeys();
      toast.success('API key created. Copy it now — it will not be shown again.');
    } catch (error) {
      toast.error(getErrorMessage(error, 'Could not create an API key.'));
    } finally {
      setCreatingKey(false);
    }
  };

  const revokeKey = async (id: number) => {
    try {
      await api.user.revokeApiKey(String(id));
      setKeys((current) => current.filter((k) => k.id !== id));
      toast.success('API key revoked.');
    } catch (error) {
      toast.error(getErrorMessage(error, 'Could not revoke the API key.'));
    }
  };

  const copyKey = async () => {
    if (!newKey) return;
    try {
      await navigator.clipboard.writeText(newKey);
      toast.success('Key copied.');
    } catch {
      toast.error('Copy failed — select the key and copy it manually.');
    }
  };

  return (
    <>
      <div className="sticky top-0 z-20 border-b border-white/6 bg-bg-primary/80 backdrop-blur-xl px-8 py-4 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-white/5 border border-white/10 rounded-xl flex items-center justify-center">
                <Settings className="w-5 h-5 text-white" />
              </div>
              <div>
                <h1 className="font-display text-xl font-bold text-white">Settings</h1>
                <p className="text-xs text-white/40">Manage your application preferences</p>
              </div>
            </div>
            <Button variant="primary" size="sm" onClick={savePrefs}>Save Changes</Button>
          </div>

          <div className="px-8 py-8 max-w-4xl mx-auto space-y-8">
            
            {/* Preferences */}
            <section className="glass border border-white/8 rounded-3xl overflow-hidden">
              <div className="px-8 py-6 border-b border-white/6 flex items-center gap-3">
                <Monitor className="w-5 h-5 text-neon-cyan" />
                <h3 className="font-display font-semibold text-white">Appearance & Behavior</h3>
              </div>
              <div className="p-8 space-y-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-white">Theme</p>
                    <p className="text-xs text-white/40">Select your preferred interface theme</p>
                  </div>
                  <div className="flex gap-2 bg-white/5 p-1 rounded-lg border border-white/10">
                    <button
                      type="button"
                      onClick={() => setPrefs((p) => ({ ...p, theme: 'dark' }))}
                      className={`px-4 py-2 text-xs rounded-md font-medium transition-colors flex items-center gap-2 ${
                        prefs.theme === 'dark' ? 'bg-white/10 text-white' : 'text-white/40 hover:text-white'
                      }`}
                    >
                      <Moon className="w-3.5 h-3.5" /> Dark
                    </button>
                    <button
                      type="button"
                      onClick={() => setPrefs((p) => ({ ...p, theme: 'system' }))}
                      className={`px-4 py-2 text-xs rounded-md font-medium transition-colors flex items-center gap-2 ${
                        prefs.theme === 'system' ? 'bg-white/10 text-white' : 'text-white/40 hover:text-white'
                      }`}
                    >
                      <Monitor className="w-3.5 h-3.5" /> System
                    </button>
                  </div>
                </div>
                
                <div className="h-px w-full bg-white/5" />
                
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-white">Language</p>
                    <p className="text-xs text-white/40">Choose your workspace language</p>
                  </div>
                  <div className="relative">
                    <Globe className="w-4 h-4 text-white/40 absolute left-3 top-1/2 -translate-y-1/2" />
                    <select
                      value={prefs.language}
                      onChange={(e) => setPrefs((p) => ({ ...p, language: e.target.value }))}
                      className="bg-white/5 border border-white/10 rounded-lg pl-9 pr-8 py-2 text-sm text-white focus:outline-none focus:border-neon-cyan/50 appearance-none cursor-pointer"
                    >
                      <option className="bg-bg-primary">English (US)</option>
                      <option className="bg-bg-primary">Spanish</option>
                      <option className="bg-bg-primary">French</option>
                    </select>
                  </div>
                </div>
              </div>
            </section>

            {/* Notifications */}
            <section className="glass border border-white/8 rounded-3xl overflow-hidden">
              <div className="px-8 py-6 border-b border-white/6 flex items-center gap-3">
                <Bell className="w-5 h-5 text-neon-lime" />
                <h3 className="font-display font-semibold text-white">Notifications</h3>
              </div>
              <div className="p-8 space-y-6">
                <ToggleRow 
                  title="Generation Complete" 
                  description="Receive an email when your long renders finish processing." 
                  checked={prefs.generationComplete}
                  onToggle={() => setPrefs((p) => ({ ...p, generationComplete: !p.generationComplete }))}
                />
                <div className="h-px w-full bg-white/5" />
                <ToggleRow 
                  title="Marketing Updates" 
                  description="Receive emails about new AI models and feature releases." 
                  checked={prefs.marketingUpdates}
                  onToggle={() => setPrefs((p) => ({ ...p, marketingUpdates: !p.marketingUpdates }))}
                />
                <div className="h-px w-full bg-white/5" />
                <ToggleRow 
                  title="Browser Notifications" 
                  description="Show desktop alerts while the app is open in a background tab." 
                  checked={prefs.browserNotifications}
                  onToggle={() => setPrefs((p) => ({ ...p, browserNotifications: !p.browserNotifications }))}
                />
              </div>
            </section>

            {/* API Keys */}
            <section className="glass border border-white/8 rounded-3xl overflow-hidden">
              <div className="px-8 py-6 border-b border-white/6 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <Key className="w-5 h-5 text-neon-purple" />
                  <h3 className="font-display font-semibold text-white">API Keys</h3>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  className="border border-white/10 text-white/60"
                  onClick={createKey}
                  disabled={creatingKey}
                >
                  {creatingKey ? 'Generating…' : 'Generate New Key'}
                </Button>
              </div>
              <div className="p-8">
                <p className="text-sm text-white/60 mb-6">Use these keys to authenticate API requests from your own custom applications.</p>
                
                {newKey && (
                  <div className="mb-4 rounded-xl border border-neon-lime/30 bg-neon-lime/5 p-4">
                    <p className="text-xs text-neon-lime mb-2">New key — copy it now, it won&apos;t be shown again.</p>
                    <div className="flex items-center justify-between gap-3">
                      <code className="text-xs font-mono text-white break-all">{newKey}</code>
                      <Button variant="ghost" size="sm" className="shrink-0 text-white/60" onClick={copyKey}>Copy</Button>
                    </div>
                  </div>
                )}

                {keysLoading ? (
                  <p className="text-sm text-white/40">Loading keys…</p>
                ) : keys.length === 0 ? (
                  <p className="text-sm text-white/40">No API keys yet. Generate one to get started.</p>
                ) : (
                  <div className="space-y-3">
                    {keys.map((key) => (
                      <div
                        key={key.id}
                        className="bg-bg-primary/50 border border-white/10 rounded-xl p-4 flex items-center justify-between"
                      >
                        <div>
                          <p className="text-sm font-medium text-white mb-1">{key.name}</p>
                          <p className="text-xs font-mono text-white/40">{key.prefix}••••••••••••••••</p>
                        </div>
                        <div className="flex items-center gap-2">
                          <span className="text-[10px] uppercase font-bold text-neon-lime bg-neon-lime/10 px-2 py-1 rounded">Active</span>
                          <Button
                            variant="ghost"
                            size="sm"
                            className="text-white/40 hover:text-white"
                            onClick={() => revokeKey(key.id)}
                          >
                            Revoke
                          </Button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </section>

          </div>
    </>
  );
}

function ToggleRow({
  title,
  description,
  checked,
  onToggle,
}: {
  title: string;
  description: string;
  checked: boolean;
  onToggle: () => void;
}) {
  return (
    <div className="flex items-center justify-between">
      <div className="pr-8">
        <p className="text-sm font-medium text-white mb-1">{title}</p>
        <p className="text-xs text-white/40 leading-relaxed">{description}</p>
      </div>
      <button
        type="button"
        role="switch"
        aria-checked={checked}
        aria-label={title}
        onClick={onToggle}
        className={`w-10 h-6 rounded-full flex items-center px-1 cursor-pointer transition-colors shrink-0 ${checked ? 'bg-neon-lime' : 'bg-white/10'}`}
      >
        <div className={`w-4 h-4 bg-white rounded-full shadow-sm transition-transform ${checked ? 'translate-x-4' : 'translate-x-0'}`} />
      </button>
    </div>
  );
}
