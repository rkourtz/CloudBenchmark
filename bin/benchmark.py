#!/usr/bin/python


####
# https://s3.amazonaws.com/nuodb-rackspace/benchmark
####

#### TODO: Set "platform" variable for Openstack and Azure

from argparse import ArgumentParser, RawDescriptionHelpFormatter
import datetime
import gspread
import inspect
import json
from oauth2client.client import SignedJwtAssertionCredentials
import os
import pwd
import subprocess
import sys
import tempfile
import time
import urllib2
import uuid as pyuuid

UUID_FILE="/benchmark.uuid"

DESCRIPTION="Runs shell scripts to benchmark a host, upload to Google Sheets"

class spreadsheet():
  def __init__(self):
    try:
      # PyInstaller creates a temp folder and stores path in _MEIPASS
      base_path = sys._MEIPASS
    except Exception:
      base_path = os.path.dirname(os.path.dirname(os.path.abspath(inspect.stack()[0][1])))
    cred_file = os.path.join(base_path, "data", "google-credentials.json")
    json_key = json.load(open(cred_file))
    scope = ['https://spreadsheets.google.com/feeds']
    credentials = SignedJwtAssertionCredentials(json_key['client_email'], json_key['private_key'], scope)
    self.gc = gspread.authorize(credentials)
    self.spreadsheet = self.gc.open_by_key("18zYLv6mJPLajG6FcuRwGq1yoM-X3GZQfazsGCu0mMgg")
    self.wks= self.spreadsheet.get_worksheet(0)
  
  def check_client(self):
    try:
      self.wks.acell('A1').value
    except Exception:
      self.__init__()
      
  def get_tests(self):
    self.check_client()
    return self.spreadsheet.worksheet("Tests").get_all_records()
  
  def get_host_row(self, host_uuid, column=1):
    def find_uuid(host_uuid, column):
      for count, uuid in enumerate(self.wks.col_values(column)):
        if host_uuid == uuid:
          return count + 1
      return None
    self.check_client()
    rownum = find_uuid(host_uuid, column)
    if rownum == None:
      self.append_line([host_uuid])
      return find_uuid(host_uuid, column)
    else:
      return rownum
    
  def update_cell(self, row, col, value=""):
    self.check_client()
    self.wks.update_cell(row, col, value)
    
  def append_line(self, line):
    self.check_client()
    return self.wks.append_row(line)
  
