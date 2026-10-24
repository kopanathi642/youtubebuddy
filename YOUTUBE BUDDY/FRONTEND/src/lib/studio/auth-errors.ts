export function authErrorMessage(status:number,payload:unknown):string{
 const data=payload&&typeof payload==='object'?payload as Record<string,unknown>:{};
 const detail=data.detail;
 if(typeof detail==='string'&&detail&&detail!=='Not Found')return detail;
 if(detail&&typeof detail==='object'&&!Array.isArray(detail)&&typeof (detail as Record<string,unknown>).message==='string')return (detail as {message:string}).message;
 if(Array.isArray(detail)&&typeof detail[0]?.msg==='string')return detail[0].msg;
 if(typeof data.message==='string'&&data.message)return data.message;
 if(status===404||status===405)return 'Account sign-in is not connected on this site. Use demo@youtubebuddy.com with Demo@12345 to enter the demo workspace.';
 if(status===401||status===403)return 'The email or password was not accepted. Demo credentials open the browser demo only.';
 if(status===429)return 'Too many sign-in attempts. Please wait and try again.';
 return 'The account service could not complete sign-in. Try the demo or retry your configured account service.';
}
