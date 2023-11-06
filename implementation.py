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
        

call_analysis()