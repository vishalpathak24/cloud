import libvirt
import sys
from bs4 import BeautifulSoup
import random
import socket   #getting host name
import commands
import time

#command to create a raw file dd if=/dev/zero of=ubuntu16-04.raw bs=1 count=1 seek=15G
# uuidgen to genrate UUID 


#Constants

BASE_DIR = '/media/vishalpathak/HD-E11/acedemics/CloudComputing/Assg/'

#IMAGES_DIR = BASE_DIR+'images/'

#DRIVE_DIR = BASE_DIR+'drives/'

#ISO_DIR = BASE_DIR+'iso/'

IMAGES_DIR = BASE_DIR

DRIVE_DIR = BASE_DIR

ISO_DIR = '/media/vishalpathak/HD-E11/softwares/'

#Node specific variables
VMcount = 0
print VMcount

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

def startVM(xml):
	conn = libvirt.open("qemu:///system")
	if conn == None:
		print "Unable to open hypervisor"
		sys.exit(1)
	new_dom = conn.createXML(xml,0)
	conn.close()

def createNewVM(hd_size_gb,ram_size_gb,n_cores):
  #Generating Mac address of the system
  mac = [0x52,0x54,0x00] #qemu mac start
  mac = mac+ [
              random.randint(0x00, 0xff),
              random.randint(0x00, 0xff),
              random.randint(0x00, 0xff)]
  mac=':'.join(map(lambda x: "%02x" % x, mac))

  #Generating UUID for system
  x,UUID_str = commands.getstatusoutput("uuidgen")
  if x != 0:
    return -1

  #Generating Hard Disk
  HDD_name = createHDD(hd_size_gb)
  if HDD_name == -1:
    return -1

  cur_xml = vm_new_xml

  soup_xml = BeautifulSoup(cur_xml,"xml")

  #Generating Name
  PC_name = socket.gethostname()
  virt_name = "INST_"+PC_name+"_"+str(createNewVM.VMcount)
  NAME = soup_xml.find('name')
  NAME.string = virt_name
  
  #Setting UUID
  UUID = soup_xml.find('uuid')
  UUID.string = UUID_str

  #Setting MAC
  MAC = soup_xml.find('mac')
  MAC['address']=mac
  
  #Setting RAM
  ram_kb = str(int(ram_size_gb)*1024*1024)
  RAM = soup_xml.find('memory')
  RAM.string = ram_kb

  #Setting VCPU
  VCPU = soup_xml.find('vcpu')
  VCPU.string = str(n_cores)

  #Setting disk location
  Disk = soup_xml.find(device="disk")
  Disk_source = Disk.find('source')
  Disk_source['file'] = DRIVE_DIR+HDD_name

  cur_xml = str(soup_xml)

  startVM(cur_xml)																																																								
  createNewVM.VMcount+=1;
  return virt_name

def getStats(dom):
	#getting CPU Stats
	stats = dom.getCPUStats(False)
	vcpu_time = 0
	cpu_time = 0
	for stat in stats:
		vcpu_time+=stat['vcpu_time']
		cpu_time+=stat['cpu_time']
	print "vcpu",vcpu_time
	print "cpu_time",cpu_time,"\n"
	per_cpu=((vcpu_time*100)/cpu_time)
	print "CPU utilization is ",per_cpu,"%"
	
	result={}																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																			
	result['vcpu_time']=vcpu_time
	result['cpu_time']=cpu_time
	return result

createNewVM.VMcount = 0

dom=createNewVM(15,2,2)
conn = libvirt.open("qemu:///system")

dom = conn.lookupByName(dom)
#dom1 = conn.lookupByName("INST_vishal-G560_0")
#dom2 = conn.lookupByName("INST_vishal-G560_1")
while True:
	R1=getStats(dom)
	#R2=getStats(dom2)
	print "R1 share ",((R1['cpu_time']*100)/(R1['cpu_time']+R2['cpu_time']))
	#print "R2 share ",((R2['cpu_time']*100)/(R1['cpu_time']+R2['cpu_time']))
	time.sleep(0.5)

conn.close()

'''

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

'''