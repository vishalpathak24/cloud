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


#CODE BEGIN
comm = MPI.COMM_WORLD
rank = comm.Get_rank()
size = comm.Get_size()


assert (size == (1 + 1*CCPERCLC + (1*CCPERCLC)*NODEPERCC)),"Number of process created is wrong"


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
		for cc in CC_ranks:
			comm.send("getpoolinfo",dest=cc,tag=SIG_CTRL)
			status = MPI.Status()
			logging.info("Sent Data")
			pool_result[i]=comm.recv(source=cc,tag=SIG_CTRL,status=status)
			print "FOR CC in GB",i+1,pool_result[i]
			i+1

		#MENU OF CLC
		print "1. Print Domains"
		print "2. Exit"

		#MENE OF CLC END
		choice = input("Enter Your choice")
		
		if choice == 1:
			result={}
			for cc in CC_ranks:
				comm.send("getdomaininfo",dest=cc,tag=SIG_CTRL)
			for cc in CC_ranks:
				status = MPI.Status()
				logging.info("Sent Data")
				result[i]=comm.recv(source=cc,tag=SIG_CTRL,status=status)
				print "IN CC ",i+1,result[i]
		
		elif choice == 2:
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
			elif command =="exit":
				exit=True

print "My rank is ",rank