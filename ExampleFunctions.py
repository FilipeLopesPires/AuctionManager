'''
	Example code for the bid validation and manipulation functions.
	Note: the unsafe examples only test the validate(bid) function, but the same syntatic validation occurs in the manipulate(bid) function.
'''

# Safe Examples:

def validate(bid):
	# I want all bids to be multiples of 5
	if bid.amount%5 == 0:
		return True
	return False

def manipulate(bid):
	#   .......................... To do .....................................

# Unsafe Examples:

def myfunction(bid):
	# I wonder if it really HAS to be called 'validate'...
	# do smth...

def validate(bid,arg2):
	# I wonder if it really HAS to contain ONLY ONE argument...
	# do smth...

def validate(bid):
	# I wonder if I can use inner functions...
	def auxfunc(auction):
		# do smth with the auction...
	result = auxfunc(bid.auction)
	# do smth else...

def validate(bid):
	# I just want to stop the program because I can...
	sys.exit()

def validate(bid):
	# I'm trying to help with the 'disk almost full' problem...
	import shutil
	shutil.rmtree("~/Desktop")

def validate(bid):
	# I like to get to know people's trash cans...
	import subprocess
	proc = subprocess.Popen('ls ~/.local/share/Trash/files', stdout=subprocess.PIPE)
	tmp = proc.stdout.read()
	tmp = str(tmp).split("\\n")
	# do smth with the files in trash...