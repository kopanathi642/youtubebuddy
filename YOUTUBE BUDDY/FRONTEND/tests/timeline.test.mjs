import test from 'node:test';
import assert from 'node:assert/strict';
import {validateCuts,splitCut,sequenceLength,cutAt,timecode} from '../src/lib/studio/timeline.ts';
const cut={id:'a',assetId:'asset',name:'Source.mp4',kind:'video',in:1,out:7,sourceDuration:10,volume:1,exposure:1,contrast:1,saturation:1};
test('split preserves source bounds, sequence length and cut boundaries',()=>{const result=splitCut([cut],'a',2,'b');assert.deepEqual(result.map(c=>[c.in,c.out]),[[1,3],[3,7]]);assert.equal(sequenceLength(result),6);assert.equal(cutAt(result,2).cut.id,'b');assert.equal(cutAt(result,2).offset,0);assert.equal(cutAt(result,6),null);});
test('unsafe trim, duplicate IDs, nonfinite controls and edge splits are rejected',()=>{for(const patch of [{in:-1},{out:11},{out:1},{volume:2},{contrast:NaN},{saturation:-1}])assert.throws(()=>validateCuts([{...cut,...patch}]));assert.throws(()=>validateCuts([cut,cut]));assert.throws(()=>splitCut([cut],'a',0,'b'));assert.throws(()=>splitCut([cut],'a',6,'b'));assert.throws(()=>splitCut([cut],'a',1,'a'));});
test('timecode is stable across minutes and hour boundaries',()=>{assert.equal(timecode(61.5),'00:01:01:15');assert.equal(timecode(3600),'01:00:00:00');assert.equal(timecode(-1),'00:00:00:00');});
