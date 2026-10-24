import {trainVersion} from './classifier';
self.onmessage=(event:MessageEvent)=>{try{const {rows,name,origin}=event.data;self.postMessage({model:trainVersion(rows,name,origin)});}catch(error){self.postMessage({error:error instanceof Error?error.message:'Training failed.'});}};
export {};
