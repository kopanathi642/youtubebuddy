// Generates small previews from the user's local media. Never fetches remote URLs.
export async function mediaPreview(blob:Blob,kind:string):Promise<Blob|null>{
 const canvas=document.createElement('canvas');canvas.width=360;canvas.height=203;const ctx=canvas.getContext('2d');if(!ctx)return null;
 const draw=(source:CanvasImageSource,w:number,h:number)=>{ctx.fillStyle='#090c12';ctx.fillRect(0,0,360,203);const scale=Math.min(360/w,203/h);ctx.drawImage(source,(360-w*scale)/2,(203-h*scale)/2,w*scale,h*scale);return new Promise<Blob|null>(resolve=>canvas.toBlob(resolve,'image/jpeg',.78));};
 if(kind==='image'){try{const bitmap=await createImageBitmap(blob);try{return await draw(bitmap,bitmap.width,bitmap.height);}finally{bitmap.close();}}catch{return null;}}
 if(kind!=='video')return null;
 return new Promise(resolve=>{const video=document.createElement('video'),url=URL.createObjectURL(blob);let done=false,capturing=false;const finish=(result:Blob|null)=>{if(done)return;done=true;clearTimeout(timer);video.pause();video.removeAttribute('src');video.load();URL.revokeObjectURL(url);resolve(result);};const capture=()=>{if(done||capturing||!video.videoWidth)return;capturing=true;draw(video,video.videoWidth,video.videoHeight).then(finish).catch(()=>finish(null));};const timer=setTimeout(()=>finish(null),8000);video.preload='auto';video.muted=true;video.onloadeddata=()=>{if(Number.isFinite(video.duration)&&video.duration>.2)video.currentTime=Math.min(1,video.duration/4);else capture();};video.onseeked=capture;video.onerror=()=>finish(null);video.src=url;});
}
