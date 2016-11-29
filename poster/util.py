import pylast

def get_period_from_string(string):
    if (string == "1 Week"):
        return pylast.PERIOD_7DAYS
    elif (string == "30 Days"):
        return pylast.PERIOD_1MONTH
    elif (string == "90 Days"):
        return pylast.PERIOD_3MONTHS
    elif (string == "180 Days"):
        return pylast.PERIOD_6MONTHS
    elif (string == "1 Year"):
        return pylast.PERIOD_12MONTHS
    elif (string == "All time"):
        return pylast.PERIOD_OVERALL
    else:
        return pylast.PERIOD_OVERALL
