import libvirt
import sys
from bs4 import BeautifulSoup
import random
import socket   #getting host name
import commands

#command to create a raw file dd if=/dev/zero of=ubuntu16-04.raw bs=1 count=1 seek=15G
# uuidgen to genrate UUID 


#Constants

BASE_DIR = '/home/hdvishal/cloud-simulation/'

#IMAGES_DIR = BASE_DIR+'images/'

#DRIVE_DIR = BASE_DIR+'drives/'

#ISO_DIR = BASE_DIR+'iso/'

IMAGES_DIR = BASE_DIR

DRIVE_DIR = BASE_DIR

ISO_DIR = '/home/hdvishal/cloud-simulation/'



#XML COPY OF VM
vm_xml = '''<domain type='kvm'>
  <name>ubuntu16.04-clone2</name>
  <uuid>959345b3-1027-47d9-ad52-c6fd199166e2</uuid>
  <memory unit='KiB'>2097152</memory>
  <vcpu placement='static'>1</vcpu>
  <os>
    <type arch='x86_64' machine='pc-i440fx-xenial'>hvm</type>
    <boot dev='hd'/>
  </os>
  <clock offset='utc'>
  </clock>
  <on_poweroff>destroy</on_poweroff>
  <on_reboot>restart</on_reboot>
  <on_crash>restart</on_crash>
  <devices>
    <emulator>/usr/bin/kvm-spice</emulator>
    <disk type='file' device='disk'>
      <driver name='qemu' type='qcow2'/>
      <source file='/var/lib/libvirt/images/ubuntu16.04_2.qcow2'/>
      <target dev='vda' bus='virtio'/>
      <address type='pci' domain='0x0000' bus='0x00' slot='0x07' function='0x0'/>
    </disk>
    <interface type='bridge'>
      <mac address='52:54:00:b4:f5:0b'/>
      <source bridge='br1'/>
      <model type='virtio'/>
      <address type='pci' domain='0x0000' bus='0x00' slot='0x03' function='0x0'/>
    </interface>
    <input type='mouse' bus='ps2'/>
    <input type='keyboard' bus='ps2'/>
    <graphics type='spice' autoport='yes'>
      <image compression='off'/>
    </graphics>
  </devices>
</domain>'''

vm_new_xml ='''<domain type='kvm'>
  <name>ubuntu16.04-new</name>
  <uuid>959345b3-1027-47d9-ad52-c6fd199166e2</uuid>
  <memory unit='KiB'>2097152</memory>
  <vcpu placement='static'>1</vcpu>
  <os>
    <type arch='x86_64' machine='pc-i440fx-xenial'>hvm</type>
    <boot dev='hd'/>
    <boot dev='cdrom'/>
  </os>
  <clock offset='utc'>
  </clock>
  <on_poweroff>destroy</on_poweroff>
  <on_reboot>restart</on_reboot>
  <on_crash>restart</on_crash>
  <devices>
    <emulator>/usr/bin/kvm-spice</emulator>
    <disk type='file' device='disk'>
      <driver name='qemu' type='raw'/>
      <source file=\''''+DRIVE_DIR+'''ubuntu16-04.raw\'/>
      <target dev='vda' bus='virtio'/>
      <address type='pci' domain='0x0000' bus='0x00' slot='0x07' function='0x0'/>
    </disk>
    <disk type='file' device='cdrom'>
		<source file=\''''+ISO_DIR+'''ubuntu-16.04-desktop-amd64.iso\'/>
		<target dev='hdc' bus='ide'/>
	</disk>
    <interface type='bridge'>
      <mac address='52:54:00:b4:f5:0b'/>
      <source bridge='br1'/>
      <model type='virtio'/>
      <address type='pci' domain='0x0000' bus='0x00' slot='0x03' function='0x0'/>
    </interface>
    <input type='mouse' bus='ps2'/>
    <input type='keyboard' bus='ps2'/>
    <graphics type='spice' autoport='yes'>
      <image compression='off'/>
    </graphics>
  </devices>
</domain>'''

#function definations
def createHDD(size):
  HD_id = random.randint(0,1000)
  PC_name = socket.gethostname()
  Filename = "HDD_"+PC_name+"_"+str(HD_id)+".raw"
  Command_String = """dd if=/dev/zero of="""+DRIVE_DIR+"/"+Filename+""" bs=1 count=1 seek="""+str(size)+"G"
  x,y=commands.getstatusoutput(Command_String)
  if x==0:
    return Filename
  return -1


conn = libvirt.open("qemu:///system")

if conn == None:
	print "Unable to open hypervisor"
	sys.exit(1)

print "Sccess in connection"

domainIDs = conn.listDomainsID()
domainNames = conn.listDefinedDomains()

if domainIDs == None:
	print('Failed to get a list of domain IDs')
	sys.exit(1)


print("Active domain IDs:")
if len(domainIDs) == 0:
	print(' None')
else:
	for domainID in domainIDs:
		print(' '+str(domainID))
		domain=conn.lookupByID(domainID)
		#Running Domain
		print domain.name(),"OS type is",domain.OSType()
		print "Has current snapshot",domain.hasCurrentSnapshot()
		print "Has managed save image",domain.hasManagedSaveImage()
		
		state, maxmem, mem, cpus, cput = domain.info()
		print('The state is ' + str(state))
		print('The max memory is ' + str(maxmem))
		print('The memory is ' + str(mem))
		print('The number of cpus is ' + str(cpus))
		print('The cpu time is ' + str(cput))


print("All inactive domain names:")
if len(domainNames) == 0:
	print(' None')
else:
	for domainName in domainNames:
		print(' '+domainName)


print("Trying to create a domain")



soup = BeautifulSoup(vm_new_xml,"xml")
UUID = soup.find('uuid')

#print "UUID tag is ",UUID.string
UUID.string = "959345b3-1027-47d9-ad52-c6fd199167d3"

print "*************\n"
print str(soup)
vm_new_xml = str(soup)

#sys.exit(0)

new_dom = conn.createXML(vm_new_xml,0)

if new_dom == None:
	print("Unable to create new domain")
	sys.exit(1)

print("Successfully created the required domain")

print ("Creating Hardisk")

createHDD(15)


conn.close()
sys.exit(0)