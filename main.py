import xml.etree.ElementTree as ET
import itertools
from copy import deepcopy
import os
import sys
import math
import subprocess
from datetime import datetime
from tabulate import tabulate
def change_header(file, shall_print, num_instances):
    if(shall_print):
        print("Making modified Header file for Simulation", end='\r')
        sys.stdout.flush()
    tree = ET.parse(file)
    root = tree.getroot()
    
    program = root.find(".//program")
    file_purpose = program.find("file_purpose")
    file_purpose.text = "simulation"
    new_sim_params = ET.Element("sim_params")
    date_element = program.find(".//date")
    current_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    date_element.text = current_date

    new_sim_params_str = """
    <sim_params>
        <T_e_inv_point>0.09995000064373016</T_e_inv_point>
        <T_init>500</T_init>
        <T_min>2</T_min>
        <T_schedule>exponential</T_schedule>
        <anneal_cycles>10000</anneal_cycles>
        <debye_length>5</debye_length>
        <eps_r>5.599999904632568</eps_r>
        <hop_attempt_factor>5</hop_attempt_factor>
        <muzm>-0.3199999928474426</muzm>
        <num_instances>-1</num_instances>
        <phys_validity_check_cycles>10</phys_validity_check_cycles>
        <reset_T_during_v_freeze_reset>false</reset_T_during_v_freeze_reset>
        <result_queue_size>0.10000000149011612</result_queue_size>
        <strategic_v_freeze_reset>false</strategic_v_freeze_reset>
        <v_freeze_end_point>0.4000000059604645</v_freeze_end_point>
        <v_freeze_init>-1</v_freeze_init>
        <v_freeze_reset>-1</v_freeze_reset>
        <v_freeze_threshold>4</v_freeze_threshold>
    </sim_params>
    """



    # Parse the new sim_params XML string and insert it into the root
    new_sim_params = ET.fromstring(new_sim_params_str)
    # Modify the num_instances if provided
    num_instances_element = new_sim_params.find('num_instances')
    num_instances_element.text = f'{num_instances}'

    root.insert(1, new_sim_params)
    
    sim_params = root.find(".//sim_params")
    if(sim_params is not None):
        root.remove(sim_params)
    else:
        print("No SIM_PARAMS element found")

    root.insert(1, new_sim_params)

    # Save the modified XML to a file
    tree.write('modified_file.xml', encoding='utf-8', xml_declaration=True)

