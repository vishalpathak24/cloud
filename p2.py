from mpi4py import MPI
import logging
import random
import commands
import virt
from xml.etree import ElementTree as ET
import libvirt



#PROGRAM CONSTANTS
CTRL_TAG = 0
DATA_TAG = 1
MC_RANK = 0


POOL_NAME = "default-cloud"
#BASE_DIR = '/home/admin-6019/nfs_share/'
BASE_DIR = '/home/hdvishal/share/'

PRIVATE_DIR = '/home/hdvishal/'
DRIVE_DIR = PRIVATE_DIR

logging.basicConfig(level=logging.DEBUG)


stgvol_xml = """
<volume>
<name>sparse.img</name>
<allocation>0</allocation>
<capacity unit="G">2</capacity>
<target>
<path>"""+DRIVE_DIR+"""sparse.img</path>
<permissions>
<owner>107</owner>
<group>107</group>
<mode>0744</mode>
<label>virt_image_t</label>
</permissions>
</target>
</volume>"""

pool_xml="""<pool type='dir'>
  <name>mypool</name>
  <uuid>8c79f996-cb2a-d24d-9822-ac7547ab2d01</uuid>
  <capacity unit='bytes'>4306780815</capacity>
  <allocation unit='bytes'>237457858</allocation>
  <available unit='bytes'>4069322956</available>
  <source>
  </source>
  <target>
    <path>/home/dashley/images</path>
    <permissions>
    <mode>0755</mode>
    <owner>-1</owner>
    <group>-1</group>
    </permissions>
  </target>
</pool>"""

DISK_TEMPLATE = \
'''<disk type="file" device="disk">
        <driver name="qemu" type="raw" />
        <source file="{path}"/>
        <target bus='virtio' dev="{dev}"/>
</disk>
'''


def attach_disk(domain, path, dev):
    conn = libvirt.open("qemu:///system")
    dom = conn.lookupByName(domain)
    template = DISK_TEMPLATE.format(path=path, dev=dev)
    dom.attachDevice(template)
    conn.close()

#CODE BEGIN
comm = MPI.COMM_WORLD
rank = comm.Get_rank()
size = comm.Get_size()


if rank==MC_RANK:
	status=MPI.Status()
	exit=False
	HDD_name=''
	while not exit:

		#File Controller
		print "1. Create HDD"
		print "2. Upload File"
		print "3. Download File"
		print "4. Attach HDD to Domain"
		print "5. Exit"

		ch=input()

		if ch==1:
			print "Enter the size of HDD you want (in GB) "
			size=input()
			for sc in range(1,3):
				comm.send("createHDD",dest=sc,tag=CTRL_TAG)
				comm.send(size,dest=sc,tag=DATA_TAG)
				if sc ==1:
					HDD_name=comm.recv(source=sc,tag=DATA_TAG,status=status)
					print "HDD_name update to ",HDD_name
				else:
					comm.recv(source=sc,tag=DATA_TAG,status=status)

		elif ch==2:
			print "Enter location of file"
			loc=raw_input()
			for sc in range(1,3):
				comm.send("uploadFile",dest=sc,tag=CTRL_TAG)
				comm.send(loc,dest=sc,tag=DATA_TAG)
				comm.recv(source=sc,tag=DATA_TAG,status=status)

		elif ch==4:
			print "Enter Domain Name"
			dom_name=raw_input()
			attach_disk(dom_name,DRIVE_DIR+HDD_name,'vdb')


		elif ch==5:
			for sc in range(1,3):
				comm.send("exit",dest=sc,tag=CTRL_TAG)
			exit=True

else:
	exit = False
	status=MPI.Status()
	HHD_list={}
	N_HDD = 0
	index=-1
	FILE_LIST = {}

	while not exit:
		command=comm.recv(source=MC_RANK,tag=CTRL_TAG,status=status)

		if command == "createHDD":
			HDD_Size=comm.recv(source=MC_RANK,tag=DATA_TAG,status=status)
			HDD_Name="HDD_"+str(random.randint(0,1000))+".img"
			Command_String="dd if=/dev/zero of="+PRIVATE_DIR+HDD_Name+" bs=1 count=1 seek="+str(HDD_Size)+"G"
			x,y = commands.getstatusoutput(Command_String)
			Command_String="mkfs.fat "+PRIVATE_DIR+HDD_Name
			x,y = commands.getstatusoutput(Command_String)
			
			#if x== 0:

			HHD_list[N_HDD]=HDD_Name
			N_HDD+=1
			if index==-1:
				index=0
			comm.send(HDD_Name,dest=MC_RANK,tag=DATA_TAG)

		elif command == "uploadFile":
			logging.info("Uploading")
		
		elif command == "exit":
			exit=True