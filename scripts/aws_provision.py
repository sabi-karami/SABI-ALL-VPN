#!/usr/bin/env python3
"""Optional AWS provisioning. Uses boto3's standard credential chain, never embedded keys."""
import argparse,base64,getpass,ipaddress,json,os,re,secrets,time,sys,urllib.request
from pathlib import Path
import boto3
from botocore.exceptions import ClientError
VERSION='v1.0.0-beta.4'
REPO='sabi-karami/SABI-ALL-VPN'
parser=argparse.ArgumentParser();parser.add_argument('--region');parser.add_argument('--state');parser.add_argument('--resume',action='store_true');parser.add_argument('--delete',action='store_true');args=parser.parse_args()
path=Path(args.state).expanduser() if args.state else Path.home()/'.local/state/sabi-allvpn/aws-state.json';path.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
s=json.loads(path.read_text()) if path.exists() else {};region=s.get('region') or args.region or os.environ.get('AWS_REGION') or 'us-east-2'
session=boto3.Session(region_name=region);ec2=session.client('ec2');iam=session.client('iam');ssm=session.client('ssm')
def save():
 tmp=path.with_suffix('.tmp');tmp.write_text(json.dumps(s,indent=2));tmp.chmod(0o600);tmp.replace(path)
def wait_instance_profile():
 for _ in range(24):
  try:
   p=iam.get_instance_profile(InstanceProfileName=s['profile'])['InstanceProfile']
   if p.get('Roles'):time.sleep(15);return
  except ClientError:pass
  time.sleep(5)
 raise RuntimeError('IAM instance profile not ready; rerun --resume')
def send(script):return ssm.send_command(InstanceIds=[s['instance']],DocumentName='AWS-RunShellScript',Parameters={'commands':[script],'executionTimeout':['1800']})['Command']['CommandId']
def read(cid):
 for _ in range(180):
  try:r=ssm.get_command_invocation(CommandId=cid,InstanceId=s['instance'])
  except ssm.exceptions.InvocationDoesNotExist:time.sleep(3);continue
  if r['Status'] not in ['Pending','InProgress','Delayed']:return r
  time.sleep(3)
 raise RuntimeError('SSM command still running; inspect command ID '+cid)
def cleanup():
 if not s:raise SystemExit('No state file; nothing deleted.')
 print('Will terminate ONLY resources named in this state file:',path)
 print(json.dumps({k:s.get(k) for k in ['name','region','instance','eip','sg','role','profile']},indent=2))
 if input('Type DELETE to confirm: ')!='DELETE':raise SystemExit('Cancelled')
 if s.get('instance'):
  ec2.terminate_instances(InstanceIds=[s['instance']]);ec2.get_waiter('instance_terminated').wait(InstanceIds=[s['instance']])
 if s.get('eip_alloc'):ec2.release_address(AllocationId=s['eip_alloc'])
 if s.get('sg'):ec2.delete_security_group(GroupId=s['sg'])
 if s.get('profile'):
  try:iam.remove_role_from_instance_profile(InstanceProfileName=s['profile'],RoleName=s['role'])
  except ClientError:pass
  iam.delete_instance_profile(InstanceProfileName=s['profile'])
 if s.get('role'):
  try:iam.delete_role_policy(RoleName=s['role'],PolicyName='bootstrap-secret')
  except ClientError:pass
  iam.detach_role_policy(RoleName=s['role'],PolicyArn='arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore');iam.delete_role(RoleName=s['role'])
 if s.get('parameter'):
  try:ssm.delete_parameter(Name=s['parameter'])
  except ClientError:pass
 s['deleted']=True;save();print('AWS resources deleted. Cloudflare DNS records are NOT deleted; remove only this deployment\'s records manually.');sys.exit(0)
