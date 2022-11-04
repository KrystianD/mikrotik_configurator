/ip firewall nat
add chain="user-dstnat" action=jump jump-target="user-dstnat-port-forwarding" comment="port forwarding"

add chain="user-dstnat-port-forwarding" action=dst-nat comment="port forwarding -> HTTP" dst-port=80,443 in-interface=ether1-WAN protocol=tcp to-addresses=192.168.1.2
add chain="user-dstnat-port-forwarding" action=dst-nat comment="port forwarding -> SSH"  dst-port=1234   in-interface-list=WAN   protocol=tcp to-addresses=192.168.1.2 to-ports=22322

{{ rollback_delete_chain("user-dstnat-port-forwarding") }}