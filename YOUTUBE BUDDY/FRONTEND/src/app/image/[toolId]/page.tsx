import { ToolStudio } from '@/components/studio/ToolStudio';

export default async function ImageToolPage({ params }: { params: Promise<{ toolId: string }> }) {
  const resolvedParams = await params;
  return <ToolStudio toolId={resolvedParams.toolId} category="image" />;
}

export const dynamicParams = false;
export function generateStaticParams() { return ["create", "cineshot", "moodboard", "character", "persona", "aesthetic", "relight", "inpaint", "faceswap", "charswap", "fashion", "upscale", "draw"].map(toolId => ({toolId})); }
