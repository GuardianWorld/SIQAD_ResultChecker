import xml.etree.ElementTree as ET
import itertools
from copy import deepcopy
import os
import sys
import math
import subprocess
from datetime import datetime
from tabulate import tabulate


def change_header(file):
    print("Making modified Header file for Simulation", end = '\r')
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
    root.insert(1, new_sim_params)
        
    sim_params = root.find(".//sim_params")
    if(sim_params is not None):
        root.remove(sim_params)
    else:
        print("No SIM_PARAMS element found")

    root.insert(1, new_sim_params)

    # Save the modified XML to a file
    tree.write('modified_file.xml', encoding='utf-8', xml_declaration=True)

def call_simmaneal(file, result_name):
    resultPath = " ./result/" + result_name
    command = " ./simanneal/simanneal " + file + resultPath
    print("Calling Simanneal for file: " + file + " please wait!", end='\r')
    sys.stdout.flush()
    subprocess.run(command, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def grab_DBs(db_file):
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

def combinations(dbdot_coordinates, output_coordinates, file):
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
        call_simmaneal(f'modified/modified_file_{i}.xml', f'result_{i}.xml')
        result = read_result(f'./result/result_{i}.xml', output_coordinates)

        opposite_names = [name for _, _, _, name in opposite_combination]
        #result_names, result_values, result_energy = zip(*[(name_output, value, energy) for name_output, value, energy in result])
        result_names = [name_output for name_output, _, _ in result]
        result_values = [value for _, value, _ in result]
        result_energy = [energy for _, _, energy in result]
        result_name = f'result_{i}.xml'
        truth_table.append([result_name,opposite_names, result_names, result_values, result_energy])
        i += 1

    return truth_table

def list_files_in_directory(directory):
    sqd_files = [f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f)) and f.endswith('.sqd')]
    return sqd_files

#This part of the code will be responsable for grabbing
#(or telling the program that it needs to generate for future runs)
#The expected table;

def grab_table(table_file):
    if(not os.path.isfile(table_file)):
        return ["NoTable"]
    
    data = []
    with open(table_file, "r") as file:
        for line in file:
            parts = line.strip().split(" | ")
            inputs = [inp.strip("'") for inp in parts[0].strip('[]').split(', ')]
            outputs = [out.strip("'") for out in parts[1].strip('[]').split(', ')]
            results = [res.strip("'") if res.strip("'") else '""' for res in parts[2].strip('[]').split(', ')]
            data.append([inputs, outputs, results])

    return data

def compare_table(table, expected):
    inputs_t = []
    outputs_t = []
    results_t = []

    inputs_e = []
    outputs_e = []
    results_e = []

    expected = [[[] if e == [''] else e for e in item] for item in expected]

    for item in table:
        inputs_t.append(item[1])
        outputs_t.append(item[2])  
        results_t.append(item[3])

    for item in expected:
        inputs_e.append(item[0])
        outputs_e.append(item[1])  
        results_e.append(item[2])
    
    for i, (inputs1, outputs1, results1, inputs2, outputs2, results2) in enumerate(
        zip(inputs_t, outputs_t, results_t, inputs_e, outputs_e, results_e)
    ):
        if inputs1 != inputs2 or outputs1 != outputs2 or results1 != results2:
            print(f"Row {i + 1}: Mismatch")
            print(f"   Inputs:   {inputs1} (expected {inputs2})")
            print(f"   Outputs:  {outputs1} (expected {outputs2})")
            print(f"   Results:  {results1} (expected {results2})")
        
    return results_e
        


def write_table(table_file, table):
    with open(table_file, "w") as file:
        for item in table:
            inputs = item[1]
            outputs = item[2]  
            results = item[3]
            file.write(f"{inputs} | {outputs} | {results}\n")  # Write to the file

def insert_expected_results_as_column(table, result_e):
    new_table = []
    
    for i, item in enumerate(table):
        new_row = item.copy()  # Create a copy of the original row
        last_column = new_row.pop()  # Remove the last column
        new_row.append(result_e[i])  # Append the expected result to the new row
        new_row.append(last_column)  # Append the last column to the new row
        new_table.append(new_row)  # Add the new row to the new table
    
    return new_table

def executeFile(directory, file):
    #get wanted files
    selected_file = file
    selected_txt = file.replace('.sqd', '.txt')
    selected_exp_table = file.replace('.sqd', '_table.txt')
    full_path = os.path.join(directory, selected_file)
    full_txt_path = os.path.join(directory, selected_txt)
    full_exp_table_path = os.path.join(directory, selected_exp_table)
    print(f"Executing file: {selected_file} + {selected_txt}")


    #Executing them
    change_header(full_path)
    inputs, outputs = grab_DBs(full_txt_path)
    expected = grab_table(full_exp_table_path)
    truth_table = combinations(inputs, outputs, 'modified_file.xml')
    #truth_table.reverse()
    if(expected[0] == "NoTable"):
        write_table(full_exp_table_path, truth_table)
        print("No table.txt found, generating one for you, please modify it and run again later!")
        print(tabulate(truth_table, headers=["File", "Inputs", "Outputs", "State", "Energy"], tablefmt="pretty"))
    else:    
        expected_result = compare_table(truth_table, expected)
        truth_table = insert_expected_results_as_column(truth_table, expected_result)
        print(tabulate(truth_table, headers=["File", "Inputs", "Outputs", "State", "Expected", "Energy"], tablefmt="pretty"))

def main():
    directory = 'gates/'  # Replace with your directory path

    while(True):
        print("GATE CHECKER by Emanuel\n")
        files = list_files_in_directory(directory)
        if not files:
            print("No files found in the directory.")
            return
        print("Available files:")
        for i, file in enumerate(files, 1):
            print(f"{i}. {file}")

        print("\nEnter 0 to Exit")
        choice = input("Enter the number of the file you want to execute: ")

        try:
            choice = int(choice)
            if choice == 0:
                return
            if 1 <= choice <= len(files):
                executeFile(directory, files[choice - 1])
            else:
                print("Invalid choice.")
        except ValueError:
            print("Invalid input. Please enter a valid number.")

if __name__ == "__main__":
    main()