if args.delete:cleanup()
if s and not args.resume:raise SystemExit('State already exists. Use --resume, --delete, or --state /path/to/new-state.json. No additional resources created.')
if s.get('deleted'):raise SystemExit('State marks a deleted deployment. Use a new state path.')
identity=session.client('sts').get_caller_identity();print('AWS account:',identity['Account'],'region:',region)
if not s:
 print('BILLABLE: one EC2, 30-GiB EBS, one public IPv4/EIP, and outbound traffic. No automatic spending cap. No fixed price is promised.')
 print('Use a fresh dedicated instance. Region/SCP/quota restrictions remain enforced.')
 vpcs=ec2.describe_vpcs(Filters=[{'Name':'is-default','Values':['true']}])['Vpcs']
 if not vpcs:raise SystemExit('Default VPC required. Create a public VPC/subnet yourself or use existing-server mode. No networking changes made.')
 subnetlist=ec2.describe_subnets(Filters=[{'Name':'vpc-id','Values':[vpcs[0]['VpcId']]},{'Name':'map-public-ip-on-launch','Values':['true']}])['Subnets']
 if not subnetlist:raise SystemExit('No public default subnet found.')
 zone=input('Cloudflare zone, e.g. example.com: ').strip().lower();prefix=input('Subdomain prefix [allvpn]: ').strip() or 'allvpn'
 if not re.fullmatch(r'(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}',zone):raise SystemExit('Invalid zone')
 if not re.fullmatch(r'[a-z0-9](?:[a-z0-9-]{0,38}[a-z0-9])?',prefix):raise SystemExit('Invalid prefix')
 name='sabi-allvpn-'+time.strftime('%Y%m%d')+'-'+secrets.token_hex(3)
 typ=input('Instance type [t3.small]: ').strip() or 't3.small'
 info=ec2.describe_instance_types(InstanceTypes=[typ])['InstanceTypes'][0]
 if 'x86_64' not in info['ProcessorInfo']['SupportedArchitectures'] or info['MemoryInfo']['SizeInMiB']<2048:raise SystemExit('Choose x86_64 with at least 2 GiB RAM.')
 admin=input('IPv4 CIDR allowed for panel 9444 (e.g. YOUR.IP/32) [0.0.0.0/0]: ').strip() or '0.0.0.0/0';ipaddress.IPv4Network(admin)
 pptp='yes' if input('Enable INSECURE PPTP? [no]: ').strip()=='yes' else 'no'
 plain='yes' if input('Expose unencrypted SOCKS/HTTP? [no]: ').strip()=='yes' else 'no'
 if input('Type CREATE to accept charges and provision: ')!='CREATE':raise SystemExit('Cancelled')
 s={'name':name,'region':region,'account':identity['Account'],'type':typ,'role':name+'-role','profile':name+'-profile','vpc':vpcs[0]['VpcId'],'subnet':subnetlist[0]['SubnetId'],'parameter':'/sabi-allvpn/'+name+'/bootstrap','admin_cidr':admin,'cfg':{'ZONE':zone,'DOMAIN':prefix+'.'+zone,'CDN':prefix+'-cdn.'+zone,'DNS_NS':prefix+'-ns.'+zone,'DNS_TUNNEL':prefix+'-t.'+zone,'PANEL_USER':'sabi','REALITY_SNI':'www.speedtest.net','ENABLE_PPTP':pptp,'ENABLE_PLAIN_PROXY':plain,'DNS_MODE':'cloudflare','REGION':region},'token':'request-'+secrets.token_hex(16)};save()
if s['account']!=identity['Account']:raise SystemExit('Credential account differs from deployment state.')
if s.get('launched'):
 print('Already launched. No new resources created.');print('Panel: https://'+s['cfg']['DOMAIN']+':9444');print('Use SSM: sudo tail -f /var/log/sabi-allvpn-install.log');sys.exit(0)
