import libvirt
import sys
import logging
from bs4 import BeautifulSoup
import random
import socket   #getting host name
import commands
import time
from xml.etree import ElementTree


#command to create a raw file dd if=/dev/zero of=ubuntu16-04.raw bs=1 count=1 seek=15G
# uuidgen to genrate UUID 

#filename='/home/admin-6019/Documents/image.img'

#Constants

USER_NAME = "admin-6019"
POOL_NAME = "default-cloud"
#POOL_NAME = "default"

BASE_DIR = '/home/admin-6019/nfs_share/'
#BASE_DIR = '/media/vishalpathak/HD-E11/acedemics/CloudComputing/Assg/'

filename=BASE_DIR+'image.img'
IMAGES_DIR ='/home/admin-6019/nfs_share/pool/'

#DRIVE_DIR = BASE_DIR+'drives/'

#ISO_DIR = BASE_DIR+'iso/'

#IMAGES_DIR = BASE_DIR

DRIVE_DIR = BASE_DIR

ISO_DIR = '/home/admin-6019/nfs_share/'
#ISO_DIR = '/media/vishalpathak/HD-E11/softwares/'

#Node specific variables
VMcount = 0
#print VMcount

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
			<source file=\''''+IMAGES_DIR+'''ubuntu16.04.qcow2'/>
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
	Command_String = """chmod 777 """+DRIVE_DIR+"/"+Filename
	x,y=commands.getstatusoutput(Command_String)
	if x==0:
		return Filename
	return -1

def startVM(xml):
	conn = libvirt.open("qemu:///system")
	if conn == None:
		logging.info("Unable to open hypervisor")
		sys.exit(1)
	#new_dom = conn.createXML(xml,0)
	new_dom = conn.defineXML(xml)
	new_dom.create()
	conn.close()
	return

def SaveVM(VMname) :
	conn = libvirt.open('qemu:///system')
	if conn == None:
		print('Failed to open connection to qemu:///system')
		exit(1)
	dom = conn.lookupByName(VMname)
	if dom == None:
		print('Cannot find guest to be saved.')
		exit(1)
	#info = dom.info()
	#if info == None:
	#	print('Cannot check guest state')
	#	exit(1)
	#if info.state == VIR_DOMAIN_SHUTOFF:
	#	print('Not saving guest that is not running')
	#	exit(1)
	filename = BASE_DIR+VMname+".img"
	if dom.save(filename) < 0:
		print('Unable to save guest to '+str(filename))
	print('Guest state saved to '+str(filename))
	conn.close()
	return

def restoreVM(VMname) :
	filename = BASE_DIR+VMname+".img"
	conn = libvirt.open('qemu:///system')
	if conn == None:
		print('Failed to open connection to qemu:///system')
		exit(1)
	iD = conn.restore(filename)
	Command_String="rm "+filename
	x,y = commands.getstatusoutput(Command_String)

	if iD < 0:
		print('Unable to restore guest from ')
		exit(1)
	#dom = conn.lookupByID(iD);
	#if dom == None:
	#	print('Cannot find guest that was restored')
	#	exit(1)
	print('Guest state restored from '+filename)
	conn.close()
	return

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
	
	virt_name = "INST_"+PC_name+"_"+str(random.randint(0,1000))
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
	try:
		stats = dom.getCPUStats(False)
		result={}
		if len(stats) > 0:
			vcpu_time = 0
			cpu_time = 0
			
			for stat in stats:
				cpu_time+=stat['cpu_time']
				if 'vcpu_time' in stat: #Not available for newly created VMs
					vcpu_time+=stat['vcpu_time']
				
			#logging.info( "vcpu"+str(vcpu_time))
			#logging.info("cpu_time"+str(cpu_time)+"\n")
			
			if cpu_time !=0:
				per_cpu=((vcpu_time*100)/cpu_time)
				#logging.info("CPU utilization is "+str(per_cpu)+"%")
			
																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																				
			result['vcpu_time']=vcpu_time
			result['cpu_time']=cpu_time

			# Memory stats
			memory = dom.memoryStats()
			result['actual_ram'] = memory['actual']
			result['used_ram'] = memory['rss']

			#Network load
			tree = ElementTree.fromstring(dom.XMLDesc())
			iface = tree.find('devices/interface/target').get('dev')
			NL_1 = dom.interfaceStats(iface)
			time.sleep(0.5)
			NL_2 = dom.interfaceStats(iface)
			result['upload_packet'] = NL_2[4] - NL_1[4]
			result['download_packet'] = NL_2[0] - NL_1[0]
	except libvirt.libvirtError:
		#Domain newly created unable to get stats for now																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																
		logging.info("Execption Caught")
		result['vcpu_time']=0
		result['cpu_time']=0
		result['actual_ram'] = 0
		result['used_ram'] = 0
		result['upload_packet'] = 0
		result['download_packet'] = 0
	return result

