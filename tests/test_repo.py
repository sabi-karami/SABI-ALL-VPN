import unittest,ast,subprocess,json,re,os,sys,tempfile,types,base64
from pathlib import Path
from string import Template
ROOT=Path(__file__).resolve().parents[1]
class RepoTests(unittest.TestCase):
 def test_python_syntax(self):
  for p in ROOT.rglob('*.py'):ast.parse(p.read_text(),str(p))
 def test_shell_syntax(self):
  for p in ROOT.rglob('*.sh'):subprocess.run(['bash','-n',str(p)],check=True,capture_output=True)
 def test_catalog(self):
  c=json.loads((ROOT/'templates/catalog.json').read_text());self.assertEqual(len(c['items']),30);self.assertEqual(len({i['id'] for i in c['items']}),30)
  for i in c['items']:self.assertTrue(i['steps']);self.assertTrue(i['service']);self.assertNotIn('تست کردم',i['evidence'])
 def test_no_live_identity(self):
  for p in ROOT.rglob('*'):
   if p.is_file() and p.suffix not in ['.woff2','.pyc'] and '.git' not in p.parts and p.name!='test_repo.py':
    t=p.read_text()
    self.assertNotRegex(t,r'AKIA[A-Z0-9]{16}');self.assertNotRegex(t,r'-----BEGIN (?:RSA |OPENSSH )?PRIVATE KEY-----')
 def test_no_shell_tracing(self):
  for p in (ROOT/'modules').glob('*.sh'):self.assertNotRegex(p.read_text(),r'(?m)^set -[a-zA-Z]*x')
 def test_core_heredocs(self):
  text=(ROOT/'modules/10-core.sh').read_text()
  blocks=re.findall(r'cat > (\S+) <<EOF\n(.*?)\nEOF',text,re.S)
  self.assertGreaterEqual(len(blocks),2)
  E={x:'test' for x in re.findall(r'\$([A-Z_0-9]+)',text)};E.update(UUID='00000000-0000-4000-8000-000000000001',C='/etc/allvpn/cert',DOMAIN='vpn.example.com',REALITY_SNI='www.example.com',REALITY_PRIV='A'*43,REALITY_SID='1234567890abcdef',SS_METHOD='2022-blake3-aes-128-gcm',SS_KEY='AAAAAAAAAAAAAAAAAAAAAA==',STLS_SS_KEY='AAAAAAAAAAAAAAAAAAAAAA==',TUIC_UUID='00000000-0000-4000-8000-000000000002')
  for file,body in blocks:
   if file.endswith('.json'):json.loads(Template(body).substitute(E))
 def test_catalog_rendering_and_client_fixups(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td);clients=root/'clients';clients.mkdir();data=root/'data';data.mkdir()
   template=(ROOT/'templates/catalog.json').read_text();names=set(re.findall(r'\$\{([^}]+)\}',template));env={k:'SYNTHETIC-'+k for k in names if not k.startswith('LINK_')}
   env.update(REPO=str(ROOT),ENABLE_PPTP='no',ENABLE_PLAIN_PROXY='no',DOMAIN='vpn.example.com',CDN='cdn.example.com',IP='192.0.2.1',ZONE='example.com',DNS_TUNNEL='t.example.com',REGION='test',INSTANCE_ID='test',NAIVE_USER='test',NAIVE_PW='test')
   source=(ROOT/'scripts/catalog.py').read_text();mapping=ast.literal_eval(re.search(r'labels=(\{.*?\})\n',source,re.S)[1]);links=[]
   for label,id in mapping.items():
    if id in ['socks','http']:continue
    if id=='vmess':links.append('vmess://'+base64.b64encode(json.dumps({'ps':label}).encode()).decode())
    else:links.append('vless://test@192.0.2.1:443#'+label)
   (clients/'links.txt').write_text('\n'.join(links));(clients/'telegram-mtproto.txt').write_text('tg://proxy?test\nhttps://t.me/proxy?test\n');(clients/'tor-obfs4-bridge.txt').write_text('Bridge obfs4 192.0.2.1:7443 TEST');(clients/'dnstt-server.pub').write_text('0'*64)
   old=dict(os.environ);os.environ.update(env)
   try:
    src=source.replace("Path('/root/allvpn/clients')",f'Path({str(clients)!r})').replace("Path('/var/lib/allvpn-panel')",f'Path({str(data)!r})');exec(compile(src,'catalog-test','exec'),{})
    c=json.loads((data/'catalog.json').read_text());self.assertEqual(len(c['items']),27);self.assertNotIn('${',(data/'catalog.json').read_text())
   finally:os.environ.clear();os.environ.update(old)
 def test_panel_password_and_auth(self):
  from werkzeug.security import generate_password_hash
  with tempfile.TemporaryDirectory() as tmp:
   p=Path(tmp);(p/'auth.json').write_text(json.dumps({'username':'sabi','password_hash':generate_password_hash('local-test-previous'),'session_key':'local-test-key','version':'1'}));(p/'files').mkdir();(p/'files/test.txt').write_text('test');(p/'files.json').write_text('[{"name":"test.txt","text":true}]');(p/'catalog.json').write_text('{}')
   os.environ['PANEL_ORIGIN']='https://vpn.example.com:9444'
   source=(ROOT/'panel/app.py').read_text().replace("Path('/var/lib/allvpn-panel')",f'Path({tmp!r})')
   m=types.ModuleType('testpanel');m.__file__=str(p/'app.py');exec(compile(source,m.__file__,'exec'),m.__dict__);m.app.testing=True;c=m.app.test_client();base=os.environ['PANEL_ORIGIN'];h={'Origin':base}
   for url in ['/api/catalog','/api/files','/download/test.txt','/api/file/test.txt']:self.assertEqual(c.get(url,base_url=base).status_code,401)
   self.assertEqual(c.post('/api/login',base_url=base,headers={'Origin':'https://evil.example'},json={}).status_code,403)
   r=c.post('/api/login',base_url=base,headers=h,json={'username':'sabi','password':'local-test-previous'});self.assertEqual(r.status_code,200);self.assertIn('HttpOnly',r.headers['Set-Cookie']);self.assertIn('Secure',r.headers['Set-Cookie'])
   self.assertEqual(c.get('/download/test.txt',base_url=base).data,b'test');self.assertEqual(c.get('/download/auth.json',base_url=base).status_code,404)
   self.assertEqual(c.post('/api/password',base_url=base,headers=h,json={}).status_code,403)
   h['X-CSRF-Token']=c.get('/api/session',base_url=base).json['csrf']
   self.assertEqual(c.post('/api/password',base_url=base,headers=h,json={'current':'local-test-previous','new':'1234567'}).status_code,400)
   self.assertEqual(c.post('/api/password',base_url=base,headers=h,json={'current':'local-test-previous','new':'12345678'}).status_code,200)
   self.assertEqual(c.get('/api/catalog',base_url=base).status_code,401)
if __name__=='__main__':unittest.main()
