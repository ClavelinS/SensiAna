import csv
import numpy as np
import multiprocessing as mp
from pathlib import Path

from model.data import SingletonData, BackUpParser
from model.checkData import CheckData
from theFunc import theFunction
import pandas as pd
import gc
from multiprocessing import Process, Queue
from model.progBar import ProgressionBar

class MeshManager:
    def __init__(self,axis_borders:list[list[float]]=[]):
        self.theFunction = theFunction
        self.data = SingletonData()

        self.theCriticalFunc = None
        if self.data.dataFile.criterium == "under":
            self.theCriticalFunc = self.testCriticalUnder
        elif self.data.dataFile.criterium == "over":
            self.theCriticalFunc = self.testCriticalOver
        elif self.data.dataFile.criterium == "out" :
            self.theCriticalFunc = self.testCriticalOut
        elif self.data.dataFile.criterium == "in" :
            self.theCriticalFunc = self.testCriticalIn

        self.backUpParser = None
        if self.data.dataFile.backup != Path():
            self.backUpParser = BackUpParser()
            self.backUpParser.writeDataBackUpToml()
        
        check_data = CheckData()
        if check_data.areDataValid():
            if axis_borders == []:
                self._axis_borders:list[list[float]] = self.data.dataFile.axis_borders
            else:
                self._axis_borders:list[list[float]] = axis_borders
            self.n_axis = len(self._axis_borders)
            self._axis_step:list[float] = [min(step, int(pow(self.data.max_step,1/self.n_axis))) for step in self.data.dataFile.axis_step] #mettre un msg si nb de steps modifié ?
            if self._axis_step != self.data.dataFile.axis_step:
                print("Max total steps clipped to 10**6. We uniformly dispatched the steps between the axis.")
                self.data.dataFile.axis_step=self._axis_step
            self._axis_name:list[str] = self.data.dataFile.axis_name

            self.critical_domain = [] #the domain (index coords) where function values are over/under the critical value ; it's a list of indices
            self.aborted_domain = [] #index coords of each node where the value of the function couldn't be computed due to some error

            self._createMesh()
            self._mapFunc()
            self._isValide = True
        else:
            if axis_borders == []: #data file's lists
                print("Something went wrong while reading data in file data.toml.")
            else:
                print("Something went wrong while meshing for further computing. Keep your data as now and contact support.")
            print("Here is a summary :")
            error_messages:dict[str:str] = check_data.get_error_messages()
            for key in error_messages:
                print(error_messages[key])
            self._isValide = False
            raise Exception("No point in continuing, aborting everything.")
        
        return None
       
    def _createMesh(self) -> None:
        '''create the mesh'''
        self.axis = []
        for axis_index in range(self.n_axis):
            self.axis.append(np.linspace(self._axis_borders[axis_index][0], self._axis_borders[axis_index][1], self._axis_step[axis_index]))

        return None
    
    def _mapFunc(self) -> None:
        '''
        maps the function on the mesh
        '''
        #creating map/matrix size
        map_size:tuple[int] = ()
        for axis_index in range(self.n_axis):
            map_size+=(self._axis_step[axis_index],)
        #creating the matrix
        self.map = np.zeros(shape=map_size)
        self.data.dataFile.n_sample = min(self.data.dataFile.n_sample, np.prod(self.map.shape))

        last_node_value = 0
        if self.backUpParser:
            starting_msg = "Starting loading values to plot the graph ..."
        else:
            starting_msg = "Starting computing values to plot the graph ..."
        progressionBar = ProgressionBar(np.prod(self.map.shape), starting_msg=starting_msg, ending_msg="Values done !")

        for indices, _ in np.ndenumerate(self.map): #indices : tuple like
            axis_values = self.fromIndicesToCoordinates(indices)
            try:
                if self.backUpParser:
                    nodeValue = self.backUpParser.map[indices]
                elif self.data.dataFile.max_computation_time <= 0:
                    nodeValue = self.theFunction(axis_values)
                else : #timeout set by the user
                    queue = Queue()
                    p = Process(target=theFunctionInQueue, args=(axis_values, queue)) #takes less than 10s
                    p.start()
                    p.join(timeout=self.data.dataFile.max_computation_time)

                    if p.is_alive():
                        p.kill()
                        p.join()
                        raise TimeoutError(f"Le calcul du noeud a dépassé le temps imparti ({self.data.dataFile.max_computation_time}s).")
                    
                    #if it went great
                    if not queue.empty():
                        nodeValue = queue.get()
                    else:
                        nodeValue = last_node_value
                        raise ValueError

                #all went good
                if self.theCriticalFunc(nodeValue):
                    self.critical_domain.append(indices)
                    last_node_value = nodeValue
                
            except (Exception, TimeoutError) as e:
                print(f"Le noeud à {[float(axis_value) for axis_value in axis_values]} n'a pas pu être calculé. Raison : {e}")
                self.aborted_domain.append(indices)
                nodeValue = last_node_value

            finally:
                self.map[indices] = nodeValue
                progressionBar.next()

            if self.backUpParser:
                self.backUpParser=None
                gc.collect() #freeing memory

        return None
    
    def isValide(self):
        return self._isValide
    
    def testCriticalUnder(self, value:float) -> bool:
        '''tests if under the critical value'''
        return value < self.data.dataFile.critical_value[0]
    
    def testCriticalOver(self, value:float) -> bool:
        '''tests if over the critical value'''
        return value > self.data.dataFile.critical_value[0]
    
    def testCriticalOut(self, value:float) -> bool:
        '''tests if out the critical value interval'''
        return not self.testCriticalIn(value) #the value is out of the [self.data.dataFile.critical_value[0], self.data.dataFile.critical_value[1]] interval
    
    def testCriticalIn(self, value:float) -> bool:
        '''tests if in the critical value interval'''
        return self.data.dataFile.critical_value[0] < value < self.data.dataFile.critical_value[1] #the value is in the [self.data.dataFile.critical_value[0], self.data.dataFile.critical_value[1]] interval

    def fromIndicesToCoordinates(self, indices:np.ndarray[int] | list[int] | tuple[int]) -> np.ndarray[float] | list[float] | tuple[float]:
        '''
        args like (5,3,9,1) -> indices of the node/step for each axis ; axis 1 : node 5, axis 2 : node 3, ...
        returns like (0.3, 0.001, 2.3, -0.9) -> coordinates associated to each node in the mesh
        '''
        axis_values = []
        for axis_index in range(self.n_axis):
            index = indices[axis_index] #the step on the axis_index-th axis
            axis_values.append(self.axis[axis_index][index])

        return axis_values
    
    def fromIndexToCoordinates(self, index:int, axis_index:int) -> np.ndarray[float] | list[float] | float:
        '''
        args like index=3, axis_index=1 -> indices of the node/step for each axis ; axis 1 : node 3
        returns like 2.3 -> coordinates associated to the node on this axis
        '''
        return self.axis[axis_index][index]
    
    def getClosestIndexFromValue(self,vec:np.ndarray[float], value:float) -> tuple[int, float]:
        '''
        from a vector vec gets the index of the closest value to value (arg)
        '''
        index = int(np.argmin(np.abs(vec-value))) #int car np.int sinon
        return index, vec[index]
    
    def getIndexRootNode(self, coordinates:tuple[float]) -> tuple[int]:
        '''e.g if the map is 2D, then if coordinates is in a cell (i,j)--(i+1,j)--(i+1,j+1)--(i,j+1) return (i,j)'''
        return tuple([int(val*self._axis_step[axis_index]/(self._axis_borders[axis_index][1]-self._axis_borders[axis_index][0])) for axis_index, val in enumerate(coordinates)])
    
    def exportCriticalDomain(self):
        with open("CriticalDomain.csv", mode='w', newline='') as csvfile:
            writer = csv.writer(csvfile)

            # Écriture des en-têtes (paramètre1, ..., paramètreN, valeur)
            headers = self.data.dataFile.axis_name
            writer.writerow(headers)

            # Écriture des lignes
            for coords in self.critical_domain:
                coords_value = [self.fromIndexToCoordinates(coord, axis_index) for axis_index, coord in enumerate(coords)]
                writer.writerow(coords_value + [self.map[coords]])

    def _export_BackUpMetaData(self) -> list[str]:
        lines = [] #liste des lignes

        # line 0 : title
        lines.append(self.data.dataFile.title + ",\n")
        
        # line 1 : axis names
        lines.append(",".join(self.data.dataFile.axis_name[:self.n_axis+1]) + ",\n")

        # line 2 : axis steps
        lines.append(",".join(str(s) for s in self._axis_step[:self.n_axis]) + ",\n")

        # line 3 : axis upper bound
        lines.append(",".join(str(b[1]) for b in self.data.dataFile.axis_borders[:self.n_axis]) + ",\n")

        # line 4 : axis lower bound
        lines.append(",".join(str(b[0]) for b in self.data.dataFile.axis_borders[:self.n_axis]) + ",\n")

        # line 5 : critical value
        lines.append(",".join(str(v) for v in self.data.dataFile.critical_value) + ",\n")

        # line 6 : criterium
        lines.append(str(self.data.dataFile.criterium) + ",\n")

        # line 7 : n sample
        lines.append(str(self.data.dataFile.n_sample) + ",\n")

        #line 8 : favorites
        fav_line = ""
        for fav in self.data.fav_order:
            fav_line += self.data.fav[fav].favToStr() + ","
        lines.append(fav_line + "\n")

        return lines

    def exportBackUp(self, progress_callback=None) -> None: #for 900,000 elt -> 53.7 seconds
        '''exports the backup file to be used to display without computing again'''
        lines = self._export_BackUpMetaData()

        # mesh values
        if hasattr(self, "map"):
            for idx, value in np.ndenumerate(self.map):
                index_str = ",".join(str(i) for i in idx)
                lines.append(f"{index_str},{value},\n")
                if progress_callback:
                    progress_callback(len(lines) - self.data.first_line_mesh_backup_file)  # -9 pour ignorer les lignes d'en-tête

        # écriture dans le fichier
        backup_file_name = "BackupFile"
        while Path(backup_file_name+".txt").is_file():
            backup_file_name += "_1" #funny haha
            print(backup_file_name+".txt" + "already exists.")
        backup_file_path = Path(backup_file_name+".txt")
        with open(backup_file_path, 'w') as f:
            f.writelines(lines)

        return None    

    def serialize_block(self, args):
        block, offset = args
        result = []
        for indices, value in np.ndenumerate(block):
            global_indices = (indices[0] + offset,) + indices[1:]
            coord_str = ",".join(str(i) for i in global_indices)
            result.append(f"{coord_str},{value},\n")
        return result
    
    def exportBackUp_parallel(self):
        lines = self._export_BackUpMetaData()

        if hasattr(self, "map"):
            cpu_count = mp.cpu_count()
            chunks = np.array_split(self.map, cpu_count)

            # Calcule les offsets pour chaque bloc
            chunk_sizes = [chunk.shape[0] for chunk in chunks]
            offsets = np.cumsum([0] + chunk_sizes[:-1])

            # Prépare les entrées (chunk, offset)
            inputs = list(zip(chunks, offsets))

            with mp.Pool(processes=cpu_count) as pool:
                all_results = pool.map(self.serialize_block, inputs)

            for block_lines in all_results:
                lines.extend(block_lines)

        backup_file_name = self.data.backup_file_name
        while Path(backup_file_name+".txt").is_file():
            print(backup_file_name+".txt" + " already exists.")
            backup_file_name += "_bis" #funny haha
        backup_file_path = Path(backup_file_name+".txt")
        with open(backup_file_path, 'w') as f:
            f.writelines(lines)

    def toDataframe(self) -> pd.DataFrame:
        ''' Convert the N-dimensional matrix into a "long" pandas DataFrame using fully vectorized operations.

        Each row corresponds to a point in the matrix:
          * Columns represent the parameters, named according to self._axis_name.
          * An additional column 'f' contains the function value at that point.
        Method suitable for very large matrices.
        
        Make sure to release the DataFrame when not needed.'''
        # Number of dimensions and shape of each axis
        shape = self.map.shape
        ndim = len(shape)

        # Generate a grid of indices for each axis
        grids = np.indices(shape)

        # Flatten the grids to get 1D arrays of coordinates
        data_dict = {self._axis_name[i]: self.axis[i][grids[i].ravel()] for i in range(ndim)}
        data_dict['f'] = self.map.ravel()

        return pd.DataFrame(data_dict)

def theFunctionInQueue(coords, queue) -> None:
    res = theFunction(coords)
    queue.put(res)
    return None
