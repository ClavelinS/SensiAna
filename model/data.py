import tomllib
from pathlib import Path
import numpy as np
import sys
import re
from model.fav import Favorites

__DEFAULT_N_SAMPLE__ = 1024
__MAX_STEP__ = 10**6
__FIRST_LINE_MESH_BACKUP_FILE__ = 9 #from 0
__RANDOM_POINTS_TEST_HYPOTHESIS__ = 1000

class SingletonData:
    '''
    Class containing all data : inputs, outputs, parameters, ...
    '''
    def __new__(cls) :
        if not hasattr(cls, "instance"): #if class not already created (test if the class has the attribute cls.instance)
            cls.instance = super(SingletonData, cls).__new__(cls) #create the attribute

        return cls.instance
    
    def __init__(self) -> None :
        if not hasattr(self, 'initialized'): #if the singleton has not been initialized
            self.initialized = True
            self.dataFile = DataFile()
            self.max_step = __MAX_STEP__
            self.first_line_mesh_backup_file = __FIRST_LINE_MESH_BACKUP_FILE__ #first line where the data are in the backup file (mesh values)
            self.random_points_test_hypothesis = __RANDOM_POINTS_TEST_HYPOTHESIS__
            self.backup_file_name = "BackupFile"
            self.fav:dict[str:Favorites] = dict() #key corresponds to Favorites().name
            self.fav_order:list[str] = []          # Contient l’ordre d’affichage

        return None
            
class DataFile:
    """Class containing only data from the data file data.toml"""
    def __init__(self) -> None:
        with open("data.toml", 'rb') as f:
            self.file = tomllib.load(f)
            self._createVars()
        
    def _createVars(self) -> None:
        '''create variables from the data file'''
        self.title:str = self.file["title"]
        self.axis_name:list[str] = self.file["axis_name"]

        self.axis_borders:list[list[float]] = self.file["axis_borders"]
        self.axis_step:list[int] = self.file["axis_step"]

        self.max_computation_time:float = self.file["max_computation_time"]

        self.critical_value:list[float] = self.file["critical_value"]
        self.criterium:str = self.file["criterium"] #what to watch out : when the function is over the critical value or under ; can either be 'under', 'over', 'out' or 'in'

        self.high_precision_analysis:bool = True if self.file["high_precision_analysis"]==1 else False
        self.n_sample = __DEFAULT_N_SAMPLE__ if self.file["n_sample"] == 0 else self.file["n_sample"]

        self.backup = Path(self.file["backup"])

        return None
    
