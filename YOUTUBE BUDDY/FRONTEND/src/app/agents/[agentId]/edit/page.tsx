import AgentEditorClient from './AgentEditorClient';
export const dynamicParams=false;
export function generateStaticParams(){return ['trend','script','seo','shorts','upload','pipeline'].map(agentId=>({agentId}));}
export default async function AgentPage({params}:{params:Promise<{agentId:string}>}){const {agentId}=await params;return <AgentEditorClient agentId={agentId}/>;}