def migrate(dom_name,host_src,host_dest):
	conn_src = libvirt.open("qemu+tcp://"+USER_NAME+"@"+host_src+"/system")
	conn_dest = libvirt.open("qemu+tcp://"+USER_NAME+"@"+host_dest+"/system")
	dom=conn_src.lookupByName(dom_name)
	new_dom = dom.migrate(conn_dest,libvirt.VIR_MIGRATE_LIVE|libvirt.VIR_MIGRATE_UNSAFE,None,"tcp://"+host_dest,0)
	conn_dest.close()
	conn_src.close()
	if new_dom == None:
		logging.info( "Unable to Migrate")
		return False
	
	return True

def getLocalPoolInfo():
	#logging.info("local Pool info")
	conn = libvirt.open("qemu:///system")
	pool = conn.storagePoolLookupByName(POOL_NAME)
	info = pool.info()
	result={}
	result['Capacity']=info[1]/(1024*1024*1024)
	result['Allocation']=info[2]/(1024*1024*1024)
	result['Available']=info[3]/(1024*1024*1024)
	conn.close()
	return result

def getLocalDomainInfo():
	conn = libvirt.open("qemu:///system")
	result={}
	ActiveDomain_IDs = conn.listDomainsID()
	for Dom_id in ActiveDomain_IDs:
		dom = conn.lookupByID(Dom_id)
		dom_stat = getStats(dom)
		result[dom.name()]=dom_stat

	conn.close()
	return result

def getLocalMemoryInfo():
	conn = libvirt.open("qemu:///system")

	mem_stats = conn.getFreeMemory()
	result = mem_stats

	conn.close()
	return result

def getActiveLocalDomainInfo():
	conn = libvirt.open("qemu:///system")
	
	result={}
	ActiveDomain_IDs = conn.listDomainsID()
	for Dom_id in ActiveDomain_IDs:
		dom = conn.lookupByID(Dom_id)
		#logging.info("Finding info for domain"+dom.name())
		dom_stat = getStats(dom)
		result[dom.name()]=dom_stat
	
	conn.close()
	return result

def createServer():
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
	
	
	
	###################CHANGE HERE FOR ACTUAL COPY##################
	#HDD_name = DRIVE_DIR+"ubuntu_"+str(random.randint(0,1000))+".qcow2"
	HDD_name = DRIVE_DIR+"ubuntu_"+str(730)+".qcow2"
	#Command_String = "cp "+IMAGES_DIR+"ubuntu16.04.qcow2 "+HDD_name
	#print "copying from "+Command_String
	#x,out = commands.getstatusoutput(Command_String)
	#if x == -1:
	#	return "NOT ABLE TO CREATE"
	Command_String = "chmod 777 "+HDD_name
	x,out = commands.getstatusoutput(Command_String)
	if x == -1:
		return "NOT ABLE TO CREATE"
	#############################################
	if HDD_name == -1:
		return -1

	cur_xml = vm_xml

	soup_xml = BeautifulSoup(cur_xml,"xml")

	#Generating Name
	PC_name = socket.gethostname()
	
	virt_name = "SERV_"+PC_name+"_"+str(random.randint(0,1000))
	NAME = soup_xml.find('name')
	NAME.string = virt_name
	
	#Setting UUID
	UUID = soup_xml.find('uuid')
	UUID.string = UUID_str

	#Setting MAC
	MAC = soup_xml.find('mac')
	MAC['address']=mac
	
	#Setting disk location
	Disk = soup_xml.find(device="disk")
	Disk_source = Disk.find('source')
	Disk_source['file'] = HDD_name

	cur_xml = str(soup_xml)

	startVM(cur_xml)																																																								
	createNewVM.VMcount+=1;
	return virt_name



def Hello():
	logging.info("Hello from virt")
	return	
createNewVM.VMcount = 0
#print "Creating Server"
#createServer()
