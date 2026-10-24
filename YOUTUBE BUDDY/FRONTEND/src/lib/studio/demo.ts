// Public demonstration credentials. These grant browser-only sandbox access, never API authorization.
export const DEMO_ID='demo@youtubebuddy.com';
export const DEMO_PASSWORD='Demo@12345';
export function validDemoLogin(id:string,password:string){return id.trim().toLowerCase()===DEMO_ID&&password===DEMO_PASSWORD;}
export const DEMO_SESSION_KEY='buddy-browser-demo';
export const DEMO_DESTINATION='/create/?demo=1';
export function beginBrowserDemo(id:string,password:string,storage:Pick<Storage,'setItem'>):string{
 if(!validDemoLogin(id,password))throw Error('Use demo@youtubebuddy.com and the password Demo@12345 for the demo.');
 try{storage.setItem(DEMO_SESSION_KEY,'active');}catch{throw Error('Demo mode needs browser site storage. Allow site data for this app, then try again.');}
 return DEMO_DESTINATION;
}
export function isDemoId(id:string){return id.trim().toLowerCase()===DEMO_ID;}
