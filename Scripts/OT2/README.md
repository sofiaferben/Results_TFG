OT2
---
These are the scripts used to run protocols in Opentrons OT2.
- **phenotipation.py**: final script generated for the phenotyping protocol

The rest of the scripts were the ones used for the troubleshooting. 


In order to perform the protocol for phenotyping protocol perform the following steps:

**Requirements**: Python 3.7.6 (Windows x64, Windows x86, OS X) or higher on your local computer. 
1. Install opentrons Python Package. Refer to https://docs.opentrons.com/v2/writing.html#simulate-block
2. Download phenotyping.py and phenotyping_input.xlsx (https://github.com/sofiaferben/TFG/tree/main/OT2_files/Input_files_OT2)
3. Fill in phenotyping_input.xlsx and store it in path data/user_storage
4. Simulate the protocol to test it runs well:
   ```
   opentrons_simulate phenotyping.py
   ```
5. Simualate the protocol again to know where to place reagents this way:
  ```
   opentrons_simulate phenotyping.py
   ```


