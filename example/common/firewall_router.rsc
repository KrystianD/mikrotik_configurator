:do {
	/ip firewall filter
	remove [find chain=input]
	remove [find chain=forward action!=passthrough]
	remove [find chain=output]

	remove [find chain=icmp]
	remove [find jump-target="user-input"]
	remove [find jump-target="user-forward"]
	remove [find jump-target="user-output"]

	remove [find chain="core-icmp"]

	/ip firewall nat
	remove [find chain=srcnat]
	remove [find chain=dstnat]
} on-error={}

/ip firewall filter
# INPUT
add chain=input action=accept comment="accept established,related,untracked" connection-state=established,related,untracked
add chain=input action=drop   comment="drop connection-state=invalid"        connection-state=invalid
add chain=input action=drop   comment="drop banned" src-address-list=bans
add chain=input action=jump   comment="check ICMP" jump-target="core-icmp"   protocol=icmp
add chain=input action=accept comment="accept SSH and HTTP (LAN only)"   in-interface-list=LAN protocol=tcp  dst-port=22,80
add chain=input action=accept comment="accept WinBox and API (LAN only)" in-interface-list=LAN protocol=tcp  dst-port=8291,8728
add chain=input action=accept comment="accept DNS and DHCP (LAN only)"   in-interface-list=LAN protocol=udp  dst-port=53,67,68
# add chain=input action=accept comment="accept to local loopback (for CAPsMAN)" dst-address=127.0.0.1

add chain=input action=jump jump-target="user-input" comment="forward to user-input"
add chain=input action=drop   comment="drop all not coming from LAN" in-interface-list=!LAN
add chain=input action=drop   comment="drop all other"

# FORWARD
add chain=forward action=fasttrack-connection comment="fasttrack"              connection-state=established,related
add chain=forward action=accept comment="accept established,related,untracked" connection-state=established,related,untracked
add chain=forward action=drop   comment="drop connection-state=invalid"        connection-state=invalid
add chain=forward action=drop   comment="drop banned" src-address-list=bans
add chain=forward action=jump   comment="check ICMP" jump-target="core-icmp" src-address-list=lan in-interface-list=LAN protocol=icmp
add chain=forward action=accept comment="accept DSTNATed from WAN to LAN"      connection-state=new     in-interface-list=WAN out-interface-list=LAN dst-address-list=lan connection-nat-state=dstnat
add chain=forward action=accept comment="accept all from LAN to WAN"           connection-state=new     in-interface-list=LAN src-address-list=lan out-interface-list=WAN
add chain=forward action=accept comment="accept all between LAN interfaces"    connection-state=new     in-interface-list=LAN src-address-list=lan out-interface-list=LAN dst-address-list=lan
# add chain=forward action=accept comment="accept in ipsec policy" ipsec-policy=in,ipsec
# add chain=forward action=accept comment="accept out ipsec policy" ipsec-policy=out,ipsec

add chain=forward action=jump jump-target="user-forward" comment="forward to user-forward"
add chain=forward action=drop                            comment="drop all other"

# OUTPUT
add chain=output action=jump jump-target="user-output" comment="forward to user-output"

add chain="core-icmp" protocol=icmp icmp-options=0:0  action=accept comment="echo reply"
add chain="core-icmp" protocol=icmp icmp-options=3:0  action=accept comment="net unreachable"
add chain="core-icmp" protocol=icmp icmp-options=3:1  action=accept comment="host unreachable"
add chain="core-icmp" protocol=icmp icmp-options=3:4  action=accept comment="host unreachable fragmentation required"
add chain="core-icmp" protocol=icmp icmp-options=8:0  action=accept comment="allow echo request"
add chain="core-icmp" protocol=icmp icmp-options=11:0 action=accept comment="allow time exceed"
add chain="core-icmp" protocol=icmp icmp-options=12:0 action=accept comment="allow parameter bad"
add chain="core-icmp" action=drop                                   comment="deny all other types"

/ip firewall nat
add chain=srcnat action=masquerade comment="masquerade to WAN" ipsec-policy=out,none out-interface-list=WAN

add chain=srcnat action=jump jump-target="user-srcnat" comment="forward to user-srcnat"
add chain=dstnat action=jump jump-target="user-dstnat" comment="forward to user-dstnat"

# Address lists
/ip firewall address-list
add list=bogons address=0.0.0.0/8       comment="Self-Identification [RFC 3330]"
add list=bogons address=127.0.0.0/8     comment="Loopback [RFC 3330]"
add list=bogons address=10.0.0.0/8      comment="Private[RFC 1918] - CLASS A" disabled=no
add list=bogons address=172.16.0.0/12   comment="Private[RFC 1918] - CLASS B" disabled=no
add list=bogons address=192.168.0.0/16  comment="Private[RFC 1918] - CLASS C" disabled=yes
add list=bogons address=169.254.0.0/16  comment="Link Local [RFC 3330]"
add list=bogons address=192.88.99.0/24  comment="6to4 Relay Anycast [RFC 3068]"
add list=bogons address=198.18.0.0/15   comment="NIDB Testing"
add list=bogons address=192.0.2.0/24    comment="Reserved - IANA - TestNet1"
add list=bogons address=198.51.100.0/24 comment="Reserved - IANA - TestNet2"
add list=bogons address=203.0.113.0/24  comment="Reserved - IANA - TestNet3"
add list=bogons address=224.0.0.0/4     comment="MC, Class D, IANA"           disabled=no
{% call register_cleanup() %}
/ip firewall address-list remove [find list=bogons]
{% endcall %}
