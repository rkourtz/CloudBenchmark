#!/usr/bin/python


####
# https://s3.amazonaws.com/nuodb-rackspace/benchmark
####

#### TODO: Set "platform" variable for Openstack and Azure

from argparse import ArgumentParser, RawDescriptionHelpFormatter
import gspread
import inspect
import json
from oauth2client.client import SignedJwtAssertionCredentials
import os
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
  if sudo_user != None:
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
  def amazon_data(url="http://169.254.169.254/latest/meta-data/"):
    data = {}
    for key in urllib2.urlopen(url).read().split("\n"):
      newurl = "".join([url, key.split("=")[0].strip()])
      if key[-1] == "/":
        data[key[0:-1]] = amazon_data(newurl)
      else:
        try:
          data[key] = urllib2.urlopen(newurl).read()
        except urllib2.HTTPError, e:
          print "Can't get %s" % newurl
    return data

  def openstack_data(url="http://169.254.169.254/openstack/latest/meta_data.json"):
    data = json.loads(urllib2.urlopen(url).read())
    return data

  def google_data(url="http://metadata.google.internal/computeMetadata/v1/instance/?recursive=true", headers={"Metadata-Flavor": "Google"}):
    data = json.loads(urllib2.urlopen(urllib2.Request(url, headers=headers)).read())
    return data
  
  urls = {
          "http://169.254.169.254/latest/meta-data/": amazon_data,
          "http://169.254.169.254/openstack": openstack_data,
          "http://metadata.google.internal/": google_data,
          }
  metadata = {}
  for url in urls.keys():
    try:
      urllib2.urlopen(url, timeout=4).read()   
      metadata = urls[url]()
    except Exception, e:
      pass
  return metadata
      
      
parser = ArgumentParser(description=DESCRIPTION, formatter_class=RawDescriptionHelpFormatter)
parser.add_argument("-g", "--test-groups", dest="testGroups", help="A comma separated list of the test groups to run. Default is \"all\".", default="*")
parser.add_argument("-n", "--notes", dest="notes", help="Helpful notes on this run to be added to the spreadsheet", default="")
args = parser.parse_args()

if args.testGroups == "*":
  testGroups = args.testGroups
else:
  testGroups = args.testGroups.split(",")
  
package_installer=None
package_installers=["yum", "apt-get", "zypper"]
for installer in package_installers:
  if package_installer == None and execute_command("which %s" % installer)[0] == 0:
    package_installer = installer
if package_installer == None:
  print "Cannot determine the package install method."
  print "Tried: %s" % ", ".join(package_installers)
  print "Cannot continue."
  sys.exit(2)
elif package_installer == "apt-get":
  print "Refreshing repositories"
  (exitcode, stdout, stderr) = execute_command("apt-get -y update", sudo_user="root")

print "Testing for utilities..."
commands={
          'sysbench': {
           "yum": "https://dl.fedoraproject.org/pub/epel/6/x86_64/sysbench-0.4.12-5.el6.x86_64.rpm",
          },
          "iperf": {
            "yum": "https://dl.fedoraproject.org/pub/epel/6/x86_64/iperf-2.0.5-11.el6.x86_64.rpm",
          }
}
for command in commands.keys():
  if execute_command("which %s" % command)[0] != 0:
    print "Installing %s" % command
    install_command = "%s -y install %s" % (package_installer, command)
    (exitcode, stdout, stderr) = execute_command(install_command, sudo_user="root")
    if exitcode != 0 and package_installer in commands[command].keys():
      print "-- '%s' failed. Trying from %s" % (install_command, commands[command][package_installer])
      install_command = "%s -y install %s" % (package_installer, commands[command][package_installer])
      (exitcode, stdout, stderr) = execute_command(install_command, sudo_user="root")
    if exitcode != 0:
      print "-- '%s' failed. Cannot continue." % install_command
      print "ERROR DUMP"
      print stdout
      print stderr
      sys.exit(2)

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
host_metadata["METADATA"] = get_metadata()
if "instance-type" in host_metadata['METADATA']:
  platform = "AWS"
  host_metadata['instance-type'] = host_metadata['METADATA']['instance-type']
elif "machine-type" in host_metadata['METADATA']:
  platform = "GCE"
  host_metadata['instance-type'] = os.path.basename(host_metadata['METADATA']["machine-type"])
elif os.path.exists("/vagrant"):
  platform = "Vagrant"
  host_metadata['instance-type'] = "VAGRANT"
else:
  platform = ""
  host_metadata['instance-type'] = ""
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
  
for value in [host_metadata["UNIXTIME"], args.notes, platform, host_metadata["instance-type"], json.dumps(host_metadata["METADATA"])]:
  update_next_cell(value)

results = []
try:
  for test in ss.get_tests():
    if testGroups !="*" and isinstance(testGroups, list) and str(test["GROUP"]) not in testGroups:
      print "Skipping %s (%s)" % (test['TEST NAME'], test['COMMAND'])
      update_next_cell("--DISABLED--")
    else:
      print "Running %s (%s)" % (test['TEST NAME'], test['COMMAND'])
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