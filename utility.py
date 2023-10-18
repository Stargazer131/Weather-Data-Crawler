wind_directions = {
    "N": 360,
    "NNE": 22.5,
    "NE": 45,
    "ENE": 67.5,
    "E": 90,
    "ESE": 112.5,
    "SE": 135,
    "SSE": 157.5,
    "S": 180,
    "SSW": 202.5,
    "SW": 225,
    "WSW": 247.5,
    "W": 270,
    "WNW": 292.5,
    "NW": 315,
    "NNW": 337.5,
}

reverse_wind_directions = {
    360: "N",
    22.5: "NNE",
    45: "NE",
    67.5: "ENE",
    90: "E",
    112.5: "ESE",
    135: "SE",
    157.5: "SSE",
    180: "S",
    202.5: "SSW",
    225: "SW",
    247.5: "WSW",
    270: "W",
    292.5: "WNW",
    315: "NW",
    337.5: "NNW",
}


def wind_direction_to_degree(wind_direction: str):
    try:
        degree = wind_directions.get(wind_direction.upper())
        if degree is not None:
            return degree
        else:
            if wind_direction == 'CALM':
                return 0.0
            else:
                return -1.0
    except:
        return float('nan')


def degree_to_wind_direction(degree):
    try:
        if degree < wind_directions['NNE'] / 2:
            return 'N'

        # Find the closest matching wind direction for the given degrees
        closest_match = min(reverse_wind_directions, key=lambda x: abs(x - degrees))
        return reverse_wind_directions[closest_match]
    except:
        return None

if __name__ == '__main__':
    pass
