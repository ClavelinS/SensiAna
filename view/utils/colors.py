def get_contrasting_text_color(bg_hex: str) -> str:
    """Retourne 'black' ou 'white' en fonction du contraste avec une couleur hex donnée."""
    hex_color = bg_hex.lstrip("#")
    r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    # Calcul du YIQ, simple proxy de luminosité perçue
    yiq = (r*299 + g*587 + b*114) / 1000
    return "black" if yiq >= 128 else "white"

def getColorScale(crit_vals:list[float], criterium:float, min_val:float, max_val:float) -> list[list[float|str]]:
    '''return the colorscale of the function values so that
      * the more blue the further from any critical value but not critical
      * the more green the closer to a critical value but not critical
      * the more orange the closer to a critical value and critical
      * the more red the further from any critical value and critical
      * gray for outbounds values (bounds are the one chosen by the user)'''
    color_outbounds = "lightgray"
    color_farFromCrit_notCrit = "blue"
    color_closeToCrit_notCrit = "green"
    color_closeToCrit_crit = "orange"
    color_farFromCrit_crit = "red"

    eps = min(1e-6,(max_val-min_val)*1e-6) #for little offsets ; why not keeping only (max_val-min_val)*1e-6 ? e-6 enough ?
    
    relativ_crit_vals = [max(3*eps, min((crit_val-min_val)/(max_val-min_val), 1-2*eps)) for crit_val in crit_vals] #min and max to be sure it's in [3*eps, 1-2*eps] so the colorscale is easily computable

    colorscale = []

    if criterium == "over":
        colorscale = [
            [0.0, color_outbounds],
            [eps, color_farFromCrit_notCrit],
            [relativ_crit_vals[0]-eps, color_closeToCrit_notCrit],
            [relativ_crit_vals[0], color_closeToCrit_crit],
            [1.0, color_farFromCrit_crit]
            ]
    elif criterium == "under":
        colorscale = [
            [0.0, color_outbounds],
            [eps, color_farFromCrit_crit],
            [relativ_crit_vals[0]-eps, color_closeToCrit_crit],
            [relativ_crit_vals[0], color_closeToCrit_notCrit],
            [1.0, color_farFromCrit_notCrit]
            ]
    elif criterium == "in":
        colorscale = [
            [0.0, color_outbounds],
            [eps, color_farFromCrit_notCrit],
            [min(relativ_crit_vals)-eps, color_closeToCrit_notCrit],
            [min(relativ_crit_vals), color_closeToCrit_crit],
            [(relativ_crit_vals[0]+relativ_crit_vals[1])/2, color_farFromCrit_crit],
            [max(relativ_crit_vals), color_closeToCrit_crit],
            [max(relativ_crit_vals)+eps, color_closeToCrit_notCrit],
            [1.0, color_farFromCrit_notCrit]
            ]
    elif criterium == "out":
        colorscale = [
            [0.0, color_outbounds],
            [eps, color_farFromCrit_crit],
            [min(relativ_crit_vals)-eps, color_closeToCrit_crit],
            [min(relativ_crit_vals), color_closeToCrit_notCrit],
            [(relativ_crit_vals[0]+relativ_crit_vals[1])/2, color_farFromCrit_notCrit],
            [max(relativ_crit_vals), color_closeToCrit_notCrit],
            [max(relativ_crit_vals)+eps, color_closeToCrit_crit],
            [1.0, color_farFromCrit_crit]
            ]
        
    return colorscale
