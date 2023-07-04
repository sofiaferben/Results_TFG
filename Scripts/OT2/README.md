OT2
---
These are the scripts used to run protocols in Opentrons OT2.
- **phenotipation.py**: final script generated for the phenotyping protocol

The rest of the scripts were the ones used for the troubleshooting. 


In order to perform the protocol for phenotyping protocol perform the following steps:

**Requirements**: Python 3.7.6 (Windows x64, Windows x86, OS X) or higher on your local computer. 
1. Install opentrons Python Package. Refer to https://docs.opentrons.com/v2/writing.html#simulate-block
 ```
  pip install opentrons 
   ```
3. Download phenotyping.py and phenotyping_input.xlsx (https://github.com/sofiaferben/TFG/tree/main/OT2_files/Input_files_OT2)
4. Fill in phenotyping_input.xlsx and store it in path data/user_storage
5. Simulate the protocol to test it runs well:
   ```
   opentrons_simulate phenotyping.py
   ```
6. Simualate the protocol again to know where to place reagents this way:
   ```
   opentrons_simulate phenotyping.py -o nothing 
   ```
6. Upload XLSX file to OT2 via command line. Refer to:https://support.opentrons.com/s/article/Copying-files-to-and-from-your-OT-2-with-SCP . The command needed to do so is :
   ```
   scp -i ot2_ssh_key /path/on/computer/phenotyping_intput.xlsx root@ROBOT_IP:/data/user_storage

   ```
