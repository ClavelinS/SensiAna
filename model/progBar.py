import sys

GREEN = "\033[92m"
PINK = "\033[95m"
LIGHT_BLUE = "\033[94m"
RESET = "\033[0m"

class ProgressionBar:
    def __init__(self, max_iteration:int, print_step:float=1, width:int=100, starting_msg:str="", ending_msg:str=""):
        '''print_step : print on bar only if difference between the actual percentage and the last one exceed print_step so the progression bar prints a step each print_step %
        width : width of the bar'''
        self._max_iteration:int = max_iteration
        self._print_step:float = print_step
        self._width:int = width
        self._last_percentage:int = 0
        self._current_iteration:int = 0
        self._ending_msg:str = ending_msg
        if print_step != "":
            print("\n"+starting_msg)

    def next(self):
        '''prints the next step of the progression bar'''
        self._current_iteration += 1
        percentage:float = self._current_iteration/self._max_iteration*100
        percentage = max(0, min(100, percentage))
        if percentage-self._last_percentage > self._print_step or (self._current_iteration>= self._max_iteration and self._last_percentage < 100):
            self._print_progress_bar(percentage)
            self._last_percentage = percentage
            if self._current_iteration == self._max_iteration:
                print("\n"+self._ending_msg)

    def _print_progress_bar(self, percentage:float):
        """
        Barre de progression avec :
        - barre remplie en vert,
        - tête en bleu clair,
        - tirets restants en rose,
        - pourcentage en bleu clair.
        """
        # Bornage entre 0 et 100
        filled = int((percentage/100) * self._width)
        empty = self._width - filled

        bar = ""
        if filled > 0:
            bar += GREEN + "/" * (filled - 1)
            bar += LIGHT_BLUE + ">"
        else:
            # Si rien rempli, pas de barre verte ni tête, direct rose
            pass
        bar += PINK + "-" * empty
        bar += RESET

        percent_str = f"{percentage:.1f}%"
        percent_str_colored = "(" + LIGHT_BLUE + percent_str + RESET + ")"

        sys.stdout.write(f"\r[{bar}] {percent_str_colored}")
        sys.stdout.flush()