from pathlib import Path
from model.data import SingletonData

class CheckData:
    def __init__(self, axis_borders=[]) -> None:
        self.data = SingletonData()

        if axis_borders == []:
            self._axis_borders:list[list[float]] = self.data.dataFile.axis_borders
        else:
            self._axis_borders:list[list[float]] = axis_borders
        self._axis_step:list[float] = self.data.dataFile.axis_step
        self._axis_name:list[str] = self.data.dataFile.axis_name

        self._overall_results = True
        self._non_valid_messages:dict[str:str] = {}

        #tests
        self._test_nAxis_nSteps()
        self._testCriteriumAndCriticalValue()
        self._testBackupPath()
        self._testBackupHighResAna()
        self._test_nb_steps()

        return None

    def _test_nAxis_nSteps(self) -> None:
        '''checks if the length of the steps list is the same than the borders list'''
        if not (len(self._axis_borders) == len(self._axis_step) and len(self._axis_borders) == len(self._axis_name)-1):
            self._overall_results = False
            self._non_valid_messages["_test_nAxis_nSteps"] = f"The length of the axis_step list, axis_borders list and the axis_names list must be equal. Indeed, axis_names is {len(self._axis_name)} long, axis_step is {len(self._axis_step)} long and axis_borders is {len(self._axis_borders)} long. axis_name must be one longer than the other though, it's normal."

        return None
    
    def _testCriteriumAndCriticalValue(self) -> None:
        '''tests if critical value is one value if criterium is 'over' or 'under', two values if criterium is 'out' our 'in' (first is the lower bound, second is the upper bound)'''
        if self.data.dataFile.criterium in ["out", "in"]:
            if not len(self.data.dataFile.critical_value) == 2:
                self._overall_results = False
                self._non_valid_messages["_testCriteriumAndCriticalValue"] = f"You chose as the criterium {self.data.dataFile.criterium} so you need two critical values, one for the lower bound and the second for the upper one. But you filled {len(self.data.dataFile.critical_value)}."
            elif len(self.data.dataFile.critical_value) == 2 and self.data.dataFile.critical_value[0] == self.data.dataFile.critical_value[1]:
                self._overall_results = False
                self._non_valid_messages["_testCriteriumAndCriticalValue"] = f"You chose as the criterium {self.data.dataFile.criterium} so you need two different critical values, but you filled two time the same one : {self.data.dataFile.critical_value[0]}"
        elif self.data.dataFile.criterium in ["over", "under"]:
            if not len(self.data.dataFile.critical_value) == 1:
                self._overall_results = False
                self._non_valid_messages["_testCriteriumAndCriticalValue"] = f"You chose as the criterium {self.data.dataFile.criterium} so you need one critical value. But you filled {len(self.data.dataFile.critical_value)}."

        return None
    
    def _testBackupPath(self) -> None:
        '''tests if the path to the backup is correct'''
        if self.data.dataFile.backup != Path():
            if not self.data.dataFile.backup.is_file():
                if self.data.dataFile.backup.is_dir():
                    self._overall_results = False
                    self._non_valid_messages["_testBackupPath"] = f"The backup path you filled ({self.data.dataFile.backup}) is a directory path, not a file one."
                else:
                    self._overall_results = False
                    self._non_valid_messages["_testBackupPath"] = f"The backup path you filled ({self.data.dataFile.backup}) might not exist. Please check it."
        
        return None
    
    def _testBackupHighResAna(self) -> None:
        '''cannot ask for high res analysis with a backup file. Tests that'''
        if self.data.dataFile.backup != Path() and self.data.dataFile.high_precision_analysis:
            self._overall_results = False
            self._non_valid_messages["_testBackupHighResAna"] = "You cannot ask for a high res analysis with a backup file, sorry. If you really need it, ask the dev to code it. Or do it by yourself."
        
        return None
    
    def _test_nb_steps(self) -> None:
        axis_index_not_enough_steps = []
        for axis_index, steps in enumerate(self.data.dataFile.axis_step):
            if steps < 2:
                axis_index_not_enough_steps.append(axis_index)

        if axis_index_not_enough_steps != []:
            self._overall_results = False
            self._non_valid_messages["_test_nb_steps"] = "Number of steps needs to be over 2. It is not the case fot the following axis :\n"
            for axis_index in axis_index_not_enough_steps:
                self._non_valid_messages["_test_nb_steps"] += f"Axis index {axis_index} : {self.data.dataFile.axis_name[axis_index]}\n"

    def areDataValid(self) -> bool:
        return self._overall_results
    
    def get_error_messages(self) -> dict[str:str]:
        return self._non_valid_messages
