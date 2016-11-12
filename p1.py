from mpi4py import MPI
import logging

#IMPORTANT PROGRAM SETTINGS

NODEPERCC = 2
CCPERCLC = 2

logging.basicConfig(level=logging.DEBUG)

#CODE CONSTANTS
CLC_RANK = 0


#CODE BEGIN
comm = MPI.COMM_WORLD
rank = comm.Get_rank()
size = comm.Get_size()

assert (size == (1 + 1*CCPERCLC + (1*CCPERCLC)*NODEPERCC)),"Number of process created is wrong"

if rank == CLC_RANK:
	logging.info("I AM CLOUD CONTROLLER")

else:
	if rank%(NODEPERCC+1) == 1:
		logging.info("I AM CLUSTER CONTROLLER")
	else:
		logging.info("I AM NODE CONTROLLER")

print "My rank is ",rank