def call_simmaneal(file, result_name, shall_print):
    resultPath = " ./result/" + result_name
    command = " ./simanneal/simanneal " + file + resultPath
    if(shall_print):
        print("Calling Simanneal for file: " + file + " please wait!", end='\r')
        sys.stdout.flush()
    subprocess.run(command, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def grab_DBs(db_file):
    try:
        with open(db_file, "r") as file:
            coordinates = []
            inputs = []
            outputs = []

            for line_number, line in enumerate(file, start=1):
                line = line.strip()

                if not line:
                    continue

                if line_number == 1:
                    input_number = int(line)
                elif line_number == 2:
                    output_number = int(line)
                elif input_number > 0:
                    input_number -= 1
                    inputs.append(grab_coordinate(line))
                elif output_number > 0:
                    output_number -= 1
                    outputs.append(grab_coordinate(line))

        return inputs, outputs
    except:
        print("Error, missing or invalid file:", db_file)
        return "None", "None"

def grab_coordinate(line):
    n, m, l, name = line.split()
    n = float(n)
    m = float(m)
    l = float(l)
    return n, m, l, name

def remove_dbdots_by_latcoord(xml_tree, coordinates):
    db_layer = xml_tree.find(".//layer[@type='DB']")

    coordinates_without_name = [(n, m, l) for n, m, l, _ in coordinates]

    for dbdot in xml_tree.findall(".//dbdot"):
        latcoord = dbdot.find("latcoord")
        
        if latcoord is not None:
            n = latcoord.get("n")
            m = latcoord.get("m")
            l = latcoord.get("l")
            
            coords = (float(n), float(m), float(l))

            if(coords in coordinates_without_name):
                db_layer.remove(dbdot)
    
    return xml_tree

def read_result(file, output_coordinates):
    #print("file: " + file)
    tree = ET.parse(file)
    root = tree.getroot()
    indexes = []

    i = 0
    for dbdot in root.findall(".//dbdot"):
        x = float(dbdot.get("x"))
        y = float(dbdot.get("y"))

        for output in output_coordinates:
            x_output = output[0] * 3.84
            y_output = (output[1] * 7.68) + (output[2] * 2.25)
            #print(x_output, y_output, x, y)
            if(x == x_output and y == y_output):
                indexes.append([i, output])
                break
        i += 1

    biggest = []
    lowest_energy = math.inf

    for dist in root.findall(".//dist"):
        energy = float(dist.get("energy"))
        count = int(dist.get("count"))
        physically_valid = int(dist.get("physically_valid")) == 1
        state_count = int(dist.get("state_count"))
        symbol = dist.text
        if not physically_valid:
            continue

        if energy < lowest_energy:
            biggest = [energy, count, physically_valid, state_count, symbol]
            lowest_energy = energy
    
    symbol = biggest[4]
    
    symbol_list = []

    for i, output in indexes:
        symbol_list.append([output[3], symbol[i], energy])
        

    return symbol_list

def combinations(dbdot_coordinates, output_coordinates, file, shall_print):
    tree = ET.parse(file)
    number_of_dots = len(dbdot_coordinates)
    combinations_to_remove = []
    table_combination_result = []

    #i, X Y
    DB_Table = []


    for i in range(number_of_dots + 1):
        combinations_to_remove.extend(itertools.combinations(dbdot_coordinates, i))

    i = 0

    truth_table = []

    for combination in combinations_to_remove:
        # Make a copy of the original XML tree
        modified_tree = deepcopy(tree)
        opposite_combination = [coord for coord in dbdot_coordinates if coord not in combination]

        modified_tree = remove_dbdots_by_latcoord(modified_tree, combination)

        # Save the modified XML to a file
        modified_tree.write(f'modified/modified_file_{i}.xml', encoding='utf-8', xml_declaration=True)
        call_simmaneal(f'modified/modified_file_{i}.xml', f'result_{i}.xml', shall_print)
        result = read_result(f'./result/result_{i}.xml', output_coordinates)

        opposite_names = [name for _, _, _, name in opposite_combination]
        result_names = [name_output for name_output, _, _ in result]
        result_values = [value for _, value, _ in result]
        result_energy = [energy for _, _, energy in result]
        result_energy = [result_energy[0]]
        result_name = f'result_{i}.xml'
        truth_table.append([result_name,opposite_names, result_names, result_values, result_energy])
        i += 1

    return truth_table

def remove_files_in_directory(directory):
    for file in os.listdir(directory):
        file_path = os.path.join(directory, file)
        if os.path.isfile(file_path):
            #print(file_path)
            os.remove(file_path)

def list_files_in_directory(directory):
    sqd_files = [f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f)) and f.endswith('.sqd')]
    return sqd_files

#This part of the code will be responsable for grabbing
#(or telling the program that it needs to generate for future runs)
#The expected table;

def grab_table(table_file):
    if(not os.path.isfile(table_file)):
        return ["NoTable"], ["NoTable"]
    
    try:
        data = []
        header = []
        lineNumber = 0
        with open(table_file, "r") as file:
            for line in file:
                if(lineNumber == 0):
                    lineNumber += 1
                    header = line.strip().split(" | ")
                    continue
                parts = line.strip().split(" | ")
                inputs_str = parts[0].strip()
                results_str = parts[1].strip()
                #print(results_str)
                
                inputs = inputs_str.split()  # Split inputs
                results = results_str.split()  # Split outputs
                #print(">>", results)
                data.append([inputs, results])

        #Now to convert the Header and data into the format we want
        input_header = header[0].split()
        output_header = header[1].split()

        new_data = deepcopy(data)
        for i, (inputs, results) in enumerate(new_data):
            #print(results)
            new_data[i][0] = [input_header[j] for j in range(len(inputs)) if inputs[j] == '1']
            new_results = []
            for result in results:
                if result == '1':
                    new_results.append('-')
                else:
                    new_results.append('0')
            
            new_data[i][1] = new_results

        return data, new_data
    except:
        print("\nInvalid Table file!")
        return ["NoTable"], ["NoTable"]

