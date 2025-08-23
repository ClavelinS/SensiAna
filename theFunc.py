import numpy as np

def theFunction(args:np.ndarray[float] | list[float] | tuple[float]) -> float:
    '''
    this is the function to use, please match args type and results type
    to be general, this function takes in an array or list or whatever iterable, whatever the length is ; put your arguments in here
    '''
    return np.sin(args[0]+args[1])*args[2]+0.0001*args[3]
    # term_x = np.where(args[0] < 0.0, 10 * np.sin(3 * args[0]), 0)
    # term_y = np.where((args[1] > 2) & (args[1] < 4), 8 * np.cos(2 * args[1]), 0)
    # term_z = 1.5 * np.random.normal(size=args[0].shape)  # bruit
    # term_t = np.where(args[3] > 1.0, 6 * (args[3] - 1), 0)
    # return term_x + term_y + term_z + term_t

    # x = args[0]
    # y = args[1]
    # z = args[2]
    # t = args[3]

    # term_x = 10 * np.tanh(-3 * x)                    # variation douce et saturée
    # term_y = 6 * np.exp(-((y - 3.0) ** 2) / 0.25)    # pic centré sur y=3
    # term_z = 0.1 * np.random.normal(size=x.shape)   # bruit faible
    # term_t = 8 * (t / 2.0) ** 2                      # croissance quadratique

    # return term_x + term_y + term_z + term_t

    # val = (
    #     np.tanh(5 * (x - 0.5)) * np.tanh(5 * (y - 2.5)) +
    #     0.5 * np.exp(-((z - 0.25) ** 2) * 10) +
    #     0.3 * (t - 1)
    # )

    # val = (
    #     3 * np.tanh(1.5 * x)
    #     + 4 * np.exp(-((y - 2.5) ** 2))
    #     + 2 * (t - 1) * (t > 1)
    #     + 0.5 * np.random.normal()
    # )

    # return val
