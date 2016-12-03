from mpi4py import MPI
import logging
import virt
import operator
import socket
import time

#IMPORTANT PROGRAM SETTINGS

NODEPERCC = 2
CCPERCLC = 2
NETWORK_THRESH = 80

logging.basicConfig(level=logging.DEBUG)

#CODE CONSTANTS
CLC_RANK = 0


#SIGNALS
SIG_CTRL = 0
SIG_DATA = 1
SIG_SAVE = 2

#CODE BEGIN
comm = MPI.COMM_WORLD
rank = comm.Get_rank()
size = comm.Get_size()

#print "Hello",socket.gethostname()

assert (size == (1 + 1*CCPERCLC + (1*CCPERCLC)*NODEPERCC)),"Number of process created is wrong"

#Algorithm to schedule VMs

def greedyAlgo(pool_result,actdom_result,VMHDDsize):
	for i in range(0,CCPERCLC):
		if pool_result[i]['Available'] >= VMHDDsize:
			return i
	return -1

def NCchoice_greedy(activedom_state):
	
	if len(activedom_state) > 0:
		min_busy = 0
		"""
		for i in range(0,NODEPERCC+1):
			if activedom_state[i] >= activedom_state[min_busy]:
				min_busy = i
		"""
		min_busy=max(activedom_state.iteritems(), key=operator.itemgetter(1))[0]
		
		#print(min_busy)

		return min_busy	

	else:
		return 0
	
	return 0
def NCchoice_match_making(activedom_state):
	
	if len(activedom_state) > 0:
		min_busy = 0
		"""
		for i in range(0,NODEPERCC+1):
			if activedom_state[i] >= activedom_state[min_busy]:
				min_busy = i
		"""
		cpu_freq=1000
		free_memory=2
		ranking_expression=cpu_freq*free_memory
		
		min_busy=max(activedom_state.iteritems(), key=operator.itemgetter(1))[0]
		
		print(min_busy)

		return min_busy	

	else:
		return 0
	
	return 0

def NCchoice_round_robbin():
	
	if len(activedom_state) > 0:
		min_busy = 0
		"""
		for i in range(0,NODEPERCC+1):
			if activedom_state[i] >= activedom_state[min_busy]:
				min_busy = i
		"""
		if not hasattr(NCchoice_round_robbin, "count"):
			NCchoice_round_robbin.count = 0  # it doesn't exist yet, so initialize it
		NCchoice_round_robbin.count += 1
		print(NCchoice_round_robbin.count)		
		
		

		return NCchoice_round_robbin.count%2	

	else:
		return 0
	
	return 0


#Creating NC rank list
CC_ranks = []

for i in range(0,NODEPERCC):
	CC_ranks.append(1+i*(CCPERCLC+1))
print CC_ranks
if rank == CLC_RANK:
	#key: CC rank ,value :list of VMS
	CCnames = {}
	logging.info("I AM CLOUD CONTROLLER"+socket.gethostname())
	print "I AM CLOUD CONTROLLER"
	exit=False
	while not exit:
		#getting consolidated resource
		#print "hello from loop"		
		i=0
		pool_result={}
		actdom_result={}

		for cc in CC_ranks:
			logging.info("Sending Data to "+str(cc))
			comm.send("getpoolinfo",dest=cc,tag=SIG_CTRL)
			status = MPI.Status()
			logging.info("Sent Data")
			pool_result[i]=comm.recv(source=cc,tag=SIG_CTRL,status=status)
			print "FOR CC in GB",i+1,pool_result[i]
			i=i+1

		#MENU OF CLC
		print "1. Print Domains"
		print "2. Create VM"
		print "3. Exit"
		print "4. Save"
		print "7. Create Server"

		#MENE OF CLC END
		print "Enter Your choice"
		choice = input()
		
		if choice == 1:
			actdom_result={}
			for cc in CC_ranks:
				comm.send("getdomaininfo",dest=cc,tag=SIG_CTRL)
			i=0
			for cc in CC_ranks:
				status = MPI.Status()
				logging.info("Sent Data")
				actdom_result[i]=comm.recv(source=cc,tag=SIG_CTRL,status=status)
				i=i+1
				print "IN CC ",i,actdom_result[i-1]
		
		elif choice == 2:
			print "Enter the size of disk you want in GB"
			VMHDDsize = input()
			print "Enter the number of cores you want should be <=4"
			VMNCPU = input()
			print "Eneter the RAM size you want in GB"
			VMRAM = input()
			CC_choice = greedyAlgo(pool_result,actdom_result,VMHDDsize)
			if CC_choice != -1:
				CC_choice_rank = 1+CC_choice*(NODEPERCC	+1)
				comm.send("createvm",dest=CC_choice_rank,tag=SIG_CTRL)
				comm.send(VMHDDsize,dest=CC_choice_rank,tag=SIG_DATA)
				comm.send(VMNCPU,dest=CC_choice_rank,tag=SIG_DATA)
				comm.send(VMRAM,dest=CC_choice_rank,tag=SIG_DATA)
				print "waiting for creation of vm"
				status = MPI.Status()
				
				new_vm_name = comm.recv(source=CC_choice_rank,tag=SIG_DATA,status=status)

				CCnames[new_vm_name]=CC_choice_rank
				
				print "New VM created with Name ",new_vm_name

			else:
				logging.info("Unable to find CC for given choice")

		elif choice == 3:
			for cc in CC_ranks:
				comm.send("exit",dest=cc,tag=SIG_CTRL)
			exit=True
		
		elif choice == 4:
			print CCnames
			print "Enter the Cluster controller rank containing your VM " 
			CC_rank = input()
			print "Enter the vmname"
			vmname = raw_input()
			comm.send("SaveVM",dest=CC_rank,tag=SIG_CTRL)
			comm.send(vmname,dest=CC_rank,tag=SIG_SAVE)
			print "waiting for cluster controller to save VM "
			#status= MPI.Status()

		elif choice == 7:
			CC_choice = greedyAlgo(pool_result,actdom_result,16.1)
			status=MPI.Status()
			if CC_choice != -1:
				CC_choice_rank = 1+CC_choice*(NODEPERCC	+1)
				print "creating server...."+str(CC_choice_rank)
				comm.send("createserver",dest=CC_choice_rank,tag=SIG_CTRL)
				print "Waiting for Response"
				server_name = comm.recv(source=CC_choice_rank,tag=SIG_DATA,status=status)
				print "Successfull in creating Demo SERVER",server_name
			else:
				print "Unable to chose cluster constroller for server"

