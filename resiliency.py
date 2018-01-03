#!/usr/bin/python

"""
Create a network and start sshd(8) on each host.

While something like rshd(8) would be lighter and faster,
(and perfectly adequate on an in-machine network)
the advantage of running sshd is that scripts can work
unchanged on mininet and hardware.

In addition to providing ssh access to hosts, this example
demonstrates:

- creating a convenience function to construct networks
- connecting the host network to the root namespace
- running server processes (sshd in this case) on hosts
"""

import sys

from mininet.net import Mininet
from mininet.cli import CLI
from mininet.log import lg, info
from mininet.node import Node
from mininet.topolib import TreeTopo
from mininet.util import waitListening
from mininet.link import Link



def connectToRootNS( network, switch, ip, routes ):
    """Connect hosts to root namespace via switch. Starts network.
      network: Mininet() network object
      switch: switch to connect to root namespace
      ip: IP address for root namespace node
      routes: host networks to route to"""
    # Create a node in root namespace and link to switch 0
    root = Node( 'root', inNamespace=False )
    defaultIP1 = '10.0.1.0/24'
    defaultIP2 = '10.0.2.0/24'
    defaultIP3 = '10.0.3.0/24'
    #Adding routers to obtain three networks
    router1 = Node('wifi1', cls = LinuxRouter, ip = defaultIP1)
    router2 = Node('wifi2', cls = LinuxRouter, ip = defaultIP2)
    router3 = Node('wifi3', cls = LinuxRouter, ip = defaultIP3)
    #Adding links between routers and switches
    Link(s4, router1, intfName2= 'n1-eth0', params2={'ip':defaultIP1})
    Link(s3, router2, intfName2= 'n2-eth0', params2={'ip':defaultIP2})
    Link(s2, router3, intfName2= 'n3-eth0', params2={'ip':defaultIP3})
    #Adding links between hosts and switches
    Link(h1, s4)
    Link(h1, s2, params1={'ip':'10.0.2.1/24'})
    Link(h1, s3, params1 ={'ip':'10.0.3.1/24'})
    Link(h2, s4)
    Link(h2, s2, params1={'ip':'10.0.2.2/24'})
    Link(h2, s3, params1={'ip':'10.0.3.2/24'})

    	
    intf = network.addLink( root, switch ).intf1
    root.setIP( ip, intf=intf )
    # Start network that now includes link to root namespace
    network.start()
    # Add routes from root ns to hosts
    for route in routes:
        root.cmd( 'route add -net ' + route + ' dev ' + str( intf ) )
	info (network['h1'].cmd('ip route flush table main'))
	info (network['h2'].cmd('ip route flush table main'))
	"Adding routes to the routing table of hosts"
	info (network['h1'].cmd('route add -net 10.0.0.0 netmask 255.255.255.0 dev h1-eth0'))
	info (network['h1'].cmd('route add -net 10.0.2.0 netmask 255.255.255.0 dev h1-eth1'))
	info (network['h1'].cmd('route add -net 10.0.3.0 netmask 255.255.255.0 dev h1-eth2'))
        info (network['h2'].cmd('route add -net 10.0.0.0 netmask 255.255.255.0 dev h2-eth0'))
	info (network['h2'].cmd('route add -net 10.0.2.0 netmask 255.255.255.0 dev h2-eth1'))
	info (network['h2'].cmd('route add -net 10.0.3.0 netmask 255.255.255.0 dev h2-eth2')) 
		
def sshd( network, cmd='/usr/sbin/sshd', opts='-D',
          ip='10.123.123.1/32', routes=None, switch=None ):
    """Start a network, connect it to root ns, and run sshd on all hosts.
       ip: root-eth0 IP address in root namespace (10.123.123.1/32)
       routes: Mininet host networks to route to (10.0/24)
       switch: Mininet switch to connect to root namespace (s1)"""
    if not switch:
        switch = network[ 's1' ]  # switch to use
    if not routes:
        routes = [ '10.0.0.0/24' ]
    connectToRootNS( network, switch, ip, routes )
    for host in network.hosts:
        host.cmd( cmd + ' ' + opts + '&' )
    print "*** Waiting for ssh daemons to start"
    for server in network.hosts:
        waitListening( server=server, port=22, timeout=5 )

    print
    print "*** Hosts are running sshd at the following addresses:"
    print
    for host in network.hosts:
        print host.name, host.IP()
    print "\n*** Pinging through Network1 ***\n"	
    info(network['h1'].cmd('ping -c 1 10.0.0.2'))
    print "\n*** Pinging through Network2 ***\n"
    info(network['h1'].cmd('ping -c 1 10.0.2.2'))
    print "\n*** Pinging through Network3 ***\n"
    info(network['h1'].cmd('ping -c 1 10.0.3.2'))
    	    	    

    print
    print "*** Type 'exit' or control-D to shut down network"
    CLI( network )
    for host in network.hosts:
        host.cmd( 'kill %' + cmd )
    network.stop()

class LinuxRouter(Node):
	"A node with IP forwarding"
	def config(self, **params):
		super(LinuxRouter, self).config(**params)
		#To enable forwarding
		self.cmd('sysctl net.ipv4.ip_forward = 1')
	def terminate(self):
		self.cmd('sysctl net.ipv4.ip_forward = 0')
		super(LinuxRouter, self).terminate()

if __name__ == '__main__':
    lg.setLogLevel( 'info')
    network = Mininet(topo = None, build = False)
    info("***Adding Controller***\n")
    network.addController(name = 'c0')
    #Adding hosts and switches
    info('***Adding Hosts***\n')
    h1 = network.addHost('h1')
    h2 = network.addHost('h2')
    info('***Adding Switches***\n')
    s1 = network.addSwitch('s1')
    s2 = network.addSwitch('s2')
    s3 = network.addSwitch('s3')
    s4 = network.addSwitch('s4')
    
    
    # get sshd args from the command line or use default args
    # useDNS=no -u0 to avoid reverse DNS lookup timeout
    argvopts = ' '.join( sys.argv[ 1: ] ) if len( sys.argv ) > 1 else (
        '-D -o UseDNS=no -u0' )
    sshd( network, opts=argvopts )