def execute_command(command, dir = None, sudo_user = None):
  delimiter = str(pyuuid.uuid4())
  if sudo_user != None and sudo_user != pwd.getpwuid( os.getuid() )[ 0 ]:
    command = "sudo -n -u %s %s" % (sudo_user, command)
  if dir != None:
    command = "cd %s && %s" % (dir, command)
  command = "echo %s; %s" % (delimiter, command)
  p = subprocess.Popen([command], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
  stdout, stderr = p.communicate()
  stdout = stdout.partition(delimiter)[2].strip()
  exit_code = p.returncode
  return (exit_code, stdout, stderr)

def get_metadata():
  global DEBUG
  def __crawl_data(url="http://169.254.169.254/latest/meta-data/"):
    data = {}
    for key in urllib2.urlopen(url).read().split("\n"):
      newurl = "".join([url, key.split("=")[0].strip()])
      if key[-1] == "/":
        data[key[0:-1]] = __crawl_data(newurl)
      else:
        try:
          data[key] = urllib2.urlopen(newurl).read()
        except urllib2.HTTPError, e:
          print "Can't get %s" % newurl
    return data

  def amazon():
    return("AWS", __crawl_data())
  
  def openstack():
    return ("openstack", __crawl_data())

  def google(url="http://metadata.google.internal/computeMetadata/v1/instance/?recursive=true", headers={"Metadata-Flavor": "Google"}):
    data = json.loads(urllib2.urlopen(urllib2.Request(url, headers=headers)).read())
    return ("GCE", data)
  
  urls = (
          ("http://169.254.169.254/openstack", openstack),
          ("http://169.254.169.254/latest/meta-data/", amazon),
          ("http://metadata.google.internal/", google),
          )
  for pair in urls:
    try:
      url, function = pair
      if DEBUG: print "Getting metadata from %s" % url
      data = urllib2.urlopen(url, timeout=10)
      if data.getcode() == 200:
        return function()
    except urllib2.URLError:
      pass
  return ("", {})
      
      
parser = ArgumentParser(description=DESCRIPTION, formatter_class=RawDescriptionHelpFormatter)
parser.add_argument("-g", "--test-groups", dest="testGroups", help="A comma separated list of the test groups to run. Default is \"all\".", default="*")
parser.add_argument("-n", "--notes", dest="notes", help="Helpful notes on this run to be added to the spreadsheet", default="")
parser.add_argument("-s", "--storage-backend", dest="storagebackend", help="What type of storage backend is being tested (IO1, GP2, Ceph)", default="")
parser.add_argument("--debug", dest="debug", help="Add verbose output", action="store_true")
args = parser.parse_args()
DEBUG=args.debug

if args.testGroups == "*":
  testGroups = args.testGroups
else:
  testGroups = args.testGroups.split(",")

web_endpoints=["https://spreadsheets.google.com"]
for web_endpoint in web_endpoints:
  print "Testing connectivity to '%s'" % web_endpoint
  try:
    pass
  except Exception, e:
    print "-- FAILED"
    print e
    sys.exit(2)

print "Patching cert file"
execute_command("sudo find /usr -type f -name cacerts.txt -exec chmod 644 {} \;")

print "Gathering host metadata..."
host_metadata={}
if os.path.exists(UUID_FILE):
  host_metadata["UUID"] = open(UUID_FILE).read()
else:
  host_metadata["UUID"] = str(pyuuid.uuid4())
  f = tempfile.NamedTemporaryFile(delete=False)
  f.write(host_metadata["UUID"])
  f.close()
  execute_command("cp %s %s" % (f.name, UUID_FILE), sudo_user="root")
  execute_command("chmod 644 %s" % (UUID_FILE), sudo_user="root")
  os.unlink(f.name)
host_metadata["HOSTNAME"] = execute_command("hostname")[1]
(platform, host_metadata["METADATA"]) = get_metadata()
if DEBUG: print "DEBUG: Host Medatata\n%s" % json.dumps(host_metadata['METADATA'], indent=2)
if platform == "GCE":
  host_metadata['instance-type'] = os.path.basename(host_metadata['METADATA']["machine-type"])
elif os.path.exists("/vagrant"):
  platform = "Vagrant"
  host_metadata['instance-type'] = "VAGRANT"
elif "instance-type" in host_metadata["METADATA"]:
  host_metadata['instance-type'] = host_metadata["METADATA"]['instance-type']
else:
  host_metadata['instance-type'] = ""
if DEBUG: print "Platform is %s" % platform
host_metadata["UNIXTIME"] = int(time.time())

print "Getting tests..."
ss = spreadsheet()
col=2 
def update_next_cell(value, tries=5):
  global col
  rownum = ss.get_host_row(host_uuid=host_metadata["UUID"])
  success = False
  while tries > 0 and not success:
    try:
      ss.update_cell(rownum, col, value)
      success = True
    except Exception, e:
      time.sleep(20)
      tries -= 1
  col += 1

def skip_next_cell():
  global col
  col += 1
  
for value in [host_metadata["UNIXTIME"], args.notes, platform, host_metadata["instance-type"], args.storagebackend, json.dumps(host_metadata["METADATA"])]:
  update_next_cell(value)

results = []
try:
  for test in ss.get_tests():
    if testGroups !="*" and isinstance(testGroups, list) and str(test["GROUP"]) not in testGroups:
      print "Skipping %s" % (test['TEST NAME'])
      skip_next_cell()
    else:
      print "Running %s" % (test['TEST NAME'])
      print "  %s" % test['COMMAND']
      if len(test['USER']) > 0:
        user=test['USER']
      else:
        user=None
      (exitcode, stdout, stderr) = execute_command(test['COMMAND'], sudo_user=user)
      if exitcode != 0:
        print "-- Failed!"
        print "#### BEGIN DUMP ####"
        print stdout
        print stderr
        print "#### END DUMP   ####"
        update_next_cell("--FAILEDCOMMAND--")
      else:
        print "-- %s" % stdout
        update_next_cell(stdout) 
  print "Complete"    
except KeyboardInterrupt:
  sys.exit(1)