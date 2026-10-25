import type {Metadata} from 'next';
import {notFound} from 'next/navigation';
import registry from '@/lib/studio/categories.json';
import {StudioHub} from '@/components/studios/StudioHub';
import '../studios.css';
export function generateStaticParams(){return registry.map(c=>({category:c.slug}));}
export async function generateMetadata({params}:{params:Promise<{category:string}>}):Promise<Metadata>{const {category}=await params;const c=registry.find(c=>c.slug===category);return {title:c?`${c.name} — YouTube Buddy X`:'Studio not found',description:c?.purpose};}
export default async function CategoryPage({params}:{params:Promise<{category:string}>}){const {category}=await params;if(!registry.some(c=>c.slug===category))notFound();return <StudioHub initialCategory={category}/>;}
