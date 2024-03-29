from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet
from ryu.lib.packet.packet import Packet
from ryu.lib.packet import arp
from ryu.lib.packet import ethernet
from ryu.lib.packet import ether_types


class LoadBalancer(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]     # Specify the use of OpenFlow v13
    virtual_ip = "10.0.0.10"              # The virtual server IP
    ## Hosts 5 and 6 are servers.
    H5_mac = "00:00:00:00:00:05"          # Host 5's mac
    H5_ip = "10.0.0.5"                    # Host 5's IP
    H6_mac = "00:00:00:00:00:06"          # Host 6's mac
    H6_ip = "10.0.0.6"                    # Host 6's IP
    next_server = ""      # Stores the IP of the  next server to use in round robin manner
    current_server = ""   # Stores the current server's IP
    ip_to_port = {H5_ip: 5, H6_ip: 6}
    ip_to_mac = {"10.0.0.1": "00:00:00:00:00:01",
                 "10.0.0.2": "00:00:00:00:00:02",
                 "10.0.0.3": "00:00:00:00:00:03",
                 "10.0.0.4": "00:00:00:00:00:04"}

    def __init__(self, *args, **kwargs):
        super(LoadBalancer, self).__init__(*args, **kwargs)
        self.next_server = self.H5_ip
        self.current_server = self.H5_ip

    # This function is called when a packet arrives from the switch
    # after the initial handshake has been completed.
    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def packet_in_handler(self, ev):
        msg = ev.msg
        dp = msg.datapath
        ofp = dp.ofproto
        ofp_parser = dp.ofproto_parser
        in_port = msg.match['in_port']

        pkt = packet.Packet(msg.data)
        etherFrame = pkt.get_protocol(ethernet.ethernet)

        # If the packet is an ARP packet, create new flow table
        # entries and send an ARP response.
        if etherFrame.ethertype == ether_types.ETH_TYPE_ARP:
            self.add_flow(dp, pkt, ofp_parser, ofp, in_port)
            self.arp_response(dp, pkt, etherFrame, ofp_parser, ofp, in_port)
            self.current_server = self.next_server
            return
        else:
            return

    # Sends an ARP response to the contacting host with the
    # real MAC address of a server.
    def arp_response(self, datapath, packet, etherFrame, ofp_parser, ofp, in_port):
        arpPacket = packet.get_protocol(arp.arp)
        dstIp = arpPacket.src_ip
        srcIp = arpPacket.dst_ip
        dstMac = etherFrame.src

        # If the ARP request isn't from one of the two servers,
        # choose the target/source MAC address from one of the servers;
        # else the target MAC address is set to the one corresponding
        # to the target host's IP.
        if dstIp != self.H5_ip and dstIp != self.H6_ip:
            if self.next_server == self.H5_ip:
                srcMac = self.H5_mac
                self.next_server = self.H6_ip
            else:
                srcMac = self.H6_mac
                self.next_server = self.H5_ip
        else:
            srcMac = self.ip_to_mac[srcIp]

        e = ethernet.ethernet(dstMac, srcMac, ether_types.ETH_TYPE_ARP)
        a = arp.arp(1, 0x0800, 6, 4, 2, srcMac, srcIp, dstMac, dstIp)
        p = Packet()
        p.add_protocol(e)
        p.add_protocol(a)
        p.serialize()

        # ARP action list
        actions = [ofp_parser.OFPActionOutput(ofp.OFPP_IN_PORT)]
        # ARP output message
        out = ofp_parser.OFPPacketOut(
            datapath=datapath,
            buffer_id=ofp.OFP_NO_BUFFER,
            in_port=in_port,
            actions=actions,
            data=p.data
        )
        datapath.send_msg(out) # Send out ARP reply

    # Sets up the flow table in the switch to map IP addresses correctly.
    def add_flow(self, datapath, packet, ofp_parser, ofp, in_port):
        srcIp = packet.get_protocol(arp.arp).src_ip

        # Don't push forwarding rules if an ARP request is received from a server.
        if srcIp == self.H5_ip or srcIp == self.H6_ip:
            return

        # Generate flow from host to server.
        match = ofp_parser.OFPMatch(in_port=in_port,
                                    ipv4_dst=self.virtual_ip,
                                    eth_type=0x0800)
        actions = [ofp_parser.OFPActionSetField(ipv4_dst=self.current_server),
                   ofp_parser.OFPActionOutput(self.ip_to_port[self.current_server])]
        inst = [ofp_parser.OFPInstructionActions(ofp.OFPIT_APPLY_ACTIONS, actions)]

        mod = ofp_parser.OFPFlowMod(
            datapath=datapath,
            priority=0,
            buffer_id=ofp.OFP_NO_BUFFER,
            match=match,
            instructions=inst)

        datapath.send_msg(mod)

        # Generate reverse flow from server to host.
        match = ofp_parser.OFPMatch(in_port=self.ip_to_port[self.current_server],
                                    ipv4_src=self.current_server,
                                    ipv4_dst=srcIp,
                                    eth_type=0x0800)
        actions = [ofp_parser.OFPActionSetField(ipv4_src=self.virtual_ip),
                   ofp_parser.OFPActionOutput(in_port)]
        inst = [ofp_parser.OFPInstructionActions(ofp.OFPIT_APPLY_ACTIONS, actions)]

        mod = ofp_parser.OFPFlowMod(
            datapath=datapath,
            priority=0,
            buffer_id=ofp.OFP_NO_BUFFER,
            match=match,
            instructions=inst)

        datapath.send_msg(mod)
