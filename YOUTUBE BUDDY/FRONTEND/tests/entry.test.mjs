import test from 'node:test';
import assert from 'node:assert/strict';
import {workspaceDestination,loginHref} from '../src/lib/studio/entry.ts';
test('workspace login preserves valid tool, query and fragment destinations',()=>{for(const p of ['/launch/','/master/?tool=360','/master/','/studios/video-editor/','/image/create/','/create/?tab=models','/workbench/#video'])assert.equal(workspaceDestination(p),p);assert.equal(loginHref('/studio/cinematic/'),'/login/?next=%2Fstudio%2Fcinematic%2F');});
test('login return rejects external destinations, auth loops and malformed paths',()=>{for(const p of ['https://evil.test','//evil.test','/\\evil.test','/login/?next=/login/','/signup/','/unknown','/studioevil/','/studio/\ncreate/','/studio/ bad',null,''])assert.equal(workspaceDestination(p),'/studios/');});
