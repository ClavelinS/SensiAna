import sys

GREEN = "\033[92m"
PINK = "\033[95m"
LIGHT_BLUE = "\033[94m"
RESET = "\033[0m"

def rgb(r, g, b):
    return f"\033[38;2;{r};{g};{b}m"

class ProgressionBar:
    def __init__(self, max_iteration:int, print_step:float=1, width:int=100, starting_msg:str="", ending_msg:str="", style:str="Green'n'Pink") -> None:
        '''print_step : print on bar only if difference between the actual percentage and the last one exceed print_step so the progression bar prints a step each print_step %
        width : width of the bar
        style : the progressbar'style, e.g. "Green'n'Pink", "Turbo", "InProgress", "Blocks"
        '''
        self._max_iteration:int = max_iteration
        self._print_step:float = print_step
        self._width:int = width
        self._last_percentage:int = 0
        self._current_iteration:int = 0
        self._ending_msg:str = ending_msg

        # dictionnaire des styles
        self._style_to_func = {
            "Turbo": self._print_progress_turbo,
            "InProgress": self._print_progress_inProgress,
            "Blocks":self._print_progress_blocks,
        }
        self._print_progress_bar = self._style_to_func.get(style, self._print_progress_greenPink) # greenPink by defaut

        if print_step != "":
            print("\n"+starting_msg)

    def next(self) -> None:
        '''prints the next step of the progression bar'''
        self._current_iteration += 1
        percentage:float = self._current_iteration/self._max_iteration*100
        percentage = max(0, min(100, percentage))
        if percentage-self._last_percentage > self._print_step or (self._current_iteration>= self._max_iteration and self._last_percentage < 100):
            self._print_progress_bar(percentage)
            self._last_percentage = percentage
            if self._current_iteration == self._max_iteration:
                print("\n"+self._ending_msg)
        return None

    def _print_progress_greenPink(self, percentage:float) -> None:
        """
        Barre de progression avec :
        - barre remplie en vert,
        - tête en bleu clair,
        - tirets restants en rose,
        - pourcentage en bleu clair.
        """
        filled = int((percentage/100) * self._width)
        empty = self._width - filled

        bar = ""
        if filled > 0:
            bar += GREEN + "/" * (filled - 1)
            bar += LIGHT_BLUE + ">"
        bar += PINK + "-" * empty
        bar += RESET

        percent_str = f"{percentage:.1f}%"
        percent_str_colored = "(" + LIGHT_BLUE + percent_str + RESET + ")"

        sys.stdout.write(f"\r[{bar}] {percent_str_colored}")
        sys.stdout.flush()

    def _color_gradient(self, fraction: float):
        """
        Retourne une couleur (en ANSI 24-bit) selon fraction [0,1]
        Dégradé: bleu -> vert -> jaune -> orange -> rouge
        """
        stops = [
            (0.0, (0, 0, 255)),     # bleu
            (0.25, (0, 255, 0)),    # vert
            (0.5, (255, 255, 0)),   # jaune
            (0.75, (255, 165, 0)),  # orange
            (1.0, (255, 0, 0))      # rouge
        ]
        for i in range(len(stops)-1):
            f1, c1 = stops[i]
            f2, c2 = stops[i+1]
            if f1 <= fraction <= f2:
                t = (fraction - f1) / (f2 - f1)
                r = int(c1[0] + (c2[0]-c1[0])*t)
                g = int(c1[1] + (c2[1]-c1[1])*t)
                b = int(c1[2] + (c2[2]-c1[2])*t)
                return rgb(r,g,b)
        return rgb(255,0,0)

    def _print_progress_turbo(self, percentage: float):
        """
        Barre turbo: [====>----] avec dégradé de couleur sur les '='
        """
        filled = int((percentage/100) * self._width)
        empty = self._width - filled

        bar = "["
        for i in range(filled):
            frac = i / max(1, self._width-1)
            bar += self._color_gradient(frac) + "="
        if filled > 0:
            bar = bar[:-1] + self._color_gradient(frac) + ">"  # remplace le dernier '=' par la tête
        bar += RESET
        bar += "-" * empty
        bar += "]"

        percent_str = f"{percentage:.1f}%"
        percent_str_colored = "(" + LIGHT_BLUE + percent_str + RESET + ")"
        sys.stdout.write(f"\r{bar} {percent_str_colored}")
        sys.stdout.flush()

    def _print_progress_inProgress(self, percentage: float):
        text = "IN PROGRESS"
        n = int((percentage / 100) * len(text))  # nb de lettres à afficher
        visible = text[:n]
        hidden = " " * (len(text) - n)  # espaces pour aligner
        
        color = self._color_gradient(percentage/100)
        sys.stdout.write(f"\r{color}{visible}{RESET}{hidden}")
        sys.stdout.flush()

        if percentage >= 100:
            sys.stdout.flush()

    def _print_progress_blocks(self, percentage: float):
        filled = int((percentage/100) * self._width)
        empty = self._width - filled

        gradient = self._color_gradient(percentage/100)
        bar = gradient + "|" + "█" * (filled-1 if filled < 100 else 100) + "▒" * (1 if filled < 100 else 0) + PINK + "░" * empty + gradient + "|" + RESET
        percent_str = f"{percentage:.1f}%"
        percent_str_colored = "(" + LIGHT_BLUE + percent_str + RESET + ")"
        sys.stdout.write(f"\r{bar} {percent_str_colored}")
        sys.stdout.flush()
