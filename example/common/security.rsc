{ :local ver [/system resource get version]; :global vermajor [:pick $ver 0 [:find $ver "."]] }

/ip neighbor discovery-settings set discover-interface-list=none

/ip ipsec policy set 0 disabled=yes

:if ($vermajor = 7) do={ /ipv6 settings set disable-ipv6=yes }
:if ($vermajor = 6) do={ /system package disable ipv6 }

/tool mac-server set allowed-interface-list=none
/tool mac-server mac-winbox set allowed-interface-list=none
/tool mac-server ping set enabled=no

/ip service set api     disabled=yes
/ip service set api-ssl disabled=yes
/ip service set ftp     disabled=yes
/ip service set telnet  disabled=yes
/ip service set winbox  disabled=no

/tool bandwidth-server set enabled=no

/ip ssh set strong-crypto=yes host-key-size=4096 forwarding-enabled=both always-allow-password-login=yes

/ip settings set rp-filter={{ rp_filter | default("strict") }} secure-redirects=no tcp-syncookies=yes
