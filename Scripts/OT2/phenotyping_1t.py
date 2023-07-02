import opentrons
from opentrons.protocol_api.labware import Well
from opentrons import types 
import math 
import pandas as pd 
from prettytable import PrettyTable

metadata = {
    'apiLevel': '2.13',
    'author': 'Sofia Ferrandez'
    'name: TFG'
    }

class WellH(Well): #new subprupo de well 
    """
    Class type which inherits from opentrons.protocol_api.labware.Well
    Made to track the height from where to aspirate volume in falcons, because pipettes get wet if they 
    go down no default height. 
    
    """
    def __init__(self, well, height=0, min_height=0,
                     comp_coeff=0, current_volume=0): #default 15ml python
        super().__init__(well, well._core, well.api_version)
        self.well = well 
        self.height = height #height of the liquid
        self.min_height = min_height #min height you want the liquid to have
        self.comp_coeff = comp_coeff 
        self.radius = self.diameter/2 #falcon radius
        self.current_volume = current_volume #liquid current volume 

    #Methods 
    def compute_original_height_and_comp_coeff(self): 
        """
        Given the current volume returns the original height of the falcon. It also sets the proper
        comp_coeff for each type of falcon. There are errors of 2mm because it is aprrximate, 
        it does it job  --> that the pipette doesn't get wet. 
        """
        if self.depth==117.5: #is a 15ml falcon : opentrons_15_tuberack_falcon_15ml_conical
            self.comp_coeff=1.15 
            if self.current_volume>1000:
                self.height=round(25+((self.current_volume-1000)/(math.pi*(self.radius**2))),0)
                #just takes into account the cilinder 
                #1ml --> 23mm
            else: 
                self.height=23 #will not be problems with wert pipette 
        if self.depth==113: #is a 50ml falcon
            self.comp_coeff=1.2
            if self.current_volume>5000: 
                self.height=20+((self.current_volume-5000)/(math.pi*(self.radius**2)))
            else:
                self.height=20 #will not be problems with wet pipette
                
    def update_height_volume_dec(self,vol):
        """
        Update height and volume if the falcon is being aspirated volume 

        Parameters
        ----------
        vol : int
            volume that is going to be aspirated.
        """
        dh = (vol/(math.pi*(self.radius**2)))*self.comp_coeff
        if self.height - dh > self.min_height: #updates height 
            self.height = self.height - dh
        else:
            self.height = self.min_height
        if self.current_volume - vol > 0: #updates volume 
            self.current_volume = self.current_volume - vol
        else:
            self.current_volume = 0

    def update_height_volume_inc(self,vol):
        """
        Update height and volume if the falcon is being dispense volume 

        Parameters
        ----------
        vol : int
            volume that is going to be aspirated.
        """
        dh = (vol/(math.pi*(self.radius**2)))*self.comp_coeff
        if self.height + dh < self.depth:
            self.height = self.height + dh
        else:
            self.height = self.depth
        self.current_volume += vol

    def z_tracking_falcon_dec(self,vol,pip):
        """
        If falcon is going to decrease volume, returns z  at which the pipette will be aspirated


        Parameters
        ----------
        vol : int
            volume that is going to be aspirated.
        pip : opentrons.protocol_api.instrument_context.InstrumentContext.

        """
        self.update_height_volume_dec(vol)

        
        if pip.name=='p20_single_gen2'  or pip.name=='p20_multi_gen2': 
            if self.height>20: 
                z=self.height-10-self.well.bottom().point.z #10mm deeper, so that if volume if volume is very high, liquid doesn´t spill out of the falcon
            else:
                z=1

        if pip.name=='p300_single_gen2' or pip.name=='p300_multi_gen2': 
            if 25<self.height: #>2cm height --> might be problems with wet pipette 
                z=self.height-10-self.well.bottom().point.z #8mm cm deeper, so that if volume if volume is very high, liquid doesn´t spill out of the falcon
            else:
                z=1

        if pip.name=='p1000_single_gen2':
            if 40<self.height: #>1.5cm height --> might be problems with wet pipette
                z=self.height-20-self.well.bottom().point.z #12 mm deeper, so that if volume if volume is very high, liquid doesn´t spill out of the falcon
            else:
                z=1 ##deja volumen
        return self.well.bottom(z=z)


    def z_tracking_falcon_inc(self,vol,pip): ##OJO no optimizada luego copias valores y <=
        """
        If falcon is going to increase volume, calculates de z from where the pipette is going to aspirate
        Parameters
        ----------
        vol : int
            volume that is going to be aspirated.
        pip : opentrons.protocol_api.instrument_context.InstrumentContext.
        
        """
        self.update_height_volume_inc(vol)


        if pip.name=='p20_single_gen2':
            z=self.height +self.well.bottom().point.z+5 
        if pip.name=='p300_single_gen2':
            z=self.height+self.well.bottom().point.z+8 
        if pip.name=='p1000_single_gen2':
            z=self.height+self.well.bottom().point.z +12 
        return self.well.bottom(z)


### Custom distribute for wellH
def distribute_from_WellH_to_well(vol,s:WellH,d,pip,protocol,new_tip='never',disposal_volume=0):
        """
        Custome distribute function to distribute with z (height) tracking ofo WellH

        Parameters
        ----------
        vol : int 
            volume to dispense/well.
        s : WellH
            WellH (normally falcon), from where to aspire from. 
        d : well, type 'opentrons.protocol_api.labware.Well' or list or list of list
            Well or list of wells to distribute to.
        protocol: opentrons.protocol_api.ProtocolContext
        pip : pipette, type 'opentrons.protocol_api.instrument_context.InstrumentContext'
            Pipette used during de command
        new_tip : string, optional
            Wether to get a new tip for each well. The default is 'never'.
        disposal_volume: 0, optional
            Extra volume aspired by the pieptte to be more eaxct. The default is 0.


        """
        #Step 1: Pick up tip if there is no tip
        if new_tip=='never' and not pip.has_tip: 
                pip.pick_up_tip()  
        
        protocol.comment(f'Initial source height: {round(s.height, 2)}mm, initial volume {round(s.current_volume, 2)}')

        #Step 2: getting the number of well to distribute to
        if isinstance(d,opentrons.protocol_api.labware.Well): #if only one well
            #not much sense distirbuting into one well only
            z_source=s.z_tracking_falcon_dec(vol,pip)
            pip.transfer(vol,z_source,d,new_tip=new_tip,disposal_volume=disposal_volume)
            protocol.comment(f'Source height: {round(s.height, 2)}mm, volume: {round(s.current_volume, 2)}, Position from where pipette aspires: {round(z_source.point.z,2)} mm')
        if isinstance(d,list): #more than one well
            if isinstance(d[0],opentrons.protocol_api.labware.Well): #if d is a normal list
                length=len(d)
                wells_left_list=d
            if isinstance(d[0],list): #if d is a list of list --> .columns() / .rows()
                length = sum([len(listElem) for listElem in d])

                #create a list with al the wells  --> easier to deal with when looping
                wells_left_list=[]
                for column in d: 
                    for well in column:
                        wells_left_list.append(well)



            #Step 3: extra ul/dispense in each type of pipette
            if pip.name=='p300_single_gen2': #extra 20ul/aspirate
                #extra=20
                #max_per_dist=280 #por ahora sin blow out
                max_per_move=300

            if pip.name=='p1000_single_gen2': #extra 100ul/aspirate
                #extra=100
                #max_per_dist=900
                max_per_move=1000

            
            #Step 4: optimize distribute , thx to length
            total_volume=length*vol
            max_wells_per_move=max_per_move//vol
            whole_moves=length//max_wells_per_move
            rest_wells=length%max_wells_per_move

            #prints
            #print('total volume ', total_volume)

            #foor loop distributing 
            start=0
            for i in range(whole_moves):
                z_source=s.z_tracking_falcon_dec(max_per_move,pip)
                pip.distribute(vol,z_source,wells_left_list[start:(start+max_wells_per_move)],new_tip=new_tip,disposal_volume=disposal_volume)
                #for next distribute, calculate wells to distribute
                #print(f'Source height: {round(s.height, 2)}mm, volume: {round(s.current_volume, 2)}, Position from where pipette aspires: {round(z_source.point.z,2)} mm')
                start=start+max_wells_per_move
            
            z_source=s.z_tracking_falcon_dec((vol*rest_wells),pip)
            if wells_left_list[(length-rest_wells):length]!=[]:
                pip.distribute(vol,z_source,wells_left_list[(length-rest_wells):length],new_tip=new_tip,disposal_volume=disposal_volume)


