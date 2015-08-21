bootstrap = <<SCRIPT
sudo yum install -y https://dl.fedoraproject.org/pub/epel/epel-release-latest-6.noarch.rpm
sudo yum -y install gcc gcc-c++ python-devel kernel-headers libffi-devel openssl-devel
SCRIPT

# -*- mode: ruby -*-
# vi: set ft=ruby :

# Vagrantfile API/syntax version. Don't touch unless you know what you're doing!
VAGRANTFILE_API_VERSION = "2"

Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|
  config.vm.box = "CentOS/6.6"

  config.vm.box_url = "http://opscode-vm-bento.s3.amazonaws.com/vagrant/virtualbox/opscode_centos-6.6_chef-provisionerless.box"

  # config.vm.network :forwarded_port, guest: 80, host: 8080
  #config.vm.network :public_network

  config.ssh.forward_agent = true

  #config.vm.synced_folder "/Users/rkourtz/workspace", "/workspace"

  config.vm.provision "shell", inline: bootstrap

  config.vm.provider :virtualbox do |vb|
    # Don't boot with headless mode
    # vb.gui = true
    vb.customize ["modifyvm", :id, "--memory", "2048"]
  end
end
