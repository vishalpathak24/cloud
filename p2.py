from mpi4py import MPI
import logging
import random
import commands


#PROGRAM CONSTANTS
CTRL_TAG = 0
DATA_TAG = 1
MC_RANK = 0


POOL_NAME = "default-cloud"
#BASE_DIR = '/home/admin-6019/nfs_share/'
BASE_DIR = '/media/vishalpathak/HD-E11/acedemics/CloudComputing/Assg/'

PRIVATE_DIR = '/media/vishalpathak/HD-E11/acedemics/CloudComputing/'
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

#CODE BEGIN
comm = MPI.COMM_WORLD
rank = comm.Get_rank()
size = comm.Get_size()


if rank==MC_RANK:
	status=MPI.Status()
	exit=False
	while not exit:

		#File Controller
		print "1. Create HDD"
		print "2. Upload File"
		print "3. Download File"
		print "4. Exit"

		ch=input()

		if ch==1:
			print "Enter the size of HDD you want (in GB) "
			size=input()
			for sc in range(1,3):
				comm.send("createHDD",dest=sc,tag=CTRL_TAG)
				comm.send(size,dest=sc,tag=DATA_TAG)
				comm.recv(source=sc,tag=CTRL_TAG,status=status)
		elif ch==2:
			print "Enter location of file"
			loc=raw_input()
			for sc in range(1,3):
				comm.send("uploadFile",dest=sc,tag=CTRL_TAG)
				comm.send(loc,dest=sc,tag=DATA_TAG)
				comm.recv(source=sc,tag=CTRL_TAG,status=status)
		elif ch==4:
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
			comm.send("Done",dest=MC_RANK,tag=CTRL_TAG)

		elif command == "uploadFile":
			logging.info("Uploading")
		
		elif command == "exit":
			exit=True