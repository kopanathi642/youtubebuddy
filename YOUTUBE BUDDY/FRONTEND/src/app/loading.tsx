export default function Loading() {
  return (
    <div className="min-h-screen bg-bg-primary flex flex-col items-center justify-center p-6 text-center">
      {/* Animated glowing loader */}
      <div className="relative w-16 h-16 mb-6">
        <div className="absolute inset-0 rounded-full border-2 border-neon-lime/20 animate-ping" />
        <div className="w-16 h-16 rounded-full border-2 border-transparent border-t-neon-lime border-r-neon-cyan animate-spin" />
        <div className="absolute inset-3 rounded-full bg-neon-lime/10 blur-sm" />
      </div>

      <div className="space-y-2">
        <p className="text-white font-medium tracking-wide">Loading YouTube Buddy...</p>
        <p className="text-xs text-white/40">Initializing AI workspace</p>
      </div>
    </div>
  );
}
