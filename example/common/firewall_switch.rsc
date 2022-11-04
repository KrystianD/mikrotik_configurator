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

# add chain=input action=accept comment="accept to local loopback (for CAPsMAN)" dst-address=127.0.0.1

add chain=input action=jump jump-target="user-input" comment="forward to user-input"
add chain=input action=drop   comment="drop all not coming from LAN" in-interface-list=!LAN
add chain=input action=drop   comment="drop all other"

# FORWARD











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
