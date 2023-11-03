def inverse_transform_condition(code: int):
    weather_dict = {
        0: "Cloudy",
        1: "Fair",
        2: "Fog",
        3: "Rain",
        4: "Thunderstorm"
    }
    return weather_dict[code]
