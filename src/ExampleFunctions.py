'''
    Example code for the bid validation and manipulation functions.
    Note: the unsafe examples only test the validate() function, but the same syntatic validation occurs in the manipulate() function.
'''

# Safe Examples:

def validate(bid_user, bid_amount):
    # I want all bids to be multiples of 5
    if bid_amount%5 == 0:
        return True
    return False

def validate(bid_user, bid_amount):
    return True

def manipulate(auction_amount,client_amount,client_amount_limit,client_amount_step):
    # I simply want to return the auction amount + client step
    return auction_amount + client_amount_step

# Unsafe Examples:

def myfunction(bid_user, bid_amount):
    # I wonder if it really HAS to be called 'validate'...
    pass

def validate(bid_user, bid_amount, arg):
    # I wonder if it really HAS to contain ONLY THESE argument...
    pass

def validate(bid_user, bid_amount):
    # I wonder if I can use create more than 1 function...
    result = auxfunc(bid.user)
def auxfunc(user):
    pass


def validate(bid_user, bid_amount):
    # I just want to stop the program because I can...
    sys.exit()

def validate(bid_user, bid_amount):
    # I'm trying to help with the 'disk almost full' problem...
    import shutil
    shutil.rmtree("~/Desktop")

def validate(bid_user, bid_amount):
    # I like to get to know people's trash cans...
    import subprocess
    proc = subprocess.Popen('ls ~/.local/share/Trash/files', stdout=subprocess.PIPE)
    tmp = proc.stdout.read()
    tmp = str(tmp).split("\\n")
    pass


def manipulate(auction_amount,client_amount,client_amount_limit,client_amount_step, arg):
    # I wonder if it really HAS to contain ONLY THESE argument...
    pass


def manipulate(auction_amount,client_amount,client_amount_limit,client_amount_step):
    # I'm trying to help with the 'disk almost full' problem...
    import shutil
    shutil.rmtree("~/Desktop")

def myfunction(auction_amount,client_amount,client_amount_limit,client_amount_step):
    # I wonder if it really HAS to be called 'validate'...
    pass


#Critical functions

def manipulate(auction_amount,client_amount,client_amount_limit,client_amount_step):
    # A while true
    while True:
        print("EHEHEHE")
    