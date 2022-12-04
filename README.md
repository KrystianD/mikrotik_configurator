Mikrotik configurator
======

A utility for generating and applying RouterOS / Mikrotik configuration files (.rsc).

It uses Jinja2 as a template engine with few additional helpers.

Features:

* Applying configuration over SSH,
* Support for applying only part of the whole configuration (e.g. if only firewall settings have changed).

Helpers:

* Escaping string and blocks,
* Embedding files (e.g. SSH keys),
* Cleanup functions (executed in reverse order on configuration re-apply),
* Rolling back firewall chains.

Additional:

* [IntelliJ color schema configuration](intellij) for .rsc files,
* [A script](tools/gen_ssh_host_keys.sh) for generating RouterOS-compatible SSH host key files.

# Usage

Prepare template files, like from [the embedded example](example):

* 0_0-initial.rsc
* 0_1-security.rsc
* 0_2-firewall.rsc
* 1-logging.rsc
* 2-ntp.rsc
* 3-port-forwarding.rsc

Naming is important:

* filenames starting with `0_` are considered reset configuration that is being applied after
  `/system reset-configuration` command is executed,
* filenames starting with other numbers can be applied to actively running Mikrotik router,
* adding numbers help with applying the configuration in proper order.

### Configuration

```yaml
has_flash: false     # for some RouterOS devices Flash directory is        
                     # accessible via explicit /flash/ prefix, for some just /

host: 192.168.1.1    # IP of the Mikrotik device, can be overriden with --override-id CLI argument

include_dirs: # search paths for templates including
  - common/

variables: # additonal Jinja2 variables
  admin_pass: "pass"
```

### Reset configuration and apply

```shell
cd example/
python ../mikrotik_configurator [--dry-run] --reset *.rsc
```

### Part of the configuration re-applying

```shell
cd example/
python ../mikrotik_configurator [--dry-run] 3-port-forwarding.rsc
```

# Examples

## Setting admin password from config file

File `config.yaml`

```yaml
variables:
  admin_pass: "pass"
```

File `1-example.rsc`

```text
/user set admin password="{{ admin_pass }}"
```

## SSH public key loading

File `1-example.rsc`

```text
{{ load_file("~/.ssh/id_rsa.pub", "pcl_id_rsa.pub.txt") }}
/user ssh-keys import user=admin public-key-file=pcl_id_rsa.pub.txt
```

## Creating a firewall target with rollback

```text
/ip firewall filter
add chain="user-input" action=jump jump-target="user-input-ntp" comment="NTP rules"
add chain="user-input-ntp" action=accept in-interface-list=LAN protocol=udp dst-port=123 comment="accept NTP (LAN)"
{{ rollback_delete_chain("user-input-ntp") }}
```

## Custom cleanup

```text
/interface ovpn-client add name=my-ovpn \
                           connect-to=myhost.com port=1190 \
                           user=$vpnusername \
                           password=$vpnpassword \
                           verify-server-certificate=yes \
                           cipher=aes256

{% call register_cleanup() %}
    /interface ovpn-client remove my-ovpn
{% endcall %}
```

## Script escape

```text
/system script
add dont-require-permissions=yes name="ddns-update" owner=admin policy=read,test source={% call escape_string() %}
/tool fetch output=none mode=https url="https://my.own.dynamic.dns.site\?domain={{ public_domain }}" http-method=post http-data="token={{ ddns_token }}"
{% endcall %}
```