class EppV(Well):
    """
    Class type which inherits from opentrons.protocol_api.labware.Well
    Tracks how much volume of an eppendorf is left so to know if there is more than one eppendorf for each reagent to kwno from where to aspire
    """
    def __init__(self, well,min_volume=40,current_volume=0,max_volume=0): 
        super().__init__(well, well._core, well.api_version)
        self.well = well 
        self.min_volume = min_volume
        self.current_volume = current_volume #volume
    #Methods 
    def update_volume_dec(self,vol):
        """
        updates the volume of the eppendorf it is is bieng aspired from 
        Parameters
        ----------
        vol  : int
        volume that will be aspited from eppendorf
        """
        self.current_volume=self.current_volume-vol
    
    def update_volume_inc(self,vol):
        """
        updates the volume of the eppendorf it is is bieng dispensed to  
        Parameters
        ----------
        vol  : int
        volume that will be aspited from eppendorf
        """
        self.current_volume=self.current_volume+vol
        

def choose_EppV(list_EppV,vol):
    """
    From a list of EppV choose which EppV to use, the one that can get the next volume 

    

    Parameters
    ----------
    list_EppV : list
        list of EppV types.
    vol : int
        volume that needs to be aspired in next volume
     Returns
    -------
    epp_final : EppV
        Eppendrof that has enough volume to be aspired next volume from  

    """

    for epp in list_EppV:
        if (epp.current_volume-vol)>epp.min_volume:
            epp_final=epp
            break 
    #print(epp_final.current_volume)
    epp_final.update_volume_dec(vol)
    #print('dentro de funcion choose_EppV: epp_final current volume es %s'%epp_final.current_volume)
    return epp_final

def eppV_source(list_volumes, list_eppV,protocol):
    """
    From a list of eppV and a list of volumes return which track which eppV will be used for which volumes
    
    Parameters
    ----------
    list_volumes : list
        list of volumes that have to be aspired.
    list_eppV : list
        list of possible EppV to get volume from 
    protocol : opentrons.protocol_api.ProtocolContext


    Returns
    -------
    dicc_eppV : dict
        keys are EppV and values are a list of the volumes the volumes to be taken from this eppendorf 
    """
   
    dicc_eppV = {}
    temp_vol = list_volumes[:]
    for eppV in list_eppV:
        list_vol = []
        final_vol = 0
        for volume in temp_vol:
            final_vol += volume
            if (eppV.current_volume - final_vol) >= eppV.min_volume:
                list_vol.append(volume)
            else:
                break
        dicc_eppV[eppV.well] = list_vol
        temp_vol = temp_vol[len(list_vol):]
        eppV.update_volume_dec(sum(list_vol))
        #print('volume of well %s after volumes is %s'%(eppV.well,eppV.current_volume))
    return dicc_eppV


    
####Funciones
#1)
def drop_tips(pip_left,pip_right):
    """
    drop tips from both pipettes

    Parameters
    ----------
    pip_left and pip_right: opentrons.protocol_api.instrument_context.InstrumentContext
    """
    for pipette in [pip_left,pip_right]:
        if pipette.has_tip==True:
            pipette.drop_tip()
    return

def vi(ci,cf,vf):
    """
    return initial volume needed (vi) to get to a final concentration (cf) in a final volume (vf)  from an intial conentration (ci )   

    Parameters
    ----------
    ci : int
        initial concentration.
    cf : int
        final concentration.
    vf : int
        final volume.

    Returns
    -------
    vi : TYPE
        initial volume.

    """
    vi=(vf*cf)/ci
    return vi

def shake(shaker,protocol,speed,seconds):
    """
    shakes Heater-Shaker Gen1 and rpms and seconds specified 
    
    Parameters
    ----------
    shaker : opentrons.protocol_api.module_contexts.HeaterShakerContext
        Heater-Shaker Gen1.
    protocol : opentrons.protocol_api.ProtocolContext
    speed : int
        rpm to mix Heater-Shaker Gen1.
    seconds : int
        seconds to mix in Heater-Shaker Gen1.
    -----------
    """

    shaker.set_and_wait_for_shake_speed(speed)
    protocol.delay(seconds=seconds)
    shaker.deactivate_shaker()


#3)
def divide_distributes(list_v,pip_left,pip_right):
    """
    From a lsit of volumes divides them into the pipettes that can get such volume
    
    Parameters
    ----------
    list_v : list
        list of volumes to divide 
    pip_left & pip_right : opentrons.protocol_api.instrument_context.InstrumentContext
        lest and right pieptte respectevely 
    Returns
    -------
    dicc_pips : dict
        Keys are the pipettes and values a lsit of the volumes that will get 

    """

    if pip_left.max_volume<pip_right.max_volume:
        threshold=pip_left.max_volume
        pip_threshold=pip_left
        other_pip=pip_right

    else:
        threshold=pip_right.max_volume
        pip_threshold=pip_right
        other_pip=pip_left
    less_than_th =  []
    greater_than_th = []
    for vol in list_v:
        if vol<=threshold:
            less_than_th.append(vol)
        else:
            greater_than_th.append(vol)
    dicc_pips={
        pip_threshold : less_than_th ,
        other_pip : greater_than_th 
    }
    return dicc_pips
            
            
def get_right_pipette(volume,pip_left,pip_right):
    """
    Depending on the volume  that need to be apspired picks up the right pipette 

    Parameters
    ----------
    volume : int
        volume that we want to aspire.
    pip_left & pip_right :  opentrons.protocol_api.instrument_context.InstrumentContext

    Returns
    -------
    pip :  opentrons.protocol_api.instrument_context.InstrumentContext
        The pieptte that will be used to take this volum .

    """
   
    #Step 1: Define the threshold and pipetttes acroding to it 
    if pip_left.max_volume<pip_right.max_volume:
        threshold=pip_left.max_volume
        pip_threshold=pip_left
        other_pip=pip_right
    else: 
        threshold=pip_right.max_volume
        pip_threshold=pip_right
        other_pip=pip_left

    #Step 2: Check which pipette to use 
    if volume<threshold:
        pip=pip_threshold
        if 0<volume<pip_threshold.min_volume:
            print('***ErrorThe volume is less than the pipettes can get**')
    else: 
        pip=other_pip

    return pip   

def excel_to_dict(file_path,sheet_name):
    """
    Preprocess XLSX file to  make diccs of of each sheet 

    Parameters
    ----------
    file_path : name ot the XLSX file to get information from 
        DESCRIPTION.
    sheet_name : str
        Sheet from the XLSX file to generate a dict from 

    Returns
    -------
    result_dicc : dict
        dict to iterate thorugh that has info of XLSX file

    """
    
    df = pd.read_excel(file_path,sheet_name=sheet_name,engine='openpyxl')
    df.dropna(inplace=True)
    result_dict = {}
    for key, values in df.iterrows():       
        result_dict[values[0].rstrip()] = []
        #print(result_dict)
        # Loop over the values of each row starting from the second column
        for column_name, value in values.iloc[1:].items(): #this converts booleans to 0/1
            if isinstance(value,str): #get rid of  one problem with string typo 
                value=value.rstrip()
            # First we are going to deal with the possible boolean values 
            if column_name == 'Needs antibiotics':
                if isinstance(value,str):
                    if value.lower()=='true':
                        value=True
                    elif value.lower()=='false':
                        value=False
                if isinstance(value,int):
                    if value==0:
                        value=False
                    if value==1:
                        value=True
                result_dict[values[0]].append(value)

            elif column_name =='Name Antibiotics':
                if isinstance(value,int):
                    if value==0:
                        value=False
                    if value==1:
                        value=True
                    result_dict[values[0]].append(value)
                if isinstance(value,str):
                    #this value could remain as string, if this colony does need antibiotic 
                    if value.lower()=='false':
                        value=False
                        result_dict[values[0]].append(value)
                    else: #if there are no typos this means this colony needs antibiotic
                        result_dict[values[0]].append([str(v) for v in value.split(",")])


            #Second, whe are going to deal when with the case of only needing one concentration in inductor_dilution sheet in column 'Concentrations (same concentration as stock inductor)'
            elif column_name =='Concentrations (same units as stock inductor)':
                if isinstance(value,int) or isinstance(value,float):
                    result_dict[values[0]].append([float(value)])
                if isinstance(value,str) and "," in value:
                    try: #to deal with more than one concentrations 
                        result_dict[values[0]].append([float(v) for v in value.split(",")])
                    except:
                        raise Exception('\nError: Column "Concentrations (same units as stock inductor)"" in sheet "inductor_dilutions" is not properly written')
            #Third deal with the name of dilutions in sheet 'relation_colonies_inductors'
            elif column_name=='Dilutions of the colony':
                result_dict[values[0]].extend([v for v in value.split(",")])
              
            else:
                result_dict[values[0].rstrip()].append(value)

    return result_dict 