# Token is requested only in the local terminal and briefly placed in Parameter Store SecureString.
token=getpass.getpass('Cloudflare DNS-edit + Zone-read + Zone-settings-read token (hidden): ').strip()
if not token:raise SystemExit('Token required; no token stored in state file or EC2 user-data.')
try:
 tags=[{'Key':'Name','Value':s['name']},{'Key':'ManagedBy','Value':'sabi-allvpn'}]
 if not s.get('role_ready'):
  try:iam.create_role(RoleName=s['role'],AssumeRolePolicyDocument=json.dumps({'Version':'2012-10-17','Statement':[{'Effect':'Allow','Principal':{'Service':'ec2.amazonaws.com'},'Action':'sts:AssumeRole'}]}),Tags=tags)
  except iam.exceptions.EntityAlreadyExistsException:pass
  iam.attach_role_policy(RoleName=s['role'],PolicyArn='arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore')
  try:iam.create_instance_profile(InstanceProfileName=s['profile'])
  except iam.exceptions.EntityAlreadyExistsException:pass
  p=iam.get_instance_profile(InstanceProfileName=s['profile'])['InstanceProfile']
  if not p.get('Roles'):iam.add_role_to_instance_profile(InstanceProfileName=s['profile'],RoleName=s['role'])
  s['role_ready']=True;save()
 paramarn=f'arn:aws:ssm:{region}:{s["account"]}:parameter{s["parameter"]}'
 iam.put_role_policy(RoleName=s['role'],PolicyName='bootstrap-secret',PolicyDocument=json.dumps({'Version':'2012-10-17','Statement':[{'Effect':'Allow','Action':'ssm:GetParameter','Resource':paramarn}]}))
 if not s.get('sg'):
  existing=ec2.describe_security_groups(Filters=[{'Name':'group-name','Values':[s['name']]},{'Name':'vpc-id','Values':[s['vpc']]}])['SecurityGroups']
  s['sg']=existing[0]['GroupId'] if existing else ec2.create_security_group(GroupName=s['name'],Description='SABI ALLVPN dedicated listeners',VpcId=s['vpc'],TagSpecifications=[{'ResourceType':'security-group','Tags':tags}])['GroupId'];save()
 tcp=[80,443,992,1194,2053,2083,2087,2096,3443,4433,4443,5555,7443,8388,8443,9443,10443,11443]
 udp=[53,443,500,1194,4443,4500,8388,8443,10443,51820,51821]
 if s['cfg']['ENABLE_PPTP']=='yes':tcp.append(1723)
 if s['cfg']['ENABLE_PLAIN_PROXY']=='yes':tcp.append(1080)
 rules=[{'IpProtocol':proto,'FromPort':p,'ToPort':p,'IpRanges':[{'CidrIp':'0.0.0.0/0'}]} for proto,ports in [('tcp',tcp),('udp',udp)] for p in ports]
 rules += [{'IpProtocol':'tcp','FromPort':p,'ToPort':p,'IpRanges':[{'CidrIp':s['admin_cidr']}]} for p in [22,9444]]
 if s['cfg']['ENABLE_PPTP']=='yes':rules.append({'IpProtocol':'47','IpRanges':[{'CidrIp':'0.0.0.0/0'}]})
 for rule in rules:
  try:ec2.authorize_security_group_ingress(GroupId=s['sg'],IpPermissions=[rule])
  except ClientError as e:
   if e.response['Error']['Code']!='InvalidPermission.Duplicate':raise
 if not s.get('instance'):
  ami=ssm.get_parameter(Name='/aws/service/canonical/ubuntu/server/24.04/stable/current/amd64/hvm/ebs-gp3/ami-id')['Parameter']['Value']
  wait_instance_profile()
  user_data='#!/bin/bash\nset -e\nsystemctl enable --now snap.amazon-ssm-agent.amazon-ssm-agent.service || (snap install amazon-ssm-agent --classic && systemctl enable --now snap.amazon-ssm-agent.amazon-ssm-agent.service)\n'
  r=ec2.run_instances(ClientToken=s['token'],ImageId=ami,InstanceType=s['type'],MinCount=1,MaxCount=1,SubnetId=s['subnet'],SecurityGroupIds=[s['sg']],IamInstanceProfile={'Name':s['profile']},MetadataOptions={'HttpTokens':'required'},BlockDeviceMappings=[{'DeviceName':'/dev/sda1','Ebs':{'VolumeSize':30,'VolumeType':'gp3','Encrypted':True,'DeleteOnTermination':True}}],UserData=user_data,TagSpecifications=[{'ResourceType':'instance','Tags':tags},{'ResourceType':'volume','Tags':tags}])
  s['instance']=r['Instances'][0]['InstanceId'];save()
 ec2.get_waiter('instance_running').wait(InstanceIds=[s['instance']])
 if not s.get('eip_alloc'):
  a=ec2.describe_addresses(Filters=[{'Name':'tag:Name','Values':[s['name']]}])['Addresses']
  a=a[0] if a else ec2.allocate_address(Domain='vpc',TagSpecifications=[{'ResourceType':'elastic-ip','Tags':tags}]);s.update(eip_alloc=a['AllocationId'],eip=a['PublicIp']);save()
 ec2.associate_address(AllocationId=s['eip_alloc'],InstanceId=s['instance'])
 ec2.modify_instance_attribute(InstanceId=s['instance'],SourceDestCheck={'Value':False})
 for _ in range(90):
  rows=ssm.describe_instance_information(Filters=[{'Key':'InstanceIds','Values':[s['instance']]}])['InstanceInformationList']
  if rows and rows[0]['PingStatus']=='Online':break
  time.sleep(10)
 else:raise RuntimeError('SSM did not become ready. Resources remain; use --resume or --delete.')
 cfg={**s['cfg'],'IP':s['eip'],'INSTANCE_ID':s['instance']}
 ssm.put_parameter(Name=s['parameter'],Value=json.dumps({'config':cfg,'cf_token':token}),Type='SecureString',Overwrite=True)
 script="""set -e
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq; apt-get install -y -qq python3-boto3 curl ca-certificates
umask 077
mkdir -p /etc/sabi-allvpn
python3 - <<'PY'
import boto3,json,os
from pathlib import Path
r=boto3.client('ssm',region_name=REGION).get_parameter(Name=PARAM,WithDecryption=True)
a=json.loads(r['Parameter']['Value']);p=Path('/etc/sabi-allvpn');(p/'input.json').write_text(json.dumps(a['config']));(p/'cloudflare.token').write_text(a['cf_token']);os.chmod(p/'input.json',0o600);os.chmod(p/'cloudflare.token',0o600)
PY
curl -fsSL BOOTSTRAP -o /root/sabi-bootstrap.sh
bash /root/sabi-bootstrap.sh --noninteractive
""".replace('REGION',repr(region)).replace('PARAM',repr(s['parameter'])).replace('BOOTSTRAP',f'https://raw.githubusercontent.com/{REPO}/{VERSION}/bootstrap.sh')
 cid=send(script);s['command']=cid;save();r=read(cid)
 if r['Status']!='Success':raise RuntimeError('Bootstrap failed; inspect SSM command '+cid+' (no keys are printed here).')
 s['launched']=True;save()
 ssm.delete_parameter(Name=s['parameter']);iam.delete_role_policy(RoleName=s['role'],PolicyName='bootstrap-secret')
 print('AWS deployment launched. State:',path)
 print('Panel: https://'+cfg['DOMAIN']+':9444 (available only after installation completes)')
 print('AWS SSM Session Manager: sudo tail -f /var/log/sabi-allvpn-install.log')
 print('Credentials (private): sudo cat /root/allvpn/panel-access.txt')
 print('Private ZIP: /root/allvpn/export/allvpn-private.zip')
except Exception as e:
 print('Provisioning stopped:',type(e).__name__,str(e)[:350],file=sys.stderr)
 print('Created resources may still incur charges. State:',path,file=sys.stderr)
 print('Use --resume; or --delete with this same state file after review.',file=sys.stderr)
 raise SystemExit(1)
finally:
 # Always remove temporary cloud token, including on failed bootstrap. Local certbot credential remains on the instance for renewal.
 try:ssm.delete_parameter(Name=s['parameter'])
 except Exception:pass
 try:iam.delete_role_policy(RoleName=s['role'],PolicyName='bootstrap-secret')
 except Exception:pass
