#!/usr/bin/env bash
source "$REPO/scripts/common.sh"
# Add only explicit listener rules; never flush tables or change the SSH rules/default policy.
TCP=(80 443 992 1194 2053 2083 2087 2096 3443 4433 4443 5555 7443 8388 8443 9443 9444 10443 11443)
UDP=(53 443 500 1194 4443 4500 8388 8443 10443 51820 51821)
[[ "$ENABLE_PPTP" != yes ]] || TCP+=(1723)
[[ "$ENABLE_PLAIN_PROXY" != yes ]] || TCP+=(1080)
for p in "${TCP[@]}"; do iptables -C INPUT -p tcp --dport "$p" -j ACCEPT 2>/dev/null || iptables -I INPUT -p tcp --dport "$p" -j ACCEPT; done
for p in "${UDP[@]}"; do iptables -C INPUT -p udp --dport "$p" -j ACCEPT 2>/dev/null || iptables -I INPUT -p udp --dport "$p" -j ACCEPT; done
# dnstt DNAT changes destination port before filter INPUT.
iptables -C INPUT -p udp --dport 5300 -j ACCEPT 2>/dev/null || iptables -I INPUT -p udp --dport 5300 -j ACCEPT
if [[ "$ENABLE_PPTP" == yes ]]; then iptables -C INPUT -p gre -j ACCEPT 2>/dev/null || iptables -I INPUT -p gre -j ACCEPT; fi
netfilter-persistent save
