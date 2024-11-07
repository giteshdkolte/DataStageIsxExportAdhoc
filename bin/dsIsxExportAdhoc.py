import yaml, os, subprocess, re
from tqdm import tqdm
from colorama import init, Fore, Style

# Initialize Colorama to work on Windows
init()

# Code by: Gitesh Kolte
# Description: The script will export the ISX for the jobs in a given project provided in the input file.

# Read YAML data from configurations.yaml
with open(r'..\config\configurations.yml', 'r') as file:
   yaml_data = yaml.safe_load(file)
# Access other keys in 'datastageLegacy'
datastage_legacy_data = yaml_data.get('datastageLegacy', {})
istoolPath = datastage_legacy_data['istoolPath']
isDomain = datastage_legacy_data['isDomain']
isUser = datastage_legacy_data['isUser']
isPwd = datastage_legacy_data['isPwd']
host = datastage_legacy_data['host']
isProject = datastage_legacy_data['isProject']
exportPath = datastage_legacy_data['exportPath']
exportListAdhoc = datastage_legacy_data['exportListAdhoc']
statusPath = datastage_legacy_data.get('statusPath')
statusFileAdhoc = datastage_legacy_data.get('statusFileAdhoc')
statusFilePath = os.path.join(statusPath, f'{isProject}{statusFileAdhoc}.csv')
isx_export_path = os.path.join(exportPath, "isx")

def istoolCommand(includeDep, master_seq, doubleQuottedJobPath):
    if includeDep.upper() == 'Y' :
        #istool command formation
        istool_command = [
                f"{istoolPath}\\istool.bat",
                "export",
                "-dom",
                f"{isDomain}",
                "-u",
                f"{isUser}",
                "-p",
                f"{isPwd}",
                "-ds",
                f"'-incdep {doubleQuottedJobPath}'",
                "-ar",
                f"{exportPath}\\isx\\{master_seq}.isx"   
            ]
        
    if includeDep.upper() == 'N' :
        #istool command formation
        istool_command = [
                f"{istoolPath}\\istool.bat",
                "export",
                "-dom",
                f"{isDomain}",
                "-u",
                f"{isUser}",
                "-p",
                f"{isPwd}",
                "-ds",
                f"'{doubleQuottedJobPath}'",
                "-ar",
                f"{exportPath}\\isx\\{master_seq}.isx"   
            ]
    
    #converting istool command from list to string
    command = ' '.join(istool_command)

    return command

# Create status file path if doesnot exists
os.makedirs(statusPath, exist_ok=True)

# Get the job details, export it and store in ISX directory
if os.path.isfile(exportListAdhoc):
    with open(f"{exportListAdhoc}") as srcTxtFile:
        with open(statusFilePath, 'w') as status:
            status.write('MasterAsset, Status\n')
        assetLst = [line.strip() for line in srcTxtFile.readlines() if line.strip()]
        if assetLst:
            # Create ISX Export file path if doesnot exists
            os.makedirs(isx_export_path, exist_ok=True)
            with tqdm(total=len(assetLst), bar_format='{desc} {percentage:3.0f}%|{bar:60}') as pbar:
                for idx, assetAndIncDEp in enumerate(assetLst, start=1):
                    assetName, incDep = assetAndIncDEp.split('|')
                    assetName, incDep = assetName.strip(), incDep.strip()
                    # Setting tqdm description
                    pbar.set_description(f"ISX Export initializing for {Fore.YELLOW}{assetName}{Style.RESET_ALL} [{idx}/{len(assetLst)}]")
                    # Call subprocess
                    doubleQuottedJobPath = f'"{host}/{isProject}/*/{assetName}.*"'
                    command = istoolCommand(incDep, assetName, doubleQuottedJobPath)
                    try:
                        result = subprocess.run(command, check=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                        with open(statusFilePath, 'a') as status:
                            if result.returncode == 0:
                                status.write(f'{assetName}, Success\n')
                    except subprocess.CalledProcessError as e:
                        with open(statusFilePath, 'a') as status:
                            status.write(f'{assetName}, Failed\n')
                        # Delete the  XML file which was created but failed to be added to status file
                        pattern = rf".*{assetName}.*"
                        # Remove the files which falls under error
                        for root, dirs, files in os.walk(isx_export_path):
                            for file in filter(lambda x: re.match(pattern, x), files):
                                os.remove(os.path.join(root, file))

                    pbar.update()
            print(f"\nExport process completed. Please refer to the path {Fore.GREEN}{isx_export_path}{Style.RESET_ALL} to get the ISX/s\nStatus File Path: {Fore.GREEN}{statusFilePath}{Style.RESET_ALL}")
else:           
    print(f"Error opening the file: {Fore.RED}{exportListAdhoc}{Style.RESET_ALL}")
