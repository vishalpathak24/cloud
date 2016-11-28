from mpi4py import MPI
import logging
import virt

#IMPORTANT PROGRAM SETTINGS

NODEPERCC = 2
CCPERCLC = 2

logging.basicConfig(level=logging.DEBUG)

#CODE CONSTANTS
CLC_RANK = 0


#SIGNALS
SIG_CTRL = 0
SIG_DATA = 1


#CODE BEGIN
comm = MPI.COMM_WORLD
rank = comm.Get_rank()
size = comm.Get_size()


assert (size == (1 + 1*CCPERCLC + (1*CCPERCLC)*NODEPERCC)),"Number of process created is wrong"

#Algorithm to schedule VMs

def greedyAlgo(pool_result,actdom_result):
	for i in range(0,CCPERCLC):
		if pool_result[i]['Available'] >= VMHDDsize:
			return i
	return -1

def NCchoice_greedy(activedom_state):
	if len(activedom_state) > 0:
		min_busy = 0
		for i in range(0,NODEPERCC+1):
			#if activedom_state[min_busy][]

			#TODO: Code to access load on node

	else:
		return 0



#Creating NC rank list
CC_ranks = []
for i in range(0,NODEPERCC):
	CC_ranks.append(1+i*(CCPERCLC+1))

if rank == CLC_RANK:
	logging.info("I AM CLOUD CONTROLLER")
	exit=False
	while not exit:
		#getting consolidated resource
		i=0
		pool_result={}
		actdom_result={}

		for cc in CC_ranks:
			comm.send("getpoolinfo",dest=cc,tag=SIG_CTRL)
			status = MPI.Status()
			logging.info("Sent Data")
			pool_result[i]=comm.recv(source=cc,tag=SIG_CTRL,status=status)
			print "FOR CC in GB",i+1,pool_result[i]
			i+1

		#MENU OF CLC
		print "1. Print Domains"
		print "2. Create VM"
		print "3. Exit"

		#MENE OF CLC END
		choice = input("Enter Your choice")
		
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
			VMHDDsize = input("Enter the size of disk you want in GB")
			VMNCPU = input("Enter the number of cores you want should be <=4")
			VMRAM = input("Eneter the RAM size you want in GB")
			CC_choice = greedyAlgo(pool_result,actdom_result,VMHDDsize)
			if CC_choice not -1:
				CC_choice_rank = 1+CC_choice*(NODEPERCC	+1)
				comm.send("createvm",dest=CC_choice_rank,tag=SIG_CTRL)
				comm.send(VMHDDsize,dest=CC_choice_rank,tag=SIG_DATA)
				comm.send(VMNCPU,dest=CC_choice_rank,tag=SIG_DATA)
				comm.send(VMRAM,dest=CC_choice_rank,tag=SIG_DATA)
				print "waiting for creation of vm"
				status = MPI.Status()
				new_vm_name = comm.recv(source=CC_choice_rank,tag=SIG_DATA,status=status)
				print "New VM created with Name ",new_vm_name

			else:
				print "Unable to find CC for given choice"

		elif choice == 3:
			for cc in CC_ranks:
				comm.send("exit",dest=cc,tag=SIG_CTRL)
			exit=True

else:
	if rank%(NODEPERCC+1) == 1:
		logging.info("I AM CLUSTER CONTROLLER")
		exit=False
		status = MPI.Status()
		while not exit:
			command=comm.recv(source=MPI.ANY_SOURCE,tag=SIG_CTRL,status=status)
			
			if command=="getpoolinfo":
				result = virt.getLocalPoolInfo()
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
					com.send("getactivedomaininfo",dest=nc,tag=SIG_CTRL)
				
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
				comm.send(virt_name,dest=CLC_RANK,tag=SIG_DATA)
					
			elif command=="exit":
				for nc in range(rank+1,rank+1+NODEPERCC):
					comm.send("exit",dest=nc,tag=SIG_CTRL)
					exit=True

	else:
		logging.info("I AM NODE CONTROLLER")
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
			elif command === "createvm" :
				VMHDDsize=comm.recv(source=ccRank,tag=SIG_DATA,status=status)
				VMNCPU=comm.recv(source=ccRank,tag=SIG_DATA,status=status)
				VMRAM=comm.recv(source=ccRank,tag=SIG_DATA,status=status)
				virt_name=virt.createNewVM(VMHDDsize,VMRAM,VMNCPU)
				comm.send(virt_name,dest=ccRank,tag=SIG_DATA)
			elif command =="exit":
				exit=True

print "My rank is ",rank