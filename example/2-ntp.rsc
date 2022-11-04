/system ntp client
set enabled=yes primary-ntp=162.159.200.123 secondary-ntp=162.159.200.1

/system ntp server
set enabled=yes

/ip firewall filter
add chain="user-input" action=jump jump-target="user-input-ntp" comment="NTP rules"
add chain="user-input-ntp" \
    action=accept \
    in-interface-list=LAN protocol=udp dst-port=123 \
    comment="accept NTP (LAN)"
{{ rollback_delete_chain("user-input-ntp") }}
