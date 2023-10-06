import json
import numpy
import pandas as pd
from pathlib import Path

def findAllValues(in_dict: dict, keys_to_find: set[str]):
    def joinDicts(d1, d2):
        for k, v in d2.items():
            d1[k] = v
        return d1

    result = {}
    for k, v in in_dict.items():
        if k in keys_to_find:
            result[k] = v[0] if type(v) is list else v
        elif type(v) is dict:
            result = joinDicts(result, findAllValues(v, keys_to_find))

    return result


def main():

    phoneList = json.load(open('phone_results.json'))

    keys = set([
        "name",
        "SoC:",
        "Chipset",
        "Geekbench 5 (Single-Core)",
        "Geekbench 5 (Multi-Core)",
        "AnTuTu Benchmark 9",
        "3DMark Wild Life Performance",
        "PCMark 3.0",
        # "Graphics test",
        # "Graphics score",
        # "Web score",
        # "Video editing",
        # "Photo editing",
        # "Data manipulation",
        # "Writing score",
    ])
    result = {}
    for k in keys:
        result[k] = []

    for phone in phoneList:
        minPhoneData = findAllValues(phone, keys)
        for k in keys:
            result[k].append(minPhoneData.get(k))

    filepath = Path('out.csv')
    df = pd.DataFrame(data=result)
    df.to_csv(filepath)

    print(df)

    # for k, v in result.items():
    #     #


if __name__ == "__main__":
    main()
