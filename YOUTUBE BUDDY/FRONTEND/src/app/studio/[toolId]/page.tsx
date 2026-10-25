import { ToolStudio } from '@/components/studio/ToolStudio';

export default async function VideoToolPage({ params }: { params: Promise<{ toolId: string }> }) {
  const resolvedParams = await params;
  return <ToolStudio toolId={resolvedParams.toolId} category="video" />;
}

export const dynamicParams = false;
export function generateStaticParams() { return ["create", "canvas", "mixed", "edit", "ads", "trends", "lipsync", "draw", "sketch", "ugc", "upscale", "animate", "motion", "recast"].map(toolId => ({toolId})); }
