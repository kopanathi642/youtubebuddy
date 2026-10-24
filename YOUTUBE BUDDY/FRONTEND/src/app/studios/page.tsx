import type {Metadata} from 'next';
import {StudioHub} from '@/components/studios/StudioHub';
import './studios.css';
export const metadata:Metadata={title:'30 Creative Workspaces — YouTube Buddy X',description:'Explore all 30 YouTube Buddy categories. Shared local projects, editable scene plans, real image and audio editing, caption exports, rights records and explicit feature availability.'};
export default function StudiosPage(){return <StudioHub/>;}
