export type MotionPreset='push-in'|'pull-out'|'pan-left'|'pan-right'|'drift';
export type MotionSettings={preset:MotionPreset;intensity:number;duration:number;ratio:'16:9'|'9:16'|'1:1';easing:'smooth'|'linear';brightness:number;contrast:number};
export const defaultMotion:MotionSettings={preset:'push-in',intensity:.18,duration:5,ratio:'16:9',easing:'smooth',brightness:100,contrast:100};
export function dimensions(ratio:MotionSettings['ratio']):[number,number]{return ratio==='9:16'?[720,1280]:ratio==='1:1'?[1080,1080]:[1280,720];}
export function motionTransform(progress:number,s:MotionSettings){
 if(!Number.isFinite(progress)||!Number.isFinite(s.intensity)||s.intensity<0||s.intensity>.4)throw Error('Invalid motion parameters.');
 const p=Math.min(1,Math.max(0,progress)),t=s.easing==='smooth'?p*p*(3-2*p):p;
 const amount=s.intensity;
 return {scale:s.preset==='push-in'?1+amount*t:s.preset==='pull-out'?1+amount*(1-t):1+amount,x:s.preset==='pan-left'?amount*(.5-t):s.preset==='pan-right'?amount*(t-.5):s.preset==='drift'?amount*.25*Math.sin(t*Math.PI*2):0,y:s.preset==='drift'?amount*.15*Math.cos(t*Math.PI*2):0};
}
export function drawMotion(ctx:CanvasRenderingContext2D,image:HTMLImageElement,progress:number,s:MotionSettings){
 const c=ctx.canvas,{scale,x,y}=motionTransform(progress,s),cover=Math.max(c.width/image.naturalWidth,c.height/image.naturalHeight),w=image.naturalWidth*cover*scale,h=image.naturalHeight*cover*scale;
 ctx.fillStyle='#080a0c';ctx.fillRect(0,0,c.width,c.height);ctx.save();ctx.filter=`brightness(${s.brightness}%) contrast(${s.contrast}%)`;ctx.drawImage(image,(c.width-w)/2+x*c.width,(c.height-h)/2+y*c.height,w,h);ctx.restore();
}
export function recorderMime(){return ['video/webm;codecs=vp9','video/webm;codecs=vp8','video/webm'].find(t=>typeof MediaRecorder!=='undefined'&&MediaRecorder.isTypeSupported(t));}
