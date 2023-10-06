import json
import pandas as pd
from pathlib import Path
import re

benchmarkNames = set([
    "3DMark for Android Wild Life",
    "3DMark for Android Wild Life Unlimited",
    "3DMark for Android Wild Life Extreme",
    "Wild Life Extreme Unlimited",
    "3DMark for Android Sling Shot Extreme (OpenGL ES 3.1)",
    "3DMark for Android Sling Shot Extreme (Vulkan)",
    "3DMark for Android Sling Shot Extreme Unlimited",
    "3DMark for Android Sling Shot",
    "3DMark for Android Sling Shot Unlimited",
    "3DMark for Android Solar Bay",
    "PCMark for Android Work 3.0",
    "PCMark for Android Storage 2.0",
    "PCMark for Android Work 2.0",
    "PCMark for Android Computer Vision",
    "PCMark for Android Storage"
])


def handleSamsungQuirks(name, chip, googleCsvData, benchMarkDataRow):
    assert (any([chip.startswith(x) for x in ["Snapdragon", "Dimensity", "Helio", "Exynos"]]))

    def isSamsungChip(c):
        return not (c.startswith("Snapdragon") or c.startswith("Dimensity") or c.startswith("Helio"))

    def stripCpuName(n):
        cpuCheck = re.findall(r' \(.*\)$', n)
        return n.replace(cpuCheck[0], "") if len(cpuCheck) > 0 else n

    def findPhones(n, c, csv):
        f = csv[csv['marketing_name'].str.lower() == n]
        return f[f['cpu_make'] == "Samsung"] if isSamsungChip(c) else f[f['cpu_make'] != "Samsung"]

    def fixNoteSpace(n):
        notePhoneCheck = re.findall(r'note [0-9]*', n)
        if len(notePhoneCheck) > 0:
            removedSpace = notePhoneCheck[0].replace(" ", "")
            n = n.replace(notePhoneCheck[0], removedSpace)
        return n

    nameWithoutCPU = stripCpuName(name)
    nameWithoutCPU = fixNoteSpace(nameWithoutCPU)

    foundPhones = findPhones(nameWithoutCPU, chip, googleCsvData)

    if len(foundPhones) == 0:
        nameWithoutNetwork = nameWithoutCPU.replace(" 5g", "").replace(" 4g", "").replace(" lte", "")
        foundPhones = findPhones(nameWithoutNetwork, chip, googleCsvData)

    if len(foundPhones) == 0:
        foundPhones = findPhones(nameWithoutCPU + " 5g", chip, googleCsvData)

    if len(foundPhones) == 0:
        print(f"Couldn't match samsung phone {name}")  # raise Exception(f"Couldn't match {nameWithoutCpu}")
        return []

    result = []
    for _, phoneRow in foundPhones.iterrows():
        merged = dict(phoneRow) | dict(benchMarkDataRow)
        result.append(merged)

    return result


# FIXME: add return type
def getBenchNameToGoogleNameMap(benchDataFrame, googleCsvData) -> dict:
    resultDataFrameDict = {}
    for k in set(benchDataFrame).union(googleCsvData):
        resultDataFrameDict[k] = []

    for _, benchMarkDataRow in benchDataFrame.iterrows():
        chip = benchMarkDataRow['General__Chipset']
        _name = benchMarkDataRow['name'].lower()
        brand = _name.split()[0]
        name = _name[len(brand) + 1:]

        if brand == "apple" or brand == "huawei":
            # Skip apple and huawei devices
            pass
        elif brand == "samsung":
            fullDataRows = handleSamsungQuirks(name, chip, googleCsvData, benchMarkDataRow)
            for phoneData in fullDataRows:
                for k, v in phoneData.items():
                    resultDataFrameDict[k].append(v)
        elif brand == "google":
            name = "pixel 5a 5g" if name == "pixel 5a" else name
            foundPhones = googleCsvData[googleCsvData['marketing_name'].str.lower() == name]
            assert (len(foundPhones) == 1)

            merged = dict(foundPhones.iloc[0]) | dict(benchMarkDataRow)
            for k, v in merged.items():
                resultDataFrameDict[k].append(v)
        elif brand == "asus":
            cpuCheck = re.findall(r' \(.*\)$', name)
            filtered = googleCsvData
            if len(cpuCheck) > 0:
                name = name.replace(cpuCheck[0], "")
        else:
            print(f"\"{brand}\" brand not found")

    return resultDataFrameDict


def addPhoneSpecsToBenchmarkData(benchmarkDataFrame):
    allphonesdf = pd.read_csv(Path('tomnom.all_phones_with_cpu_make.csv'))
    benchNameToGoogleName = getBenchNameToGoogleNameMap(benchmarkDataFrame, allphonesdf)
    return pd.DataFrame(benchNameToGoogleName)


def filterBenchmarkDataOnKeys(in_dict: dict, keys_to_find: set[str]):
    result = {}
    for k, v in in_dict.items():
        if k in keys_to_find:
            if type(v) is dict:
                for ik, iv in v.items():
                    result[f"{k}__{ik}"] = iv
            else:
                result[k] = v

    return result


def buildBenchmarkDataframeFromFilteredData(filteredPhoneDatas):
    foundKeys = set([])
    for phoneData in filteredPhoneDatas:
        for k, _ in phoneData.items():
            foundKeys.add(k)

    result = {}
    for k in foundKeys:
        result[k] = []

    for phoneData in filteredPhoneDatas:
        for k in foundKeys:
            result[k].append(phoneData.get(k))
    return pd.DataFrame(data=result)


def main():
    keys = set([
        "name",
        "General",
    ]).union(benchmarkNames)

    benchmarkJson = json.load(open('benchul.json'))
    filteredPhoneDatas = []
    for phone in benchmarkJson:
        filteredPhoneDatas.append(filterBenchmarkDataOnKeys(phone, keys))

    df = buildBenchmarkDataframeFromFilteredData(filteredPhoneDatas)
    # filepath = Path('benchui_parsed.csv')
    # df.to_csv(filepath)
    fullDf = addPhoneSpecsToBenchmarkData(df)
    fullDf.to_csv("./fullDataWithBenchmarks.csv")

    benchmarkDataKeys = set([])
    for k in list(fullDf):
        for benchmarkKey in benchmarkNames:
            if k.startswith(benchmarkKey):
                benchmarkDataKeys.add(k)

    validCount = []
    for benchmarkKey in benchmarkDataKeys:
        pass
        size = len(fullDf[fullDf[benchmarkKey].isnull()])
        print(f"Size of benchmark {benchmarkKey}: {size}")
        validCount.append((benchmarkKey, size))

    validCount.sort(key=lambda x: x[1])
    print(validCount.join('\n'))

if __name__ == "__main__":
    main()
