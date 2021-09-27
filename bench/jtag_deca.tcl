source [find interface/altera-usb-blaster2.cfg]

jtag newtap 10m50 tap -expected-id 0x031050dd -irlen 10
set _CHIPNAME 10m50

# source [find cpld/jtagspi.cfg]


gdb_port disabled
tcl_port disabled
telnet_port disabled

target create 10m50.tap or1k -endian big -chain-position 10m50.tap

tap_select vjtag
du_select adv 0

init

irscan 10m50.tap 0xe

puts "Waiting for Any Key"
gets stdin

puts "  DEADBEEF 32 RES: 0x[drscan 10m50.tap 32 0xDEADBEEF]"

puts "00DEADBEEF 40 RES: 0x[drscan 10m50.tap 40 0x00DEADBEEF]"

puts "00DEADBEEF 64 RES: 0x[drscan 10m50.tap 64 0x00000000DEADBEEF]"

puts "00DEADBEEF 80 RES: 0x[drscan 10m50.tap 80 0x000000000000DEADBEEF]"

shutdown