class BackUpParser:
    def __init__(self) -> None:
        self.data = SingletonData()
        self.map = None
        self._loadBackUp()
        return None
    
    def _loadBackUp(self) -> None:
        self.data.dataFile.high_precision_analysis = False
        with open(self.data.dataFile.backup, 'r') as f:
            line_index = 0
            upper_bounds = []
            lower_bounds = []
            n_lines = 0
            last_percent_printed = -1 #last percentage printed
            for line in f:
                parsed_line = line.split(",")
                if line_index==0:
                    # line 0 : title
                    self.data.dataFile.title = parsed_line[0]
                elif line_index==1:
                    # line 1 : axis names
                    self.data.dataFile.axis_name = parsed_line[:-1] #parsed_line[-1] = "\n"
                elif line_index==2:
                    # line 2 : axis steps
                    self.data.dataFile.axis_step = [int(step) for step in parsed_line[:-1]]
                    map_size:tuple[int] = ()
                    for axis_index in range(len(self.data.dataFile.axis_step)):
                        map_size+=(self.data.dataFile.axis_step[axis_index],) #ttl amount of steps are already under 10**6
                    #creating the matrix
                    self.map = np.zeros(shape=map_size)
                    n_lines = np.prod(self.map.shape)
                elif line_index==3:
                    # line 3 : axis upper bound
                    upper_bounds = [float(upper_bound) for upper_bound in parsed_line[:-1]]
                elif line_index==4:
                    # line 4 : axis lower bound
                    lower_bounds = [float(lower_bound) for lower_bound in parsed_line[:-1]]
                    self.data.dataFile.axis_borders = []
                    for axis_index, upper_bound in enumerate(upper_bounds):
                        self.data.dataFile.axis_borders.append([lower_bounds[axis_index],upper_bound])
                elif line_index==5:
                    # line 5 : critical value
                    self.data.dataFile.critical_value = [float(critical_value) for critical_value in parsed_line[:-1]]
                elif line_index==6:
                    # line 6 : criterium
                    self.data.dataFile.criterium = parsed_line[0]
                elif line_index==7:
                    # line 7 : n sample
                    self.data.dataFile.n_sample = int(parsed_line[0])
                elif line_index==8:
                    # line 8 : fav
                    list_fav = parsed_line[:-1]
                    for fav_str in list_fav:
                        fav = Favorites.fromStr(fav_str)
                        self.data.fav[fav.name]=fav
                        self.data.fav_order.append(fav.name)
                else:
                    #matrix values line
                    indices = [int(index) for index in parsed_line[:-2]]
                    value = float(parsed_line[-2])
                    self.map[tuple(indices)]=value
                    if n_lines != 0:
                        percentage = int((line_index-self.data.first_line_mesh_backup_file)/n_lines*100)
                        if percentage > last_percent_printed:
                            last_percent_printed = percentage
                            self.print_progress_bar(percentage+1)

                line_index+=1
        
        return None
    
    def writeDataBackUpToml(self) -> None:
        '''write the data.toml for the backup data'''
        file = dict() #pas utile lol
        file["title"] = self.data.dataFile.title
        file["axis_name"] = self.data.dataFile.axis_name

        file["axis_borders"] = self.data.dataFile.axis_borders
        file["axis_step"] = self.data.dataFile.axis_step

        file["critical_value"] = self.data.dataFile.critical_value
        file["criterium"]  = self.data.dataFile.criterium#what to watch out : when the function is over the critical value or under ; can either be 'under', 'over', 'out' or 'in'

        file["high_precision_analysis"] = 1 if self.data.dataFile.high_precision_analysis else 0
        file["n_sample"] = self.data.dataFile.n_sample

        file["backup"] = self.data.dataFile.backup

        lines = ["#graph part"]
        for key in file:
            #commentaries
            if key == "title":
                lines.append("#graph part\n")
            elif key == "critical_value":
                lines.append("\n#critical value part\n")
            elif key == "high_precision_analysis":
                lines.append("\n#sensitivity analysis part\n")
            elif key == "backup":
                lines.append("\n#backup part\n")

            #data
            if isinstance(file[key], str) :
                lines.append(key + ' = "' + file[key] + '"\n')
            elif isinstance(file[key], Path):
                lines.append(key + ' = "' + re.sub(r"\\", r"\\\\", file[key].__str__()) + '"\n')
            else:
                lines.append(f"{key} = {file[key]}\n")

        with open("backup_data.toml", 'w') as f:
            f.writelines(lines)

        return None
    
    def print_progress_bar(self, percentage, width=100):
        """
        Barre de progression avec :
        - barre remplie en vert,
        - tête en bleu clair,
        - tirets restants en rose,
        - pourcentage en bleu clair.
        """
        # Bornage entre 0 et 100
        percentage = max(0, min(100, percentage))

        filled = int((percentage/100) * width)
        empty = width - filled

        GREEN = "\033[92m"
        PINK = "\033[95m"
        LIGHT_BLUE = "\033[94m"
        RESET = "\033[0m"

        bar = ""
        if filled > 0:
            bar += GREEN + "/" * (filled - 1)
            bar += LIGHT_BLUE + ">"
        else:
            # Si rien rempli, pas de barre verte ni tête, direct rose
            pass
        bar += PINK + "-" * empty
        bar += RESET

        percent_str = f"{percentage}%"
        percent_str_colored = "(" + LIGHT_BLUE + percent_str + RESET + ")"

        sys.stdout.write(f"\r[{bar}] {percent_str_colored}")
        sys.stdout.flush()
            