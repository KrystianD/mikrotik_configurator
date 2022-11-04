/system identity set name="MT"

/interface bridge
add name="bridge"

/interface ethernet
set [ find default-name=sfp1 ] disabled=yes

/interface list
add name=LAN
add name=WAN

/ip address
add address=192.168.1.1/24 interface="bridge"

/interface list member
add interface="bridge" list=LAN

/interface bridge port
add bridge="bridge" interface=ether2
add bridge="bridge" interface=ether3
add bridge="bridge" interface=ether4
add bridge="bridge" interface=ether5
add bridge="bridge" interface=ether6
add bridge="bridge" interface=ether7
add bridge="bridge" interface=ether8
add bridge="bridge" interface=ether9
add bridge="bridge" interface=ether10

/user set admin password="{{ admin_pass }}"

#######################
# SSH
#######################
{{ load_file("host-keys/ssh_host_private_key_dsa", "ssh_host_private_key_dsa.txt") }}
{{ load_file("host-keys/ssh_host_private_key_rsa", "ssh_host_private_key_rsa.txt") }}
/ip ssh import-host-key private-key-file=ssh_host_private_key_dsa.txt
/ip ssh import-host-key private-key-file=ssh_host_private_key_rsa.txt

{{ load_file("~/.ssh/id_rsa.pub", "pcl_id_rsa.pub.txt") }}
/user ssh-keys import user=admin public-key-file=pcl_id_rsa.pub.txt

