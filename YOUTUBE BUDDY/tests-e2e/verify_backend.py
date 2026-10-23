import requests, time, os, sqlite3, hashlib, uuid, datetime, sys
B=os.getenv('API_URL','http://localhost:8000/api/v1'); R=[]
DEV_DB=os.getenv('DEV_DB','../backend/dev.db')  # SQLite file used by the backend under test
VIDEO=os.getenv('TEST_VIDEO','test.mp4')
def chk(name, ok, detail=''): R.append(ok); print(('PASS ' if ok else 'FAIL ')+name+('  — '+str(detail) if detail else ''))
email=f'v{int(time.time())}@example.com'; pw='Test@12345678'
s=requests.post(B+'/auth/signup',json={'email':email,'password':pw,'display_name':'Verify'}); H={'Authorization':'Bearer '+s.json()['access_token']}
chk('signup ok', s.status_code==200)
chk('signup rejects short password', requests.post(B+'/auth/signup',json={'email':'x'+email,'password':'short'}).status_code==422)
# --- arbitrary path exploit
r=requests.post(B+'/uploads/metadata',headers=H,json={'filename':'x.mp4','content_type':'video/mp4','size_bytes':1,'storage_path':'/tmp/victim.txt'})
chk('metadata with /tmp path rejected (was: arbitrary delete)', r.status_code==400, f'{r.status_code} {r.text[:80]}')
chk('victim file still exists', os.path.exists('/tmp/victim.txt'))
r=requests.post(B+'/uploads/metadata',headers=H,json={'filename':'x.mp4','content_type':'video/mp4','size_bytes':1,'storage_path':'../../../../tmp/victim.txt'})
chk('metadata with ../ traversal rejected', r.status_code==400, r.status_code)
# --- upload validation
chk('exe upload rejected', requests.post(B+'/videos/upload',headers=H,files={'file':('evil.exe',b'MZ'*100,'application/octet-stream')}).status_code==415)
chk('fake mp4 (text content) rejected', requests.post(B+'/videos/upload',headers=H,files={'file':('fake.mp4',b'this is not a video at all',"video/mp4")}).status_code==415)
up=requests.post(B+'/videos/upload',headers=H,files={'file':('real.mp4',open(VIDEO,'rb'),'video/mp4')})
chk('real mp4 accepted', up.status_code==200, up.status_code)
j=up.json(); chk('response has url, no storage_path', 'url' in j and 'storage_path' not in j, list(j.keys()))
f=requests.get(j['url']); chk('uploaded file downloadable via url', f.status_code==200 and len(f.content)>1000, f.status_code)
# --- shorts url
g=requests.post(B+'/shorts/generate',headers=H,json={'videoId':j['id'],'aspectRatio':'9:16','captions':True,'autoDetect':True}); chk('shorts generate 202', g.status_code==202, g.status_code)
for _ in range(25):
    q=requests.get(B+'/render-queue/',headers=H).json()['data']
    if q and q[0]['status'] in('completed','failed'): break
    time.sleep(1.5)
chk('render completes', q[0]['status']=='completed', q[0]['status'])
chk('render-queue has result_url, no result_path', q[0].get('result_url') and 'result_path' not in q[0])
rr=requests.get(q[0]['result_url']); chk('rendered short downloadable', rr.status_code==200 and len(rr.content)>1000, f'{rr.status_code} {len(rr.content)}B')
chk('short response hides storage_path', 'storage_path' not in g.json() and 'url' in g.json())
# --- profile update
p=requests.put(B+'/user/profile',headers=H,json={'display_name':'New Name','channel_name':'My Chan'})
chk('PUT profile 200 (was 500)', p.status_code==200 and p.json()['display_name']=='New Name', f'{p.status_code} {p.text[:90]}')
chk('profile persisted', requests.get(B+'/user/profile',headers=H).json()['channel_name']=='My Chan')
# --- bcrypt + legacy upgrade
if os.path.exists(DEV_DB):
    db=sqlite3.connect(DEV_DB)
    h=db.execute('select password_hash from users where email=?',(email,)).fetchone()[0]; chk('new account stored with bcrypt', h.startswith('$2'), h[:7])
    lemail=f'legacy{int(time.time())}@example.com'
    db.execute("insert into users (uid,email,password_hash,display_name,provider,is_active,is_paid,created_at,updated_at) values (?,?,?,?,?,1,0,?,?)",(str(uuid.uuid4()),lemail,hashlib.sha256(b'OldPass@1234').hexdigest(),'Legacy','local',datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None),datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None))); db.commit()
    chk('legacy SHA-256 account can still log in', requests.post(B+'/auth/login',json={'email':lemail,'password':'OldPass@1234'}).status_code==200)
    h2=db.execute('select password_hash from users where email=?',(lemail,)).fetchone()[0]; chk('legacy hash upgraded to bcrypt on login', h2.startswith('$2'), h2[:7])
    chk('wrong password still rejected after upgrade', requests.post(B+'/auth/login',json={'email':lemail,'password':'nope'}).status_code==401)
else:
    print('SKIP legacy-hash upgrade check (set DEV_DB to a SQLite backend file to run it)')
# --- delete cleans file
d=requests.delete(B+f"/videos/{j['id']}",headers=H); chk('delete video WITH renders ok (was 500)', d.status_code==200, f'{d.status_code} {d.text[:80]}'); chk('render file removed from disk after delete', requests.get(q[0]['result_url']).status_code==404)
# --- simulated flag
st=requests.post(B+'/studio/generate',headers=H,json={'tool_id':'script','prompt':'cat math','provider':'gemini'}).json(); chk('studio response flags simulated=true (no AI keys)', st.get('simulated') is True, st.get('simulated'))
ci=requests.post(B+'/cinematic/generate',headers=H,json={'prompt':'sunset','preset':'openai'}).json(); chk('cinematic response flags simulated', ci.get('simulated') is True)
# --- cross-user isolation
H2={'Authorization':'Bearer '+requests.post(B+'/auth/signup',json={'email':'o'+email,'password':pw}).json()['access_token']}
u2=requests.post(B+'/videos/upload',headers=H,files={'file':('b.mp4',open(VIDEO,'rb'),'video/mp4')}).json()
chk("other user cannot read my video", requests.get(B+f"/videos/{u2['id']}",headers=H2).status_code==404)
chk("other user cannot delete my video", requests.delete(B+f"/videos/{u2['id']}",headers=H2).status_code==404)
print(f'\n{sum(R)}/{len(R)} passed'); sys.exit(0 if all(R) else 1)
