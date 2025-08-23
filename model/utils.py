def addOneToAIndex(vec:tuple[int], index_to_change:int) -> tuple[int]:
    '''adds one to the index of a list (coordinate quite often)'''
    return tuple([index+1 if axis_index==index_to_change else index for axis_index, index in enumerate(vec)])

def subtractOneToAIndex(vec:tuple[int], index_to_change:int) -> tuple[int]:
    '''adds one to the index of a list (coordinate quite often)'''
    return tuple([index-1 if axis_index==index_to_change else index for axis_index, index in enumerate(vec)])