def preprocess_diccs(dicc_inductor,dicc_colonies,dicc_relation):
    """
    Preprocess diccs to mke it functional for the protocol. Previously they were formatted to be easy to hadle for user
    
    Parameters
    ----------
    dicc_inductor,dicc_colonies,dicc_relation: dict

    """
    #Change 1 
    dicc_relation_rows={'A':0,'B':1,'C':2,'D':3,'E':4,'F':5,'G':6,'H':7}
    for colony, ind_colonies in dicc_relation.items():
        initial_c,final_c,plate_number,type_medium,use_antibiotics,name_antibiotics=dicc_colonies[colony]
        list_params=[initial_c,final_c,plate_number,type_medium,use_antibiotics,name_antibiotics]
        for ind in ind_colonies:
            values_inductor=dicc_inductor[ind]
            type_inductor=values_inductor[0]
            column_py=values_inductor[4]-1
            row_py=dicc_relation_rows[values_inductor[5]]
            ##First append type of medium  and type of inductor to use in dilutions 
            if use_antibiotics==True:
                type_medium= type_medium + ' with'
                type_inductor= type_inductor + ' with'
                for anti in name_antibiotics:
                    type_medium= type_medium + ' 2x ' + anti
                    type_inductor=type_inductor+ ' 2x ' + anti

            
            #convert params Of dicc_inductor
            values_inductor.append(type_medium) #append type of medium 
            values_inductor.pop(0) #append type of inductor
            values_inductor.insert(0,type_inductor)
            values_inductor.pop(4) #change column 
            values_inductor.insert(4,column_py)
            values_inductor.pop(5) #change row 
            values_inductor.insert(5,row_py)
        list_params.pop(4)
        list_params.pop(4)
        dicc_colonies[colony]=list_params
    return

def split_list(lst, threshold):
    """
    splits the input list into multiple sublists such that the sum of each sublist
    is not greater than a given threshold
     Parameters
    ----------
    lst: list
     list of volumes to split into smaller volumes
    threshold: int
     max volume 

    """

    # Initialize a list to hold the sublists
    sublists = []

    # Initialize the current sublist and its sum
    curr_sublist = []
    curr_sum = 0

    # Iterate through the sorted list and add values to sublists
    for val in lst:
        if curr_sum + val <= threshold:
            curr_sublist.append(val)
            curr_sum += val
        else:
            # Add the current sublist to the list of sublists
            sublists.append(curr_sublist)

            # Start a new sublist with the current value
            curr_sublist = [val]
            curr_sum = val

    # Add the last sublist to the list of sublists
    sublists.append(curr_sublist)

    return sublists


