# Run tshark to convert pcap to csv 
# Usage: bash pcap_to_csv.sh input.pcap output.csv

echo "Running T-Shark pcap2csv conversion"
tshark -r $1 -T fields -e udp.srcport -e udp.dstport -e tcp.srcport -e tcp.dstport -e eth.dst -e ip.src -e ip.dst -e ip.proto -e ip.flags -e ip.len -e frame.protocols -e frame.time_epoch -e tcp.flags -e tcp.len -e udp.length -E header=y -E separator=, -E quote=d -E occurrence=f > $2
echo "T-Shark pcap2csv conversion complete"
