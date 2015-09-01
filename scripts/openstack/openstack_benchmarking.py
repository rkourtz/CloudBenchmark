#!/usr/bin/python
# Purpose:  The functionality is really provided by the 
# python client APIs distributed by the OpenStack project.
# The script is meant to be used to automate the NuoDB benchmarking
# suite by creating VMs within OpenStack and injecting a cloudinit 
# script. The cloudinit process will take care of mounting the testing 
# volume an obtaining all the required software required to successfully
# run the benchmarking suite.

from keystoneclient.auth.identity import v2
from keystoneclient               import session
from novaclient.v2                import client  as nova_client
import argparse
import os
import sys
import time

class Block_Device(object):
    # This class is an attempt to abstract the block device map required
    # by the nova.servers.create object to sucessfully create a working VM
    # programmatically. This is currently a work in progress and not in use
    # yet 8/31/2015.

    def __init__(self, size, source_type, delete_on_termination=True, bootable=False, **kwargs):
        self.dev_map = { 'delete_on_termination' : delete_on_termination,
                         'size' : size,
                         'destination_type' : 'volume',
                         'source_type' : None,
                       }
        if bootable:
            self.dev_map.setadefault('boot_index', '0')
        else:
            self.boot_index = '1'

    def get_map(self):
        return self.dev_map

            
def get_session(): 
    # The credentials needed are those setup for each user within the Keystone server.
    # The minimum credentials needed are auth_url, username, api_key (i.e. password), and
    # the name or ID of the tenant space.  The tenant space is the project under which you 
    # would like the action to take place.  Other cli tools provided by the OpenStack project
    # expects to find these credentials from the user's environment. This method avoids providing 
    # a large list of cli arguments to control the current action. This script will try and 
    # detect this from the environment as well.
    # The authentication requires a minimal set of values to be supplied. 
    required_evn_vars = ['OS_AUTH_URL', 'OS_USERNAME', 'OS_PASSWORD', 'OS_TENANT_ID']

    if set.issubset(set(required_evn_vars),set(os.environ)):
        # Process the environment variables.
        creds = {k.split('_',1)[1].lower(): os.environ[k] for k in required_evn_vars if k in os.environ}
    else:
        print('Missing credentials. Please set environment variablies as described in OpenStack manual.')
        print('\thttp://docs.openstack.org/cli-reference/content/cli_openrc.html')
        sys.exit(1)

    auth = v2.Password(**creds)
    return session.Session(auth=auth)

if __name__ == '__main__':
    # TODO: handle command line over rides for the OpenStack environment variables sourced 
    # from the openstackrc.sh file that can be generated from the horizon web UI.
    # Authenticate the nova client for all actions.
    parser = argparse.ArgumentParser(description='Automates creating as many VMs as specified and executing the NuoDB benchmark suite on these VMs.')
    parser.add_argument('-c', '--count', default=1, help='Number of simultaneous VMs to create and benchmark. Defaults to 1')
    parser.add_argument('-f', '--flavor', default='m1.medium', help='Override the default VM sizing.  Defaults to m1.medium')
    parser.add_argument('--key-name', default=None, help='Provide the key name registered with OpenStack for your user.')
    parser.add_argument('instance_name', default='benchmark_test', help='The name of the VM created. The count will be appended if there count is greater than the default')
    args = parser.parse_args()

    nova = nova_client.Client(session=get_session())
    floating_ip_pool = nova.floating_ip_pools.find(name='ext-net')

    if len(nova.floating_ips.list(all_tenants=True)) > 0:
        for ip in nova.floating_ips.list(all_tenants=True):
            if not ip.instance_id:
                floating_ip = ip
                break
    else:
        floating_ip = nova.floating_ips.create(pool=floating_ip_pool.name)
    
    # Set up some data items that will direct VM instance creation.
    image      = nova.images.find(name='CentOS 7 64 bit')
    flavor     = nova.flavors.find(name=args.flavor)
    network    = nova.networks.find(label='Phils_benchmarking_net')

    if args.key_name:
        key = nova.keypairs.find(name=args.key_name)

    # The cloudinit script is expected to reside in the current working directory
    # of this script.
    cloud_init = open(os.path.join(os.getcwd(),'cloudinit.sh'), 'r')
    
    bd_map = [{'boot_index'            : '0',
               'destination_type'      : 'volume',
               'delete_on_termination' : True,
               'source_type'           : 'image',
               'uuid'                  : image.id, 
               'volume_size'           : '40'},
              {'boot_index'            : '1',
               'destination_type'      : 'volume',
               'delete_on_termination' : True,
               'source_type'           : 'blank',
               'volume_size'           : '50'}]
    
    vm     = {'flavor'                  : flavor.id,
              'block_device_mapping_v2' : bd_map,
              'image'                   : image.id,
              'key_name'                : key.name,
              'meta'                    : {'image_name' : image.name},
              'min_count'               : 1,
              'max_count'               : args.count,
              'name'                    : args.instance_name,
              'nics'                    : [{ 'net-id' : network.id}],
              'userdata'                : cloud_init} 
    
    server   = nova.servers.create(**vm)
    instance = nova.servers.get(server.id)
    if args.count > 1:
        sys.stdout.write('Building VMs ')
    else:
        sys.stdout.write('Building VM ')
 
    while instance.status == 'BUILD':
        time.sleep(1)
        instance = nova.servers.get(server.id)
        sys.stdout.write('.')
        sys.stdout.flush()
    
    instance.add_floating_ip(floating_ip)
    print('\nStatus: {0}'.format(instance.status))
