/system logging action remove [find default=no]
/system logging remove [find default=no]

/system logging action
add name=pc2 remote=192.168.1.2 remote-port=1514 target=remote

/system logging
add action=pc2 prefix=MT topics=critical
add action=pc2 prefix=MT topics=error
add action=pc2 prefix=MT topics=warning
add action=pc2 prefix=MT topics=info
