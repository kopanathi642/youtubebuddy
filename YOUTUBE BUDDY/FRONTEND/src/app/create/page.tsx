import type {Metadata} from 'next';
import {CreateStudio} from '@/components/create/CreateStudio';
export const metadata:Metadata={title:'Creative Studio — YouTube Buddy X',description:'Create real motion clips from your images, train local text classifiers and plan creative workflows with explicit tool availability.'};
export default function CreatePage(){return <CreateStudio/>;}
