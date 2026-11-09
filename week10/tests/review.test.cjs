// Exercise the annotation code with a minimal DOM, without touching browser/user state.
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const html = fs.readFileSync(path.join(__dirname, '../review/manual20.html'), 'utf8');
const script = html.match(/<script>([\s\S]*)<\/script>/)[1];
const data = JSON.parse(script.match(/const DATA = (.*);/)[1]);
const nativeWidth=data.records[0].width, nativeHeight=data.records[0].height;
const elements = new Map();
const events = {};
const context = {clearRect(){},drawImage(){},strokeRect(){},fillRect(){},fillText(){}};
let exported;
function element(id) {
  if (!elements.has(id)) elements.set(id, {value:'', textContent:'', files:[],
    addEventListener(name, callback){ events[name] = callback; },
    getContext(){return context;},
    getBoundingClientRect(){return {left:0,top:0,width:400,height:400};},
    setPointerCapture(){},click(){},remove(){},appendChild(){}});
  return elements.get(id);
}
const sandbox = vm.createContext({console, Blob, setTimeout(callback){callback();},
  document:{getElementById:element, createElement:()=>element('download'),body:element('body')},
  localStorage:{getItem(){return null;},setItem(){}},
  URL:{createObjectURL(blob){exported=blob;return 'blob:test';},revokeObjectURL(){}},
  Image: class {constructor(){this.naturalWidth=nativeWidth;this.naturalHeight=nativeHeight;} set src(value){this.onload();}}
});
vm.runInContext(script, sandbox);
assert.equal(vm.runInContext('rows.length', sandbox), 20);
// A positive without a box must not advance or become an automatic annotation.
element('status').value='positive';element('save').onclick();
assert.equal(vm.runInContext('index',sandbox),0);
assert.match(element('message').textContent,/Draw at least one box/);
// Pointer-to-native-pixel conversion must preserve original image coordinates.
events.pointerdown({pointerId:1,clientX:100,clientY:100});
events.pointermove({clientX:300,clientY:300});
events.pointerup({clientX:300,clientY:300});
const box=JSON.parse(vm.runInContext('JSON.stringify(rows[0].boxes[0])',sandbox));
assert.deepEqual(box,{x:nativeWidth/4,y:nativeHeight/4,width:nativeWidth/2,height:nativeHeight/2});
element('status').value='negative';element('save').onclick();
assert.equal(vm.runInContext('index',sandbox),0);
assert.match(element('message').textContent,/Delete the boxes/);
element('status').value='positive';element('save').onclick();
assert.equal(vm.runInContext('index',sandbox),1);
element('export').onclick();
(async()=>{
  const text=await exported.text();
  const obj=JSON.parse(text);
  assert.equal(Object.keys(obj._via_img_metadata).length,20);
  const first=Object.values(obj._via_img_metadata)[0];
  assert.equal(first.file_attributes.status,'positive');
  assert.equal(first.regions[0].shape_attributes.width,nativeWidth/2);
  element('import').files=[{async text(){return text;}}];
  await element('import').onchange({target:element('import')});
  assert.equal(vm.runInContext('rows[0].boxes[0].width',sandbox),nativeWidth/2);
  assert.match(element('message').textContent,/Loaded your saved annotations/);
  const invalid=JSON.parse(text);
  Object.values(invalid._via_img_metadata)[0].regions[0].shape_attributes.x=999999;
  element('import').files=[{async text(){return JSON.stringify(invalid);}}];
  await element('import').onchange({target:element('import')});
  assert.match(element('message').textContent,/Box outside image/);
  assert.equal(vm.runInContext('rows[0].boxes[0].x',sandbox),nativeWidth/4);
  console.log('Review checks passed: status guards, scaled coordinates, VIA export/resume, invalid-import protection.');
})().catch(e=>{console.error(e);process.exitCode=1;});