def compare_table(table, expected, formatted, shall_print):
    num_rows = len(table)
    matching_output = []
    does_it_match = False
    
    to_be_printed = []
    index_of_success = []
    all_indexes = 0

    matches = 0
    for truth_row in table:
        # Extract the inputs and outputs from the truth_table row
        truth_inputs = truth_row[1]
        truth_outputs = truth_row[3]

        for i, expected_row in enumerate(formatted):
            # Extract the inputs and outputs from the expected row
            expected_inputs = expected_row[0]
            expected_outputs = expected_row[1]
            # Check if the inputs and outputs match
            if truth_inputs == expected_inputs:
                matching_output.append(expected_outputs)
                if truth_outputs == expected_outputs:
                    index_of_success.append(i)
                    matches += 1
                    break
        all_indexes += 1

    if matches != num_rows:
        if(shall_print):
            print(f"Number of matches: {matches}/{num_rows}")
            print("The truth table does not match the expected table.")
            print("The following rows do not match the expected table:")
            for i, row in enumerate(expected):
                if i not in index_of_success:
                    print(row, "obtained output:", table[i][3])
        else:
            for i, row in enumerate(expected):
                if i not in index_of_success:
                    str_row = ' | '.join([' '.join(sublist) for sublist in row])
                    table_wanted = table[i][3]
                    for element in table_wanted:
                        if(element == '-'):
                            table_wanted[table_wanted.index(element)] = '1'
                    table_wanted = ' '.join(table_wanted)
                    to_be_printed.append(' '.join([str_row, '|', table_wanted]))

    else:
        if(shall_print):
            print("\nThe truth table matches the expected table.")
        does_it_match = True
    return matching_output, does_it_match, to_be_printed

def insert_expected_results_as_column(table, result_e, human_readable_version):
    new_table = []
    
    for i, item in enumerate(table):
        new_row = item.copy()  # Create a copy of the original row
        last_column = new_row.pop()  # Remove the last column
        new_row.append(result_e[i])  # Append the expected result to the new row
        new_row.append(last_column)  # Append the last column to the new row
        new_table.append(new_row)  # Add the new row to the new table
    
    return new_table

def convert_table_to_human_readable(table, has_expected):
    new_table = []
    input_names = table[0][1]
    for row in table:
        input = [1 if name in row[1] else 0 for name in input_names]
        input = ' '.join(map(str, input))
        #output = ' '.join(map(str, row[2]))
        result = ['1' if state == '-' else '0' for state in row[3]]
        result = ' '.join(map(str, result))
        expected = []
        if(has_expected):
            expected = ['1' if state == '-' else '0' for state in row[4]]
            expected = ' '.join(map(str, expected))
            energy = ' '.join(map(str, row[5]))
            new_table.append([row[0], input, result, expected, energy])
        else:
            energy = ' '.join(map(str, row[4]))
            new_table.append([row[0], input, result, energy])
    return new_table

def add_tab_to_table(table, has_expected):
    table_str = ""
    if has_expected:
        table_str = tabulate(table, headers=["File", "Inputs", "Outputs", "Expected", "Energy"], tablefmt="pretty")
    else:
        table_str = tabulate(table, headers=["File", "Inputs", "Outputs", "Energy"], tablefmt="pretty")
    # Add a tab character before each line
    tabulated_lines = table_str.split('\n')
    tabulated_lines = ['\t' + line for line in tabulated_lines]

    # Join the lines back together with newline characters
    table_str = '\n'.join(tabulated_lines)
    return table_str


def create_table(table, file_name):
    input_names = table[0][1]
    ttable = ""
    header_str = ' '.join(table[0][1]) + ' | ' + ' '.join(table[0][2])
    ttable += header_str + '\n'
    for row in table:
        inputs = [1 if name in row[1] else 0 for name in input_names]
        inputs = ' '.join(map(str, inputs))
        result = ['1' if state == '-' else '0' for state in row[3]]
        result = ' '.join(map(str, result))
        ttable += inputs + ' | ' + result + '\n'
    print ("Created table: ")
    print (ttable)

    with open(file_name, "w") as file:
        for line in ttable:
            file.write(line)


def table_presentation(truth_table, full_print):
    if(not full_print):
        truth_table = convert_table_to_human_readable(truth_table, has_expected=False)
        print(tabulate(truth_table, headers=["File", "Inputs", "Outputs", "Energy"], tablefmt="pretty"), "\n\n")
    else:
        truth_table = convert_table_to_human_readable(truth_table, has_expected=True)
        print(tabulate(truth_table, headers=["File", "Inputs", "Outputs", "Expected", "Energy"], tablefmt="pretty"), "\n\n")
    return


