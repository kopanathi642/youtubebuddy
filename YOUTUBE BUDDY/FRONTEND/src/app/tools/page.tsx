import type {Metadata} from 'next';
import {LocalToolWorkbench} from '@/components/studios/LocalToolWorkbench';
export const metadata:Metadata={title:'Local tool workbench — YouTube Buddy X',description:'Run local caption, file, archive, metadata and color tools on your own assets.'};
export default function Page(){return <LocalToolWorkbench/>;}