else:
	if rank%(NODEPERCC+1) == 1:
		logging.info("I AM CLUSTER CONTROLLER"+socket.gethostname())
		#key : NC rank ,value :list of VMS
		NCVMList={}
		exit=False
		clone_done=[]
		status = MPI.Status()
		while not exit:
			
			if comm.Iprobe(source=CLC_RANK,tag=SIG_CTRL):

				command=comm.recv(source=CLC_RANK,tag=SIG_CTRL,status=status)
				
				if command=="getpoolinfo":
					logging.info("GOT POOL INFO")
					result = virt.getLocalPoolInfo()
					logging.info("Sending Pool info")
					comm.send(result,dest=status.Get_source(),tag=SIG_CTRL)
				
				elif command =="getdomaininfo":
					result={}
					for nc in range(rank+1,rank+1+NODEPERCC):
						comm.send("getdomaininfo",dest=nc,tag=SIG_CTRL)
					for nc in range(rank+1,rank+1+NODEPERCC):
						result_nc = comm.recv(source=nc,tag=SIG_CTRL,status=status)
						for dom in result_nc:
							result[dom]=result_nc[dom]
					comm.send(result,dest=CLC_RANK,tag=SIG_CTRL)		

				elif command=="createvm":
					activedom_state={}
					
					#Assesing Current Situation of NC
					for nc in range(rank+1,rank+1+NODEPERCC):
						comm.send("getlocalmemoryinfo",dest=nc,tag=SIG_CTRL)
					
					i=0
					for nc in range(rank+1,rank+1+NODEPERCC):
						result_nc = comm.recv(source=nc,tag=SIG_CTRL,status=status)
						activedom_state[i] = result_nc
						i=i+1

					nc_choice = NCchoice_greedy(activedom_state)
					nc_choice_rank = rank+1+nc_choice
					#TODO : make signals to NC for creating vm and correspoinding actions
					comm.send("createvm",dest=nc_choice_rank,tag=SIG_CTRL)

					VMHDDsize=comm.recv(source=CLC_RANK,tag=SIG_DATA,status=status)
					VMNCPU=comm.recv(source=CLC_RANK,tag=SIG_DATA,status=status)
					VMRAM=comm.recv(source=CLC_RANK,tag=SIG_DATA,status=status)

					comm.send(VMHDDsize,dest=nc_choice_rank,tag=SIG_DATA)
					comm.send(VMNCPU,dest=nc_choice_rank,tag=SIG_DATA)
					comm.send(VMRAM,dest=nc_choice_rank,tag=SIG_DATA)

					#Waiting for name of VM
					virt_name=comm.recv(source=nc_choice_rank,tag=SIG_DATA,status=status)
					NCVMList[virt_name]=nc_choice_rank
					comm.send(virt_name,dest=CLC_RANK,tag=SIG_DATA)
				
				elif command=="SaveVM" :
					print "in saveVM"
					print NCVMList
					vmname = comm.recv(source=CLC_RANK,tag=SIG_SAVE,status=status)
					NC_rank= NCVMList[vmname]
					comm.send("SaveVM",dest=NC_rank,tag=SIG_CTRL)
					comm.send(vmname,dest=NC_rank,tag=SIG_SAVE)
					print "waiting for Node controller to save VM "
					status= MPI.Status()		
				
				elif command=="createserver":
					activedom_state={}
					
					#Assesing Current Situation of NC
					for nc in range(rank+1,rank+1+NODEPERCC):
						comm.send("getlocalmemoryinfo",dest=nc,tag=SIG_CTRL)
					
					i=0
					for nc in range(rank+1,rank+1+NODEPERCC):
						result_nc = comm.recv(source=nc,tag=SIG_CTRL,status=status)
						activedom_state[i] = result_nc
						i=i+1

					nc_choice = NCchoice_greedy(activedom_state)
					nc_choice_rank = rank+1+nc_choice
					logging.info("SENDING NC TO CREATE SERVER"+str(nc_choice_rank))
					comm.send("createserver",dest=nc_choice_rank,tag=SIG_CTRL)

					#Waiting for name of SERVER
					
					virt_name=comm.recv(source=nc_choice_rank,tag=SIG_DATA,status=status)
					logging.info("WAITING TO CREATE"+str(nc_choice_rank))
					NCVMList[virt_name]=nc_choice_rank
					comm.send(virt_name,dest=CLC_RANK,tag=SIG_DATA)


				elif command=="exit":
					for nc in range(rank+1,rank+1+NODEPERCC):
						comm.send("exit",dest=nc,tag=SIG_CTRL)
						exit=True
			else:
				#logging.info("Nothing to do here")
				
				#Finding state of NCs
				for nc in range(rank+1,rank+1+NODEPERCC):
					comm.send("getactivedomaininfo",dest=nc,tag=SIG_CTRL)
				activedom_state={}
				
				i=0
				for nc in range(rank+1,rank+1+NODEPERCC):
					result_nc = comm.recv(source=nc,tag=SIG_CTRL,status=status)
					activedom_state[i] = result_nc
					i=i+1

				#Algo for finding if VM-Scaling is needed
				for nc in activedom_state:
					#print activedom_state
					for dom in activedom_state[nc]:
						if dom.startswith("SERV"):
							total_load = activedom_state[nc][dom]['upload_packet'] +activedom_state[nc][dom]['download_packet']
							#print "load on ",dom," is ",total_load
							if dom not in clone_done:
								if total_load > NETWORK_THRESH:
									print "overload detected cloning ",dom
									#Asking NC to create VM migration will distribute
									comm.send("createserver",dest=nc,tag=SIG_CTRL)
									comm.send(dom,dest=nc,tag=SIG_DATA)
									new_server = comm.recv(source=nc,tag=SIG_DATA)
									clone_done.append(dom)
									clone_done.append(new_server)



				#Algo if migration is needed
				time.sleep(0.5)

	else:
		logging.info("I AM NODE CONTROLLER"+socket.gethostname())
		#Finding Rank of CLUSTER CONTROLLER
		ccRank=-1
		for cc in CC_ranks:
			if rank < cc:
				break
			else:
				ccRank=cc 

		exit=False
		status = MPI.Status()

		while not exit:
			command=comm.recv(source=MPI.ANY_SOURCE,tag=SIG_CTRL,status=status)

			if command =="getdomaininfo":
				result = virt.getLocalDomainInfo()
				#print result
				comm.send(result,dest=ccRank,tag=SIG_CTRL)
			elif command == "getactivedomaininfo":
				result = virt.getActiveLocalDomainInfo()
				comm.send(result,dest=ccRank,tag=SIG_CTRL)
			elif command == "getlocalmemoryinfo":
				result = virt.getLocalMemoryInfo()
				comm.send(result,dest=ccRank,tag=SIG_CTRL)
			elif command == "createvm" :
				VMHDDsize=comm.recv(source=ccRank,tag=SIG_DATA,status=status)
				VMNCPU=comm.recv(source=ccRank,tag=SIG_DATA,status=status)
				VMRAM=comm.recv(source=ccRank,tag=SIG_DATA,status=status)
				virt_name=virt.createNewVM(VMHDDsize,VMRAM,VMNCPU)
				comm.send(virt_name,dest=ccRank,tag=SIG_DATA)
			elif command == "SaveVM" :
				VMname=comm.recv(source=ccRank,tag=SIG_SAVE,status=status)
				virt.SaveVM(VMname)
			elif command == "clonevm":
				dom_name = comm.recv(source=ccRank,tag=SIG_DATA,status=status)
				virt.cloneVM(dom_name)
			elif command == "createserver":
				logging.info("CREATING SERVER")
				server_name = virt.createServer()
				logging.info("CREATING SERVER DONE")
				comm.send(server_name,dest=ccRank,tag=SIG_DATA)
			elif command =="exit":
				exit=True

print "My rank is ",rank
