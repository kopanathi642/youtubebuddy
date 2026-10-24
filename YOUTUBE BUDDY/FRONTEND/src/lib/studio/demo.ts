// Public demonstration credentials. These grant browser-only sandbox access, never API authorization.
export const DEMO_ID='demo@youtubebuddy.com';
export const DEMO_PASSWORD='Demo@12345';
export function validDemoLogin(id:string,password:string){return id.trim().toLowerCase()===DEMO_ID&&password===DEMO_PASSWORD;}
export const DEMO_SESSION_KEY='buddy-browser-demo';
