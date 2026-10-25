import {storedZip} from './local-tools';
self.onmessage=(event:MessageEvent)=>{try{const bytes=storedZip(event.data.entries);self.postMessage({bytes});}catch(error){self.postMessage({error:error instanceof Error?error.message:'Archive creation failed.'});}};
export {};
