import os,json,time,secrets,threading,hmac,hashlib
from datetime import timedelta,datetime,timezone
from pathlib import Path
from functools import wraps
from flask import Flask,request,session,jsonify,send_file,redirect
from werkzeug.security import generate_password_hash,check_password_hash
ROOT=Path('/opt/allvpn-panel'); DATA=Path('/var/lib/allvpn-panel')
ORIGIN=os.environ['PANEL_ORIGIN']
app=Flask(__name__,static_folder=str(ROOT/'static'),static_url_path='/static')
auth=json.loads((DATA/'auth.json').read_text())
app.config.update(SECRET_KEY=auth['session_key'],SESSION_COOKIE_NAME='allvpn_session',SESSION_COOKIE_SECURE=True,SESSION_COOKIE_HTTPONLY=True,SESSION_COOKIE_SAMESITE='Strict',PERMANENT_SESSION_LIFETIME=timedelta(hours=8),MAX_CONTENT_LENGTH=8192)
lock=threading.Lock(); attempts={}
def current_auth():return json.loads((DATA/'auth.json').read_text())
def logged():return session.get('authenticated') is True and session.get('version')==current_auth()['version']
def private(fn):
 @wraps(fn)
 def wrapped(*a,**kw):
  if not logged():return jsonify(error='ابتدا وارد پنل شوید.'),401
  return fn(*a,**kw)
 return wrapped
@app.after_request
def headers(r):
 r.headers['Cache-Control']='no-store, private, max-age=0'
 r.headers['Pragma']='no-cache'
 r.headers['X-Content-Type-Options']='nosniff'
 r.headers['X-Frame-Options']='DENY'
 r.headers['Referrer-Policy']='no-referrer'
 r.headers['Permissions-Policy']='camera=(), microphone=(), geolocation=()'
 r.headers['Content-Security-Policy']="default-src 'self'; script-src 'self'; style-src 'self'; font-src 'self'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'; object-src 'none'"
 return r
@app.before_request
def protect():
 if request.method in ('POST','PUT','DELETE'):
  if request.headers.get('Origin')!=ORIGIN:return jsonify(error='درخواست از مبدأ مجاز نیست.'),403
  if request.path!='/api/login' and not hmac.compare_digest(request.headers.get('X-CSRF-Token',''),session.get('csrf','MISSING')):return jsonify(error='صفحه را دوباره باز کنید.'),403
@app.get('/')
def index():return send_file(ROOT/'index.html') if logged() else redirect('/login')
@app.get('/login')
def login_page():return redirect('/') if logged() else send_file(ROOT/'login.html')
@app.post('/api/login')
def login():
 data=request.get_json(silent=True) or {};ip=request.headers.get('X-Real-IP',request.remote_addr);now=time.time()
 with lock:
  if len(attempts)>2000:
   for k in list(attempts):
    if now-attempts[k][-1]>900:attempts.pop(k,None)
  q=[x for x in attempts.get(ip,[]) if now-x<900];attempts[ip]=q
  if len(q)>=10:return jsonify(error='تعداد تلاش‌ها زیاد است؛ ۱۵ دقیقه بعد دوباره امتحان کنید.'),429
  q.append(now)
 a=current_auth();pw=str(data.get('password',''))[:512]
 valid=check_password_hash(a['password_hash'],pw)
 if not(valid and hmac.compare_digest(str(data.get('username','')),a['username'])):return jsonify(error='نام کاربری یا رمز درست نیست.'),401
 with lock:attempts.pop(ip,None)
 session.clear();session.permanent=True;session.update(authenticated=True,version=a['version'],csrf=secrets.token_urlsafe(24))
 return jsonify(ok=True)
@app.post('/api/logout')
@private
def logout():session.clear();return jsonify(ok=True)
@app.get('/api/session')
@private
def who():return jsonify(username=current_auth()['username'],csrf=session['csrf'])
@app.post('/api/password')
@private
def password():
 d=request.get_json(silent=True) or {};a=current_auth();new=str(d.get('new',''))
 if not check_password_hash(a['password_hash'],str(d.get('current',''))):return jsonify(error='رمز فعلی درست نیست.'),400
 if not 8<=len(new)<=256:return jsonify(error='رمز تازه باید ۸ تا ۲۵۶ نویسه باشد.'),400
 with lock:
  a['password_hash']=generate_password_hash(new);a['version']=secrets.token_hex(12)
  t=DATA/'auth.tmp';t.write_text(json.dumps(a));os.chmod(t,0o600);t.replace(DATA/'auth.json')
 session.clear();return jsonify(ok=True)
@app.get('/api/catalog')
@private
def catalog():return send_file(DATA/'catalog.json',mimetype='application/json')
@app.get('/api/status')
@private
def status():
 p=DATA/'status.json'
 return send_file(p,mimetype='application/json') if p.exists() else jsonify(updated_at=None,services={},note='هنوز بررسی نشده')
def manifest():return json.loads((DATA/'files.json').read_text())
def entry(name):return next((f for f in manifest() if f['name']==name),None)
@app.get('/api/files')
@private
def files():return jsonify(manifest())
@app.get('/download/<name>')
@private
def download(name):
 e=entry(name)
 if not e:return jsonify(error='فایل یافت نشد.'),404
 p=DATA/'files'/e['name']
 if not p.is_file():return jsonify(error='فایل در دسترس نیست.'),404
 return send_file(p,as_attachment=True,download_name=e['name'],max_age=0)
@app.get('/api/file/<name>')
@private
def preview(name):
 e=entry(name)
 if not e or not e.get('text'):return jsonify(error='فقط فایل‌های متنی پیش‌نمایش دارند.'),400
 p=DATA/'files'/e['name']
 if p.stat().st_size>524288:return jsonify(error='فایل برای پیش‌نمایش بزرگ است؛ دانلود کنید.'),413
 return jsonify(name=e['name'],text=p.read_text())
@app.errorhandler(500)
def fail(e):return jsonify(error='خطای داخلی؛ دوباره تلاش کنید.'),500