def run(protocol: opentrons.protocol_api.ProtocolContext):
    ###### Run of the protocol


    #------ LAS POSCIONES CAMBIAN SI LA MULTI ES LA DE 300 MODIFICAR ESTO
    #------- AUNQUE NO SE SI EL PROTOCOLO FUNCIONARIA CON UNA DE 300 
  
    positions_tips_single=[11,1,2,3,4,5,6,7,8,9]
    positions_eppendorf=[8,9,4,5,6]
    positions_falcon=[8,9,1,2,3,4,5,6]
    positions_plate=[1,2,3]
    positions_tips_multi=[4,5,6]


    dicc_positions_labware={
        'tiprack single': positions_tips_single ,
        'eppendorf' : positions_eppendorf ,
        'falcon' : positions_falcon ,
        'plate' :positions_plate ,
        'tiprack multi' : positions_tips_multi
    }

    
    num_channels=0
    tips_ordered_multi=''
    tip_count_single=0
    tip_count_multi=0
    column_multi=0
    dicc_vol_medium={}
    dicc_vol_inductor={}
    dicc_vol_colonies={}
    dicc_positions_eppendorf={}
 


   

    ### Function definition  nside run because they need nonlocals 
    def pick_up(pip):
        """

        """

        nonlocal tip_count_multi # The nonlocal keyword is used to work with variables inside nested functions, where the variable should not belong to the inner function.
        pip.pick_up_tip(tips_ordered_multi[tip_count_multi])
        tip_count_multi += 1

    def pip_sum_tips(pip):
        """
        sums number of tips used for pipette 
        """
        nonlocal tip_count_multi
        nonlocal tip_count_single

        if pip.channels==8:
            tip_count_multi+=1
        if pip.channels==1:
            tip_count_single+=1
        
        return 
      

    def import_dicc_general_info(dicc_inductor,dicc_colonies,dicc_relation,protocol):
        
        """
        1) Process general_information excel sheet to process general info 
        2) Organise deck, dividing labware into : heater-shaker , tipracks_20 , tip_racks_300, eppendorf_rack , plates
        and add them to dicc_general
        
        """

        ##STEP 1: Process general_information excel sheet 
        #df = pd.read_excel('/data/user_storage/test_water.xlsx',sheet_name=0,engine='openpyxl')
        df = pd.read_excel('test_water.xlsx',sheet_name=0,engine='openpyxl')
        df = df.drop(df.columns[2], axis=1)
        df.dropna(inplace=True)


        dicc_general = {}
        for index, row in df.iterrows():
            if row[0] == 'Fill empty columns with water':
                value=row[1]
                if isinstance(value,str): #if user did a typo and didint correctly input a boolean 
                    value=row[1]
                    if value.lower()=='true':
                        value=True
                    elif value.lower()=='false':
                        value=False
                elif value==1: #if user correctly typed True boolean, but .iterrows() turns into 1 
                    value=True
                dicc_general[row[0]]=value
            else:
                if isinstance(row[1],str):
                    dicc_general[row[0]] = row[1].rstrip()
                else:
                    dicc_general[row[0]] = row[1]


        ##Step 2: Make variables out of the info at this dicc
        ##load pipettes (store them in dicc_general) and check at least one is 8-channel:
        dicc_general['pip left']=protocol.load_instrument(dicc_general['Name Left Pipette'],'left')
        dicc_general['pip right']=protocol.load_instrument(dicc_general['Name Right Pipette '],'right')


        if dicc_general['pip left'].channels==1 and dicc_general['pip right'].channels==1:
            raise Exception('\n\nError: Both channels are single channel, this protocol needs one single channel pieptte and one multichannel pipette. The protocol has been though so that the multi channel maximum volume is less than the single channel maximum volume.')
        if dicc_general['pip left'].channels==8 and dicc_general['pip right'].channels==8:
            raise Exception('\n\nError: Both channels are multi channel, this protocol needs one single channel pieptte and one multichannel pipette. The protocol has been though so that the multi channel maximum volume is less than the single channel maximum volume.')



        return dicc_general
 
    def calculate_initial_stocks(dicc_inductor,dicc_colonies,dicc_relation,V_final,pip_left,pip_right,dicc_vol_medium,dicc_vol_colonies,dicc_vol_inductor):
        """
        Calculales dilutions of colonies and inductor needed in the deep well  
        
        Parameters
        ----------
        dicc_inductor , dicc_colonies , dicc_relation : dict of info of inductors, colonies and relation between them 
            DESCRIPTION.
        V_final : int , final volume in each well of final plates 
        pip_left , pip_right :  opentrons.protocol_api.instrument_context.InstrumentContext
        dicc_vol_medium , dicc_vol_colonies , dicc_vol_inductor : dict, total volumes for each reagent 
        Returns
        -------
        colonies_stocks : dict, dict of volumen for each dilution of colonies of deep wells 
        dicc_ind_together : dict, dict of volumes for each dilutions of inductors of deep wells 

        """


        ##Step 1) Medium x antibiotic + colonies
        colonies_stocks={}
        for colony, params in dicc_colonies.items():
            od_cultivo,od_inicial,plate_number,type_medium = params


            #Calculate n_wells
            n_replicates=0
            list_inductors=dicc_relation[colony]
            extra=0
            for inductor in list_inductors:
                params_inductor=dicc_inductor[inductor]
                n=params_inductor[2]*len(params_inductor[3])
                n_replicates=n_replicates+params_inductor[2]
                extra+=len(params_inductor[3]) #for the blank 
            
            if len(params_inductor[3])==8:
                column_wells=len(params_inductor[3])
            else:
                column_wells=extra

            ##put in dictionary just the volumes per well in deep well
            if len(params_inductor[3])==8: 
                volume_2x_deep_well=(V_final/2)*(n_replicates+1) ##suponiendo que va en columnas para el blanco mal 

            else:  ##blank different extra 
                volume_2x_deep_well=(V_final/2)*(params_inductor[2]+1)

            od_stock=od_inicial*2
            vi_colony_deep_well=vi(od_cultivo,od_stock,volume_2x_deep_well)
            vi_medium_deep_well=volume_2x_deep_well-vi_colony_deep_well
            colonies_stocks[colony]=[volume_2x_deep_well,vi_colony_deep_well,vi_medium_deep_well]

            ##Append to dicc_vol_colonies all the individual volumes that will be asked to from medium 
            ##fist, append to dicc_vol_colonies ind transfer
            if colony not in dicc_vol_colonies.keys():
                dicc_vol_colonies[colony]=[vi_colony_deep_well]*column_wells
    
            #Second, append to dicc_vol_medium ech ind trans of medium ,
            if type_medium not in dicc_vol_medium.keys():
                dicc_vol_medium[type_medium]=[vi_medium_deep_well]*column_wells
            else:
                ant_list=dicc_vol_medium[type_medium]
                ant_list.extend([vi_medium_deep_well]*column_wells)


        # #Step 2) Dilutions of Inductors

        dicc_ind_together={}


        for ind,values in dicc_inductor.items():
            name_inductor,stock,n_replicates,concentrations,column_plate_dilutions,row_plate_dilutions,name_medium=values
            if name_medium not in dicc_ind_together.keys():
                dicc_ind_together[name_medium]={}
            dicc_inside=dicc_ind_together[name_medium]
            if name_inductor not in dicc_inside:
                dicc_inside[name_inductor]={}
            dicc_inside_inside=dicc_inside[name_inductor]
            if concentrations in dicc_inside_inside.values():
                swapped_dict = {str(value): key for key, value in dicc_inside_inside.items()}
                key= swapped_dict[str(concentrations)]
                new_key=key+ (ind,)
                dicc_inside_inside[new_key] = dicc_inside_inside.pop(key)
            if concentrations not in dicc_inside_inside.values():
                dicc_inside_inside[(ind,)]=concentrations #make a tuple so there are no problems while iterating 


        ##Now that we have the dictionary iterate so to calculate de volumes of each liquid depending on how much wells to use
        for medium, dicc_inside in dicc_ind_together.items():
            for ind_stock,dicc_inside_inside in dicc_inside.items():
                #ind_vol=0
                for tuple_ind , concentrations in dicc_inside_inside.items():
                    n_replicates=0
                    for ind in tuple_ind:
                        values=dicc_inductor[ind]
                        stock_inductor=values[1]
                        n_replicates+=values[2]
                    new_list=[]
                    for conc in concentrations:
                        volume_total=(n_replicates+1)*(V_final/2)
                        v_ind=vi(stock_inductor,conc*2,volume_total)
                        if 0<v_ind < 1:
                           raise Exception("Error: Can not get it with p20, several options:\n\t1)Decrease stock of inductors\n\t2)Increase concentrations of the dilutions")
                        #ind_vol+=v_ind

                        #Append volume of inductor needed in dicc_vol_inductor
                        if ind_stock not in dicc_vol_inductor.keys():
                            dicc_vol_inductor[ind_stock]=[v_ind]
                        else:
                            ant_list=dicc_vol_inductor[ind_stock]
                            ant_list.append(v_ind)
                            dicc_vol_inductor[ind_stock]=ant_list
                        v_medium=volume_total-v_ind
                        
                        #Append medium needed for dilutions to dicc_vol_medium 
                        if medium not in dicc_vol_medium.keys():
                            dicc_vol_medium[medium]=[v_medium]
                        else:
                            ant_list=dicc_vol_medium[medium]
                            ant_list.append(v_medium)
                            dicc_vol_medium[medium]=ant_list
                        new_list.append([conc,volume_total,v_ind,v_medium])
                        dicc_inside_inside[tuple_ind]=new_list



        return colonies_stocks,dicc_ind_together


    def organise_deck(protocol,dicc_inductor,dicc_colonies,dicc_relation,dicc_general,colonies_stocks,colony_dilution_stocks):
        """
        Organises deck positions and checks how many tipracks are needed for the protocol

        """

        nonlocal positions_tips_single
        nonlocal positions_tips_multi
        nonlocal positions_eppendorf
        nonlocal positions_plate
        nonlocal tips_ordered_multi
        nonlocal tip_count_single
        nonlocal tip_count_multi
        nonlocal column_multi

        pip_left=dicc_general['pip left']
        pip_right=dicc_general['pip right']
        V_final=dicc_general['Final volume per well (in ul)']


        ## 1) Check nº tips needed for inductor_dilutions
        ant_pip=pip=''
        list_index=[3,2]
        for index in list_index:
            for type_medium , dicc_type_medium in colony_dilution_stocks.items():
                ant_pip=pip=''
                for inductor_dilution, dicc_inductor_dilution in dicc_type_medium.items():
                    for tuple_dilutions ,list_conc in dicc_inductor_dilution.items():
                        if index==2:
                            ant_pip=pip=''                        
                        list_liq = [conc[index] for conc in list_conc]
                        for vol_liq in list_liq:
                            ant_pip=pip
                            if vol_liq!=float(0):
                                pip=get_right_pipette(vol_liq,pip_left,pip_right)
                            if pip!=ant_pip and vol_liq!=float(0): ##both for medium and dilutions we dont change tip unless new type of pipette
                                pip_sum_tips(pip)


        ## 2) Check nº tips needed for inductors_to_plate
        column_multi=dicc_general['Initial Column  Multi channel  Pipette']-1+math.ceil(tip_count_multi/8)
        
        print('\nAfter inductor dilutions in deep well')
        print('n columns multi ',column_multi,' n tips ',tip_count_multi)
        print(tip_count_single)

        ##) Check nº of tips needed for dilutions to plate 
        for type_medium,dicc_dilutions in colony_dilution_stocks.items(): 
            for inductor, dicc_inductor_name in dicc_dilutions.items():
                for tuple_inductor in dicc_inductor_name.keys():
                    ##The same tip will be used for each tuple
                    inductor_params=dicc_inductor[tuple_inductor[0]]
                    len_concentrations=len(inductor_params[3])
                    if len_concentrations==8:
                        column_multi+=1
                    if len_concentrations!=8:
                        if pip.channels==1:
                            tip_count_single+=1

      

        ## 3)Check nº tips for colony_dilutions
        tip_count_single+=1 ## just need one tip to put medium 
        for index in [1]: ##first we put medium (index 2) then we put colony (index 1) 
            for value in colonies_stocks.values():
                liq=value[index] 
                if index==1: ##Putting colonies we change tip every time
                    tip_count_single+=1

        

        ## 4) Check how many tips needed for cell_to_plate
        for cells, params_cells in dicc_colonies.items():
            list_inductors=dicc_relation[cells]
            inductor_params=dicc_inductor[list_inductors[0]]
            len_concentrations=len(inductor_params[3])  
            if len_concentrations==8:
                inductor_params=dicc_inductor[list_inductors[0]]
                len_concentrations=len(inductor_params[3])
                column_multi+=1
            if len_concentrations!=8: #only single channel is supported 
                for ind in list_inductors:
                    tip_count_single+=1
                    

        if dicc_general['Fill empty columns with water']==True: ##add an extra pipette to put water
            tip_count_single+=1


        ##Step 2: Organise deck 
        
        ## 1) Load Heater_
        hs_mod=protocol.load_module('heaterShakerModuleV1', 10)
        hs_mod.close_labware_latch()
        plate_dilutions=hs_mod.load_labware(dicc_general['Name Deep Well placed in Heater-Shaker']) ##change type of labware

        ## Possible positions for labware


        ##2)Load Plates
        print('-------------------------------------')
        print('\nOrganisation of plates:')
        for i in range(1,dicc_general['Number of plates']+1): #iterate over the number of plates
            plate,pos=load_labware(positions_plate,dicc_general['Name Source Plate'])
            print('Plate number %s will be placed in deck slot %s'%(i,pos))
            for colony, params in dicc_colonies.items(): ##append this plate to dicc_colonies and dicc_dilutions
                if params[2]==i:
                    params.pop(2)
                    params.insert(2,plate)
                    list_inductors_colony=dicc_relation[colony]
                    for inductor in list_inductors_colony:
                        params=dicc_inductor[inductor]
                        params.append(plate)
        

        ##3) Load  Tipracks multichannel pipette 
        for pip in [pip_left,pip_right]:
            if pip.channels==8:
                multi_pipette=pip
                if pip.max_volume==20:
                    tips_name='opentrons_96_tiprack_20ul'
                if pip.max_volume==300:
                    tips_name='opentrons_96_tiprack_300ul'
            if pip.channels==1:
                single_pipette=pip
                if pip.max_volume==20:
                    tips_name_single='opentrons_96_tiprack_20ul'
                if pip.max_volume==300:
                    tips_name_single='opentrons_96_tiprack_300ul'
                if pip.max_volume==1000:
                    tips_name_single='opentrons_96_tiprack_1000ul'

        n_tiracks_multi_needed=math.ceil(column_multi/12)
        
        for _ in range (n_tiracks_multi_needed): #iterate over the number of tipracks of multichannel pipette needed

                tip_rack,pos=load_labware(positions_tips_multi,tips_name)
                multi_pipette.tip_racks.append(tip_rack)

                ##Now eliminate the possibility 
                #   1) Of tips_single being in the front of multi tips --> it will crash
                #   2) Of tube_rack being in front of multi tips --> it will crash 

                for list_crash in [positions_tips_single,positions_falcon]: ##right,corrected
                    for position_single in list_crash:
                        if pos==position_single+3:
                            index=list_crash.index(position_single)
                            list_crash.pop(index)

        total_tipracks_multi=multi_pipette.tip_racks
        
        #Now we set tips_ordered for the multi pipette channels
        column_multi=dicc_general['Initial Column  Multi channel  Pipette']-1
        tip_count_multi=0
        set_multipipette_channels(multi_pipette,1,protocol)


        ##4) Load tip_racks for single_channel_pipete
        first_tip_single=dicc_general['Initial Tip Single Channel Pipette']
        ##we calculate how many tipracks are needed for the single channel pipette
        index_first_tip=list(tip_rack.wells_by_name().keys()).index(first_tip_single)
        n_tipracks_single_needed=math.ceil((index_first_tip+tip_count_single)/(len(tip_rack.columns()*len(tip_rack.rows()))))
        #print(index_first_tip+tip_count_single)
        for i in range(n_tipracks_single_needed):
            tip_rack_single,pos=load_labware(positions_tips_single,tips_name_single)
            single_pipette.tip_racks.append(tip_rack_single)
            if i==0:
                single_pipette.starting_tip=tip_rack_single.well(first_tip_single)


        ##5) Load tuberacks

        total_volume_water=0
        plate_names={}
        falcon_tubes=0

        if dicc_general['Fill empty columns with water']==True:

            n_plates=dicc_general['Number of plates']
            
            for key,values in dicc_inductor.items():
                if values[9] not in plate_names:
                    plate_names[values[9]]=[key]
                else:
                    x=plate_names[values[9]]
                    x.append(key)
                    plate_names[values[9]]=x

            for plate, inductions in plate_names.items(): ##iterate thorugh the plates to see empy columns 
                used_columns=[]
                for ind in inductions:
                    params=dicc_inductor[ind]
                    n_replicates=params[2]
                    first_column=params[4]
                    if first_column not in used_columns:
                        for i in range(n_replicates):
                                used_columns.append(first_column+i)
                used_columns.sort()
                not_used_columns=[]
                for column in range(len(plate.columns())):
                    if column not in used_columns:
                        not_used_columns.append(column)
                        total_volume_water+=8 #8 wells per column 
                plate_names[plate]=not_used_columns
            total_volume_water=math.ceil((total_volume_water*dicc_general['Final volume per well (in ul)']/100))*100
            if total_volume_water>14000:
                raise Exception('For now only one falcon of 15ml is supported')

            falcon_tubes,pos=load_labware(positions_falcon,'opentrons_15_tuberack_falcon_15ml_conical')
            print('\n-------------------------------------')
            print('Organisation of %s in %s'%(falcon_tubes,pos))
   
        return hs_mod,plate_dilutions,plate_names,total_volume_water,falcon_tubes

    def load_labware(list_pos_deck,name_labware_library):
        """
            Loads lawbware into deck and eliminates this deck position from other optionsº
            * list_pos_deck  list , list of all the possible in where to place the labware 
            * name_labware_Library : str, name of the labware in the labware_librry
        """
        nonlocal protocol
        nonlocal positions_tips_single
        nonlocal positions_eppendorf
        nonlocal positions_plate
        nonlocal positions_tips_multi
        nonlocal positions_falcon


        pos=list_pos_deck[0]
        try:
            list_pos_deck.pop(0)
        except: 
            raise Exception('\nNot enough space in deck to organise experiment. Options: \n\t1)Reduce number of dilutions\n\t2)Reduce number of colonies')        

        ## pop from list this position all different labware possible positions since this deck position is no longer available
        for list_pos in [positions_tips_single,positions_tips_multi,positions_plate,positions_eppendorf,positions_falcon]: 
            for position in list_pos:
                if position==pos:
                    index=list_pos.index(position)
                    list_pos.pop(index)

        labware=protocol.load_labware(name_labware_library,pos)
       
        return labware,pos


    def organise_eppendorf_rack(protocol,dicc,dicc_inductor,dicc_colonies,eppendorf_rack,positions_tips_multi,dicc_positions_eppendorf):
        """
        Steps:
            1) Calculate how many eppendorfs needed in for each stock
                * Inductors
                * Colonies
                * Medium 
            2) Update dicc of inputs

            3) Load the eppendorf racks   

        """
        import math 
        nonlocal new_well

            
        #Step 1: Calculate how many eppendorfs and load labware
        for type_liq,list_of_volumes in dicc.items():
            sum_volumes=sum(list_of_volumes)
            if sum_volumes>1000:
                sublist=split_list(list_of_volumes,1600)
                list_location=[]
                for list_ep in sublist:
                    total_vol=sum(list_ep)
                    try:
                        location_liq=eppendorf_rack.wells()[new_well]
                        new_well+=1
                        dicc_lab_eppen=dicc_positions_eppendorf[eppendorf_rack]
                    except:
                        eppendorf_rack,pos=load_labware(positions_eppendorf,'opentrons_24_tuberack_eppendorf_1.5ml_safelock_snapcap')
                        dicc_positions_eppendorf[eppendorf_rack]={}
                        dicc_lab_eppen=dicc_positions_eppendorf[eppendorf_rack]
                        for pos_multi in positions_tips_multi: ## to aovid crashing while getting tips 
                            if pos_multi==pos+3:
                                positions_tips_multi.pop(pos_multi)
                        for pos_tube in positions_falcon:
                            if pos_tube==pos-3: ##avoid crash while using eppendors
                                positions_falcon.pop(pos_tube)
                        print('\nOrganisation for %s: '%eppendorf_rack)
                        new_well=0

                    EppV_i=EppV(location_liq,current_volume=total_vol+150,min_volume=50)
                    list_location.append(EppV_i)
                    dicc_lab_eppen[str(location_liq)[0:2]]=[math.ceil(total_vol+150),type_liq]
            elif sum_volumes<1000: 
                list_location=''
                try:
                    list_location=eppendorf_rack.wells()[new_well]
                    new_well+=1
                    dicc_lab_eppen=dicc_positions_eppendorf[eppendorf_rack]
                except:
                    eppendorf_rack,pos=load_labware(positions_eppendorf,'opentrons_24_tuberack_eppendorf_1.5ml_safelock_snapcap')
                    dicc_positions_eppendorf[eppendorf_rack]={}
                    dicc_lab_eppen=dicc_positions_eppendorf[eppendorf_rack]
                    print('\nOrganisation for %s: '%eppendorf_rack)
                    new_well=0
                    for pos_multi in positions_tips_multi: ## to aovid crashing while getting tips 
                        if pos_multi==pos+3:
                            positions_tips_multi.pop(pos_multi)
                    for pos_tube in positions_falcon:
                        if pos_tube==pos-3: ##avoid crash while using eppendors
                            positions_falcon.pop(pos_tubeS)


                dicc_lab_eppen[str(list_location)[0:2]]=[sum(list_of_volumes)+100,type_liq]

            
            ##Step 2: Append the liquids to the diccs 
            for dicc in [dicc_inductor,dicc_colonies]:
                for keys,values in dicc.items(): 
                    if type_liq in values or type_liq==keys:
                        values.append(list_location)
                        dicc[keys]=values           
        return 


    def organise_deep_well_dilutions(protocol,dicc,plate_dilutions,dicc_inductor):
        """
        Calculates in which column of deep well will  colonies dilutions be placed on
        """
        nonlocal column_deep_well
        name_colony=''
        for type_medium,values in dicc.items():
            for type_inductor,dilutions in values.items():
                conc_now=8
                for tuple_ind,values_i in dilutions.items():
                    for inductor_dilution in tuple_ind:
                        name_colony_before=name_colony
                        name_colony=[key for key, value in dicc_relation.items() if inductor_dilution in value][0]
                        values_ii=dicc_inductor[inductor_dilution]
                        conc_prev=conc_now
                        conc_now=len(values_ii[3])
                        if conc_now==8 and conc_prev!=8:
                            column_deep_well=column_deep_well+1
                            if column_deep_well>11: #not enough space in deep well 
                                raise Exception('To much combinations of colonies + dilutionS.Options:\n\t1)Reduce number of colonies\n\t2)Reduce number of dilutions/colony')

                        ##we add to dick column of deep well for this dilution 
                        values_ii.append(column_deep_well)
                        dicc_inductor[inductor_dilution]=values_ii               
                    if len(values_ii[3])==8: ##sum 1 for normal tuples 
                        column_deep_well+=1
                        if column_deep_well>11: #not enough space in deep well 
                            raise Exception('To much combinations of colonies + dilutionS.Options:\n\t1)Reduce number of colonies\n\t2)Reduce number of dilutions/colony')

        #if everything has ended an the las column was one with out 8 columns add one for colony stocks 
        if conc_now!=8:
            column_deep_well+=1                        
            if column_deep_well>11: #not enough space in deep well 
                raise Exception('To much combinations of colonies + dilutionS.Options:\n\t1)Reduce number of colonies\n\t2)Reduce number of dilutions/colony')


        return  


    def organise_deep_well_colonies(protocol,dicc,plate_dilutions,dicc_colonies):
        """
        Calculates in which column of deep well will  colonies dilutions be placed on
        """
        nonlocal column_deep_well
        for keys,values in dicc.items():
            values_c=dicc_colonies[keys]
            values_c.append(column_deep_well)
            dicc_colonies[keys]=values_c
            column_deep_well+=1
            if column_deep_well>11: #not enough space in deep well 
                raise Exception('To much combinations of colonies + dilutionS.Options:\n\t1)Reduce number of colonies\n\t2)Reduce number of dilutions/colony')


        return 

    def set_multipipette_channels(pip,num_channels_per_pickup,protocol):
        """
        changes the number of channels the multichannel pieptte will use 
        """
        import math 
        if pip.name=='p20_multi_gen2':
            per_tip_pickup_current = .075
        if pip.name=='p300_multi_gen2':
            per_tip_pickup_current = 0.1 
        #define current
        nonlocal num_channels
        nonlocal tip_count_multi
        nonlocal tips_ordered_multi
        nonlocal column_multi
        num_channels=num_channels_per_pickup


        pick_up_current = num_channels_per_pickup*per_tip_pickup_current
        protocol._hw_manager.hardware._attached_instruments[
            pip._core.get_mount()].update_config_item(
            'pick_up_current', pick_up_current)


        #define tips ordered 
        if column_multi>12: ##if we are starting new tiprack
            pip.tip_racks.pop()[0]
            column_multi=0

        if num_channels_per_pickup==8:
            #the pipette previously used 1 channel and now swithching to 8
            column_used=math.ceil(tip_count_multi/8)
            column_multi+=column_used
            tip_count_multi=0
            tips_ordered_new=[]
            #first tip rack doesnt have all the column 
            for column_ord in pip.tip_racks[0].columns()[column_multi:]:
                tips_ordered_new.append(column_ord[0])
            #next tip racks do have all the columns 
            if len(pip.tip_racks)>1:
                for tiprack in pip.tip_racks[1:]:
                    for column in tiprack.columns():
                        tips_ordered_new.append(column[0])
            tips_ordered_multi=tips_ordered_new
        if num_channels_per_pickup==1:
            #the pipette previously used 8 channel and now swithching to 1    
            column_multi=column_multi+tip_count_multi
            tip_count_multi=0        
            tips_ordered_new=[]
            #first tip rack doesnt have all the column             
            for column_ord in pip.tip_racks[0].columns()[column_multi:]:
                column_ord.reverse()
                for tip in column_ord:
                    tips_ordered_new.append(tip)
            #next tip racks do have all the columns 
            if len(pip.tip_racks)>1:
                for tiprack in pip.tip_racks[1:]:
                    for column_ord in tiprack.columns():
                        column_ord.reverse()
                        for tip in column_ord:
                            tips_ordered_new.append(tip)
            tips_ordered_multi=tips_ordered_new
        return

    def transfer_multi_with_less_channel(pip,volume,source,dest,new_channels,protocol,tip='never'): 
        """
        transfer voume when the multichannel piette is being used with less channels 
        Options of new tip are:
            (it always will get a tip if there is no tip) 
            * 'never' --> never drop tips afterwars
            * 'always' --> drop tip afterwards always
        """
        nonlocal num_channels

        if num_channels!=new_channels:
            #print(pip)
            set_multipipette_channels(pip,new_channels,protocol)
        if pip.has_tip==False and volume!=0:
            pick_up(pip)
        if volume!=0:
            pip.aspirate(volume,source.bottom(z=8))
            pip.dispense(volume,dest) #en el bottom porque es una placa
        if tip=='always':
            pip.drop_tip()
        return   

    def distribute_multi_with_less_channel(pip,volume,source,dest,new_channels,protocol,tip='never'): 
            """
            Distrubutes volumes when the multichannel pipette is being used with less channels 
            volume --> list of volumes
            source --> just one source 
            dest -->  list of dest 
                * dest and volume must be the same len, to know which volume corresponds to which dest 

            Options of new tip are:
                (it always will get a tip if there is no tip) 
                * 'never' --> never drop tips afterwars
                * 'always' --> drop tip afterwards always
            """
            nonlocal num_channels

            if num_channels!=new_channels:
                #print(pip)
                set_multipipette_channels(pip,new_channels,protocol)
            if pip.has_tip==False and volume!=[0.0]:
                pick_up(pip)

            sublists = [[]]
            temp_dest=dest
            current_sum=0
            for vol in volume:
                if current_sum + vol >20:
                    sublists.append([])
                    current_sum=0
                sublists[-1].append(vol)
                current_sum+=vol
            
            for pick in sublists:
                pip.aspirate(sum(pick),source.bottom(z=8))
                for vol_dest in pick:
                    if vol_dest!=0:
                        pip.dispense(vol_dest,temp_dest[0])
                    temp_dest.pop(0)
            if tip=='always':
                pip.drop_tip()
            return   

    def inductor_dilutions(tuple_inductor,params_dilutions,dicc_inductor,type_liq,source_liq,pip_left,pip_right,plate_dilutions,protocol,num_channels,change_tip):
        """
        Creates the dilutions of the inductors  in the deep well 
        """
        list_match=dicc_inductor[tuple_inductor[0]] ##same params of type_liq and source_liq in each column od dilutions 
        protocol.comment('\nCreating dilutions')
        source=list_match[source_liq]
        column_deep_well=list_match[10]
        row_deep_well=list_match[5]
        list_v = [sublist[type_liq] for sublist in params_dilutions] #first medium then inductor
        protocol.comment(str(list_v))
        dicc_pips=divide_distributes(list_v,pip_left,pip_right) #empieza por la de min vol y sigue por la de mas vol
        index = [list_v.index(list_p[0]) for list_p in dicc_pips.values() if list_p != []]  #get the indexes of change from pip threshold to the other pipette 
        i=0
        
        for pip,v_medium in dicc_pips.items(): #iterate trough the volumes of each list
            if v_medium!=[]:          
                start=index[i]
                i=i+1
            if pip.channels!=8: #single
                if pip.has_tip==False and (v_medium!=[] or v_medium!=[0.0]):
                    pip.pick_up_tip()
                if isinstance(source,list): #is a list of EppenV --> medium 
                    
                    dicc_eppV=eppV_source(v_medium,source,protocol)
                    for epp,lvol in dicc_eppV.items():  #iterate through eppenV
                        if lvol!=[]: #list is not blank
                            start=start+ row_deep_well
                            pip.distribute(lvol,epp,plate_dilutions.columns()[column_deep_well][start:(start+len(lvol))],new_tip='never',disposal_volume=0)
                            start+=len(lvol)
                else: #just one medium 
                    if v_medium!=[]:
                        if len(v_medium)>1:
                            j=start + row_deep_well
                            pip.distribute(v_medium,source,plate_dilutions.columns()[column_deep_well][start:(start+len(v_medium))],new_tip='never',disposal_volume=0)
                        if len(v_medium)==1: 
                            j=start+ row_deep_well
                            pip.transfer(v_medium[0],source,plate_dilutions.columns()[column_deep_well][j],new_tip='never',disposal_volume=0)
                            
            if pip.channels==8: ##multichannel
                if isinstance(source,list): #is a list of EppenV --> medium
                    dicc_eppV=eppV_source(v_medium,source,protocol)
                    for epp,lvol in dicc_eppV.items():  #iterate through eppenV
                        if lvol!=[]: #list is not blank
                            if len(lvol)==1:
                                j=start+row_deep_well
                                transfer_multi_with_less_channel(pip,lvol[0],source,plate_dilutions.columns()[column_deep_well][j],num_channels,protocol,tip='never')
                            if len(lvol)>1: #dot know if it works 
                                j=start + row_deep_well
                                distribute_multi_with_less_channel(pip,lvol,epp,plate_dilutions.columns()[column_deep_well][j:len(lvol)],num_channels,protocol,tip='never')
            
                else: #just one --> inductor
                    if v_medium!=[]:
                        if len(v_medium)>1:
                            j=start + row_deep_well
                            distribute_multi_with_less_channel(pip,v_medium,source,plate_dilutions.columns()[column_deep_well][j:len(v_medium)],num_channels,protocol,tip='never')
                        if len(v_medium)==1:
                            j=start + row_deep_well
                            transfer_multi_with_less_channel(pip,v_medium[0],source,plate_dilutions.columns()[column_deep_well][j],num_channels,protocol,tip='never')

                        
        if change_tip==True:
            drop_tips(pip_left,pip_right)
        return

    def colonies_dilutions(name,params_colony,colonies_stocks,dicc_relation,dicc_inductor,type_liq,source_liq,V_final,pip_left,pip_right,plate_dilutions,protocol,change_tip):
        """
        creates the dilutions of the colonies in the deep well 

        """
        #location,colonies_2x,od_cultivo,od_inicial,plate,column_plate_dilutions,list_medium=params_colony
        protocol.comment('\nCreating colonies 2x for %s\n'%name)
        od_ini,od_final,plate,type_medium,loc_colony,list_medium,column_plate_dilutions=params_colony
        source=params_colony[source_liq]
        colony_use=colonies_stocks[name]
        vol=colony_use[type_liq] ##This will always have to be donde with the single channel pipette
        for pipette in [pip_right,pip_left]:
            if pipette.channels==1:
                pip_single=pipette
        if vol<pip_single.min_volume:
            raise Exception("{} has an OD higher than what this protocol can handle. Please dilute this colony and change the parameter 'Initial OD' in the 'colonies' sheet in the input xlsx file".format(name))
        list_inductors=dicc_relation[name]
        ## separar entre que sea una colonia normal y la colony no plasmid
        if pip_single.has_tip==False:
            pip_single.pick_up_tip()
        params_first_inductor=dicc_inductor[list_inductors[0]]

        rows=[]
        rep_rows=[]
        for ind in list_inductors:
            ##create list to know 
            name_inductor,stock,n_replicates,concentrations,column_plate,row,type_medium,plate,loc_ind_2x,list_medium,c_dilutions=dicc_inductor[ind]
            if row in rows:
                index=rows.index(row)
                prev=rep_rows[index]
                rep_rows[index]=prev+n_replicates
            if row not in rows:
                rows.append(row)
                rep_rows.append(n_replicates)

        for ind in list_inductors:
            ##create list to know 
            name_inductor,stock,n_replicates,concentrations,column_plate,row,type_medium,plate,loc_ind_2x,list_medium,c_dilutions=dicc_inductor[ind]
            for i in range(row,row+len(concentrations)):
                if i not in rows : #we already calculated first column
                    rows.append(i)
                    rep_rows.append(rep_rows[0])
        rows.sort()
        vol_list = [vol for _ in range(len(rows))]
       

        ### NOw distirbute the volumes into the well
        if isinstance(source,list): ##medium 
            dicc_eppV=eppV_source(vol_list,source,protocol)
            #print(dicc_eppV)
            # for loc in location_2x:
            #     protocol.comment('current volume is %s'%loc.current_volume)
            rows=0
            for loc,list_vol in dicc_eppV.items():
                if list_vol!=[]:
                    pip_single.distribute(list_vol,loc,plate_dilutions.columns()[column_plate_dilutions][rows:(rows+len(list_vol))],new_tip='never',disposal_volume=0)
                    rows+=len(list_vol)
        
        else: ## colony
            pip_single.distribute(vol,source,plate_dilutions.columns()[column_plate_dilutions][rows[0]:(rows[0]+len(rows))],new_tip='never',disposal_volume=0)
         
        if change_tip==True:
            drop_tips(pip_left,pip_right)

    def cells_to_plate(cells,params_cells,dicc_relation,pip_left,pip_right,plate_dilutions,V_final,protocol):
        """
        Distributes colonies dilutions into final plate
        """
        protocol.comment('\nPutting cells to plate of colony %s\n'%cells)
        od_cultivo,od_inicial,plate,type_medium,loc_colony,list_medium_colony,column_cells=params_cells
        list_inductors=dicc_relation[cells]

        for inductor in list_inductors:
            name_inductor,stock,n_replicates,concentrations,column_plate,row,type_medium,loc_ind_2x,list_medium,plate,column_plate_dilutions=dicc_inductor[inductor]
            if len(concentrations)==8:
                for pip in [pip_left,pip_right]:
                    if pip.channels==8:
                        pipette=pip
                        new_channels=len(concentrations)
                #doest work if there is no multichannel pipette
                nonlocal num_channels 
                if new_channels!=num_channels:
                    set_multipipette_channels(pipette,new_channels,protocol)
                if pipette.has_tip==False:
                    pick_up(pipette)
                pipette.distribute(V_final/2,plate_dilutions.columns()[column_cells],plate.columns()[column_plate:(column_plate+n_replicates)],new_tip='never',disposal_volume=0)
                pipette.drop_tip()
            
            if len(concentrations)!=8:
                for pip in [pip_left,pip_right]:
                    if pip.channels==1:
                        pipette=pip
                rows_dest = [row for row in range(row, row+len(concentrations))]
                if pipette.has_tip==False:
                    pipette.pick_up_tip()
                for r in rows_dest:
                    pipette.distribute(V_final/2,plate_dilutions.columns()[column_cells][r],plate.rows()[r][column_plate:column_plate+n_replicates],new_tip='never',disposal_volume=0)
                pipette.drop_tip()
    
        return

    def put_water_empty_columns(dicc_water,total_volume_water,falcon_tube,pip_left,pip_right):
        """
        Puts  in final plates water in empty columns. This function is only executed
        when dicc_general['Fill empty water with columns'] is True 
        

        Parameters
        ----------
        dicc_water : dict
            key is the name of the final plate. Value is a list with the number of the columns to put water on 
        total_volume_water : int
            Toal volume ofwater needed.
        falcon_tube : opentrons.protocol_api.labware.Labware
            Falcon where the water is located.
        pip_left : opentrons.protocol_api.instrument_context.InstrumentContext
        pip_right : opentrons.protocol_api.instrument_context.InstrumentContext

        
        """
        for pip in [pip_left,pip_right]:
            if pip.channels==1:
                pip_single=pip
        protocol.comment('Putting water to empty columns')

        print('Put %s ml of water into C5 of tuberack'%((total_volume_water+100)/1000))
        water=WellH(falcon_tube['C5'],current_volume=total_volume_water+100) #falcon 15
        water.compute_original_height_and_comp_coeff()

        for plate,list_columns in dicc_water.items():
            for column in list_columns:
                distribute_from_WellH_to_well(dicc_general['Final volume per well (in ul)'],water,plate.columns()[column],pip_single,protocol,new_tip='never',disposal_volume=0)
        if pip_single.has_tip==True:
            pip_single.drop_tip()
        return 
    
    def print_eppendorf_racks_organisation(rack_eppendorf,organisation):
        """
        Prints for one eppendorf rack where to place each reagent in a prettytable  
        
        Parameters
        ----------
        rack_eppendorf : opentrons.protocol_api.labware.Labware
            eppendorf rack  from which the position of the reagents will be printed
        organisation : dict
            Dictionary with well of each eppendorf rack as key and as value a list in form [type_liquid,volume_of_the_liquid]
        """
   
        
        print("Organisation of %s \n"%rack_eppendorf)
        # Create a PrettyTable for the labware representation
        table = PrettyTable()
        table.field_names = ['', '1', '2', '3', '4', '5', '6']
        table.align = 'l'  # Auto-align the content to the left
        table.max_width = 10  # Set the maximum width for column content
        table.border = True

        # Populate the PrettyTable with labware information
        for row in range(4):
            row_data = [chr(65 + row)]
            for col in range(1, 7):
                well = f'{chr(65 + row)}{col}'
                if well in organisation:
                    liquid, volume = organisation[well]
                    row_data.append(f'{volume} ({liquid} uL)')
                else:
                    row_data.append('Empty')
            table.add_row(row_data)

        # Print the PrettyTable
        print(table)

        return 


         

    ####BODY OF THE SCRIPT 
    protocol.comment('\n\n**Begin of the protocol**\n\n')


    # Step 1: Make the dictionaries necessary for the script
    dicc_inductor=excel_to_dict('data/user_storage/phenotyping_input.xlsx',1)
    dicc_colonies=excel_to_dict('data/user_storage/phenotyping_input.xlsx',2)
    dicc_relation=excel_to_dict('data/user_storage/phenotyping_input.xlsx',3)

    ## 1.1 Preprocess dicts so that they can be used in protocol. 
    preprocess_diccs(dicc_inductor,dicc_colonies,dicc_relation)
    ##1.2: Import dicc general informacion and load pipettes
    dicc_general=import_dicc_general_info(dicc_inductor,dicc_colonies,dicc_relation,protocol)


  

    ##Step 1: Calculate initial stocks
    colonies_stocks,colony_dilution_stocks=calculate_initial_stocks(dicc_inductor,dicc_colonies,dicc_relation,dicc_general['Final volume per well (in ul)'],dicc_general['pip left'],dicc_general['pip right'],dicc_vol_medium,dicc_vol_colonies,dicc_vol_inductor)
    ##Step 2: Organise Eppendorf racks 

    new_well=0
    print('\nWells In eppendorf racks: \n')

    eppendorf_rack,pos=load_labware(positions_eppendorf,'opentrons_24_tuberack_eppendorf_1.5ml_safelock_snapcap')
    dicc_positions_eppendorf[eppendorf_rack]={}

    for pos_multi in positions_tips_multi: ## to aovid crashing while getting tips 
        if pos_multi==pos+3:
            positions_tips_multi.pop(pos_multi)
    for pos_tube in positions_falcon:
        if pos_tube==pos-3: ##avoid crash while using eppendors 
            positions_falcon.pop(pos_tube)
    print('\nOrganisation for %s: '%eppendorf_rack)
 
    
    ##load type if liquids and relate them to the dilutons/colonies that use them 
    for dicc in [dicc_vol_inductor,dicc_vol_colonies,dicc_vol_medium]:
        organise_eppendorf_rack(protocol,dicc,dicc_inductor,dicc_colonies,eppendorf_rack,positions_tips_multi,dicc_positions_eppendorf)


    # ##Step 1: Organize  the rest fo the deck 

    hs_mod,plate_dilutions,dicc_water,total_volume_water,falcon_tubes=organise_deck(protocol,dicc_inductor,dicc_colonies,dicc_relation,dicc_general,colonies_stocks,colony_dilution_stocks)

    ##Organise deep well
    tip_count_multi=0
    column=0
    column_deep_well=0
    organise_deep_well_dilutions(protocol,colony_dilution_stocks,plate_dilutions,dicc_inductor)
    organise_deep_well_colonies(protocol,colonies_stocks, plate_dilutions,dicc_colonies)





    # # #[3,8]  3 index in diution_stocks, 8 index in dicc_inductor
    liq_index=[[3,8,False],[2,7,True]]
    for type_liq,source_liq,change_tip in liq_index:
        for type_medium,dicc_dilutions in colony_dilution_stocks.items(): #iterate through colonies --> medi
            for inductor, dicc_inductor_name in dicc_dilutions.items():
                for tuple_inductor , params_dilutions in dicc_inductor_name.items():
                    inductor_dilutions(tuple_inductor,params_dilutions,dicc_inductor,type_liq,source_liq,dicc_general['pip left'],dicc_general['pip right'],plate_dilutions,protocol,1,change_tip=change_tip)
            drop_tips(dicc_general['pip left'],dicc_general['pip right'])

  

  
    ## Step 4: distribute inductor dilutions to plate
    shake(hs_mod,protocol,dicc_general['Speed to mix dilutions (rpm)'],40)
    protocol.pause('Put inductors to plate')


    ### Step 3: dilutions 2x of colonies
        ##3.1 put medium 
        ##3.2 put colony
    liq_index=[[2,5,False],[1,4,True]] 
    # 2 is index in colonies_sotcks, 6 index in dicc_colonies
    for type_liq,source_liq,change_tip in liq_index:
        for name,params_colony in dicc_colonies.items():
            ## creates dilutions 2x in deep well and distributes allong a row 
            ##continua por aqui
            colonies_dilutions(name,params_colony,colonies_stocks,dicc_relation,dicc_inductor,type_liq,source_liq,dicc_general['Final volume per well (in ul)'],dicc_general['pip left'],dicc_general['pip right'],plate_dilutions,protocol,change_tip=change_tip)
        drop_tips(dicc_general['pip left'],dicc_general['pip right'])




    ## Step 5: Distribute cells into plate
    type_liq=[]
    shake(hs_mod,protocol,dicc_general['Speed to mix colonies (rpm)'],20)
    for cells, params_cells in dicc_colonies.items():
        cells_to_plate(cells,params_cells,dicc_relation,dicc_general['pip left'],dicc_general['pip right'],plate_dilutions,dicc_general['Final volume per well (in ul)'],protocol)


    ## Step 6: Add water in empy columns ( if user wants to)
    if dicc_general['Fill empty columns with water']==True:
        put_water_empty_columns(dicc_water,total_volume_water,falcon_tubes,dicc_general['pip left'],dicc_general['pip right'])


   
    for pip in [dicc_general['pip left'],dicc_general['pip right']]:
        if pip.channels==8:
            multi_pipette=pip
            if pip.max_volume==20:
                pick_up_current_multi=0.6
            if pip.max_volume==300: 
                pick_up_current_multi=0.8
        if pip.channels==1:
            single_pipette=pip
            if pip.max_volume==20:
                pick_up_current_single=0.1
            if pip.max_volume==300:
                pick_up_current_single=0.125
            if pip.max_volume==1000:
                pick_up_current_single=0.17

    protocol.home()

    protocol._hw_manager.hardware._attached_instruments[multi_pipette._core.get_mount()].update_config_item('pick_up_current', pick_up_current_multi)
    protocol._hw_manager.hardware._attached_instruments[single_pipette._core.get_mount()].update_config_item('pick_up_current', pick_up_current_single)


    print('\n--------------------\nOrganization of deck slots (this information will also be displayed by the Opentrons App):\n')
    for slot, labware in sorted(protocol.loaded_labwares.items()):
        print('Slot %s: Labware %s' % (slot, labware))

    print('-------------------------------------')
    print('\nPlease bear in mind that the volumes shown are minimum volumes needed, if you want to put more feel free.')
    for rack_eppendorf,organisation in dicc_positions_eppendorf.items():
        print_eppendorf_racks_organisation(rack_eppendorf,organisation)
        print('\n-------------------------------------')





