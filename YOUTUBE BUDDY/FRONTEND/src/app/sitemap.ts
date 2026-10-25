import type {MetadataRoute} from 'next';
import registry from '@/lib/studio/categories.json';
export const dynamic='force-static';
export default function sitemap():MetadataRoute.Sitemap{const base=(process.env.NEXT_PUBLIC_APP_URL||'https://youtube-buddy-x-studio.jazzyisle10.chatgpt.site').replace(/\/$/,'');return ['','/studios','/tools','/launch','/master',...registry.map(c=>'/studios/'+c.slug)].map(route=>({url:base+route+'/',changeFrequency:'weekly',priority:route===''?1:.7}));}