def executeFile(directory, file, num_instances=-1):
    #get wanted files
    selected_file = file    
    selected_txt = file.replace('.sqd', '.txt')
    selected_exp_table = file.replace('.sqd', '_table.txt')

    individual_directory = directory + selected_file.replace('.sqd', '')
    #print ("Individual directory: " + individual_directory)
    full_path = os.path.join(directory, selected_file)
    full_txt_path = os.path.join(individual_directory, selected_txt)
    full_exp_table_path = os.path.join(individual_directory, selected_exp_table)
    print(f"Executing file: {selected_file} + {selected_txt}")


    #Executing them
    change_header(full_path, True, num_instances)
    inputs, outputs = grab_DBs(full_txt_path)
    if(inputs == "None"):
        return
    expected, internal_expected = grab_table(full_exp_table_path)
    truth_table = combinations(inputs, outputs, 'modified_file.xml', True)
    if(expected[0] == "NoTable"):
        print("No table.txt found, Generating a basic one for you, please modify it later!")
        create_table(truth_table, full_exp_table_path)
    else:
        expected_result, does_it_match, _ = compare_table(truth_table, expected, internal_expected, True)
        if(not does_it_match):
            truth_table = insert_expected_results_as_column(truth_table, expected_result, expected)
            table_presentation(truth_table, True)
            return
    
    table_presentation(truth_table, False)
    return

def execute_extern(sqd, txt, expected_txt, num_instance):
    selected_file = sqd
    selected_txt = txt
    selected_exp_table = expected_txt
    change_header(selected_file, False, num_instance)
    inputs, outputs = grab_DBs(selected_txt)
    expected, internal_expected = grab_table(selected_exp_table)
    truth_table = combinations(inputs, outputs, 'modified_file.xml', False)
    if(expected[0] == "NoTable"):
       return "NoTable", False, []
    else:
        expected_result, does_it_match, to_be_printed = compare_table(truth_table, expected, internal_expected, False)
        if(not does_it_match):
            truth_table = insert_expected_results_as_column(truth_table, expected_result, expected)
            return truth_table, does_it_match, to_be_printed
    return truth_table, does_it_match, ["_"]

def sys_args_default():
    sqd = sys.argv[1]
    txt = sys.argv[2]
    table = sys.argv[3]

    truth_table, does_it_match, to_be_printed = execute_extern(sqd, txt, table, -1)
    if(truth_table == "NoTable"):
        print("-1")
        return
    if(does_it_match):
        print("1")
        table_presentation(truth_table, False)
    else:
        print("0")
        for line in to_be_printed:
            print(line)
        table_presentation(truth_table, True)

def sys_args_five():
    sqd = sys.argv[1]
    txt = sys.argv[2]
    table = sys.argv[3]
    num_instance = sys.argv[4]

    truth_table, does_it_match, to_be_printed = execute_extern(sqd, txt, table, num_instance)
    if(truth_table == "NoTable"):
        print("-1")
        return
    if(does_it_match):
        print("1")
        table_presentation(truth_table, False)
    else:
        print("0")
        for line in to_be_printed:
            print(line)
        table_presentation(truth_table, True)


def main():

    num_instances = -1
    if len(sys.argv) == 2:
        value = sys.argv[1]
        if(value == "-clean"):
            remove_files_in_directory('modified')
            remove_files_in_directory('result')
            print("Cleaned the folders!")
            return
        int_value = int(value)
        if(int_value >= 32):
            num_instances = int_value
        else:
            print("Invalid number of instances, must be bigger or equal 32!")
            return
    if len(sys.argv) == 4:
        sys_args_default()
        return 
    if len(sys.argv) == 5:
        sys_args_five()
        return

    directory = 'gates/'  # Replace with your directory path
    while(True):
        print("\tGATE CHECKER by Emanuel\n")
        print("Number of SimAnneal DB Instances:", num_instances)
        print("Enter 0 to Exit")
        print("Enter -1 to clean the folders")
        print("Enter -2 to change the number of instances")
        files = list_files_in_directory(directory)
        if not files:
            print("No files found in the directory.")
            return
        print("Available files:")
        for i, file in enumerate(files, 1):
            print(f"{i}. {file}")

        choice = input("Enter the number of the file you want to execute: ")

        try:
            choice = int(choice)
            if choice == -2:
                print("Type the number of instances (-1 or value bigger than 32): ")
                try:
                    num_instances_new = int(input())
                    if num_instances_new < 32:
                        print("Setting value to -1")
                        num_instances = -1
                        continue
                    num_instances = num_instances_new
                except ValueError:
                    print("Invalid input. Please enter a valid number.")
                    continue
            if choice == -1:
                remove_files_in_directory('modified')
                remove_files_in_directory('result')
                print("Cleaned the folders!")
                continue
            if choice == 0:
                return
            if 1 <= choice <= len(files):
                executeFile(directory, files[choice - 1], num_instances)
            else:
                print("Invalid choice.")
        except ValueError:
            print("Invalid input. Please enter a valid number.")

if __name__ == "__main__":
    main()