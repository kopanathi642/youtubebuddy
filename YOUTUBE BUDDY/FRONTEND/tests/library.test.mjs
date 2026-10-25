import test from 'node:test';
import assert from 'node:assert/strict';
import {libraryItems} from '../src/lib/studio/library.ts';
const asset=(id,name,type,createdAt='2026-10-25T00:00:00Z')=>({id,name,type,createdAt,size:123,source:'test'});
const projects=[{id:'a',title:'Travel film',assets:[asset('v','same.mp4','video/mp4'),asset('i','Frame.png','image/png'),asset('d','Notes.json','application/json')]},{id:'b',title:'Brand film',assets:[asset('v','same.mp4','video/webm','2026-10-25T01:00:00Z'),asset('a','Theme.wav','audio/wav')]}];
test('video library includes all projects without merging identical file names or asset IDs',()=>{const result=libraryItems(projects,'video');assert.equal(result.length,2);assert.deepEqual(result.map(r=>r.key),['b:v','a:v']);assert.equal(result[0].asset.type,'video/webm');});
test('media filters exclude metadata, search by file/project name and do not mutate source records',()=>{assert.equal(libraryItems(projects).length,4);assert.equal(libraryItems(projects,'image').length,1);assert.equal(libraryItems(projects,'all','  BRAND  ').length,2);assert.equal(libraryItems(projects,'video','unknown').length,0);assert.equal(projects[0].assets.length,3);});
