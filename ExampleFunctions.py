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

def manipulate(auction_amount,client_amount,client_amount_limit,client_amount_step):
    # I simply want to return the auction amount + client step
    return auction_amount + client_amount_step

def manipulate(auction_amount,client_amount,client_amount_limit,client_amount_step):
    #   .......................... To do .....................................
    # condicionar steps
    # alterar valor do step
    # condicionar amount_limit
    return auction_amount + client_amount_step
# Unsafe Examples:

def myfunction(bid):
    # I wonder if it really HAS to be called 'validate'...
    # do smth...

def validate(bid,arg2):
    # I wonder if it really HAS to contain ONLY ONE argument...
    # do smth...

def validate(bid):
    # I wonder if I can use create more than 1 function...
    result = auxfunc(bid.auction)
def auxfunc(auction):
    # do smth with the auction...


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