import subprocess


##Do all the things you need over here for gate permutation
##Make SQD file, txt with the coordinates you want to permutate and outputs and the file with truth table;

##Make function that calls a pipe witch simply calls the main.py with the right arguments

def call_analysis():
    sqd_file = "AND-AND.sqd"
    coordinates_file = "AND-AND.txt"
    truth_table_file = "AND-AND_table.txt"
    command = ["python3", "main.py", sqd_file, coordinates_file, truth_table_file]
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
    stdout, stderr = process.communicate()

    if process.returncode == 0:
        if(stdout[0] == "1"):
            print("Success, table matches, gate works")
        elif(stdout[0] == "0"):
            print("Table does not match, gate does not work")
            print(stdout[1:])
        else:
            print("Something went wrong")
    else:
        print("ERROR!")
        print(stderr)
        
## After this, it could be possible to grab the analysis and check what is going on with the outputs, example:
## - If in ONE case of the inputs, the output of the FIRST gate is 0 when it should be 1, you could try to: 
## -> Move it closer to the booster
## -> Add a DB to the output of the gate (8-10 distance)
## -> If the first DB after the booster (Lets call it Output-MID) is being checked and it also gives a wrong result
## -> Move the gate closer to the booster, or further away from the booster, etc.

call_analysis()