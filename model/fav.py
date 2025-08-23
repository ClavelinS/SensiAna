from dataclasses import dataclass
from typing import Self

@dataclass
class Favorites:

    @classmethod
    def fromStr(cls, fav_str:str) -> Self:
        '''str format : name;axis_x;axis_y;color;axis1:float1/axis2:float2
                                                |       >>sliders<<       |
                                                so separation by ; then the last by / and for each of them last by : (no , because already used to make the separate favs themselves)'''
        name, axis_x, axis_y, color, sliders_str = fav_str.split(";")[:-1]

        list_sliders:list[str] = sliders_str.split("/")[:-1]
        sliders = dict()
        for slider in list_sliders:
            axis_name, axis_value = slider.split(":")
            sliders[axis_name] = float(axis_value)

        return cls(name=name, axis_x=axis_x, axis_y=axis_y, color=color, sliders=sliders)

    name:str
    axis_x:str
    axis_y:str
    sliders:dict[str,float]
    color: str = "#f0f0f0"  # default color

    def favToStr(self) -> str:
        '''str format : name;axis_x;axis_y;color;axis1:float1/axis2:float2
                                                |       >>sliders<<       |
                                                so separation by ; then the last by / and for each of them last by : (no , because already used to make the separate favs themselves)'''
        slider_str = ""
        for axis_name in self.sliders:
            slider_str += f"{axis_name}:{self.sliders[axis_name]}/"
        
        return f"{self.name};{self.axis_x};{self.axis_y};{self.color};{slider_str};"
