ssh-keygen -N "" -f ssh_host_private_key_dsa -t dsa -m pkcs8
ssh-keygen -N "" -f ssh_host_private_key_rsa -t rsa -m pkcs8
ssh-keygen -e -f ssh_host_private_key_rsa.pub -m pkcs8 > ssh_host_private_key_rsa.pub.tmp
mv ssh_host_private_key_rsa.pub.tmp ssh_host_private_key_rsa.pub
