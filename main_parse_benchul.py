import json
import pandas as pd
from pathlib import Path
import re

benchmarkNames = set([
    # "3DMark for Android Wild Life",
    # "3DMark for Android Wild Life Unlimited",
    "3DMark for Android Wild Life Extreme",
    # "Wild Life Extreme Unlimited",

    # "3DMark for Android Sling Shot Extreme (OpenGL ES 3.1)",
    # "3DMark for Android Sling Shot Extreme (Vulkan)",
    # "3DMark for Android Sling Shot Extreme Unlimited",
    # "3DMark for Android Sling Shot",
    # "3DMark for Android Sling Shot Unlimited",

    # "3DMark Sling Shot Extreme (OpenGL ES 3.1)",
    # "3DMark Sling Shot Extreme (Vulkan)",
    # "3DMark Sling Shot Extreme Unlimited",
    # "3DMark Sling Shot",
    # "3DMark Sling Shot Unlimited",

    # "3DMark for Android Solar Bay",
    # "PCMark for Android Work 3.0",
    # "PCMark for Android Storage 2.0",
    # "PCMark for Android Work 2.0",
    # "PCMark for Android Computer Vision",
    # "PCMark for Android Storage",
])

failedSamsungDevices = []
def handleSamsungQuirks(name, chip, googleCsvData, benchMarkDataRow):
    if not any([chip.startswith(x) for x in ["Snapdragon", "Dimensity", "Helio", "Exynos"]]):
        failedSamsungDevices.append(name)
        return []

    assert (any([chip.startswith(x) for x in ["Snapdragon", "Dimensity", "Helio", "Exynos"]]))

    def isSamsungChip(c):
        return not (c.startswith("Snapdragon") or c.startswith("Dimensity") or c.startswith("Helio"))

    def stripCpuName(n):
        cpuCheck = re.findall(r' \(.*\)$', n)
        return n.replace(cpuCheck[0], "") if len(cpuCheck) > 0 else n

    def findPhones(n, c, csv):
        f = csv[csv['marketing_name'].str.lower() == n]
        return f[f['cpu_make'] == "Samsung"] if isSamsungChip(c) else f[f['cpu_make'] != "Samsung"]

    def fixNumberSpace(word, n):
        notePhoneCheck = re.findall(re.escape(word) + r' [0-9]*', n)
        if len(notePhoneCheck) > 0:
            removedSpace = notePhoneCheck[0].replace(" ", "")
            n = n.replace(notePhoneCheck[0], removedSpace)
        return n

    def fixNoteSpace(n):
        return fixNumberSpace('note', n)

    def fixWidePhoneSpace(n):
        return fixNumberSpace('wide', n)

    def stripYear(n):
        n = n.replace(" 2018", "")
        n = n.replace(" 2022", "")
        return n

    if name in [
        'galaxy j3 eclipse',# The CPU of this phone doesn't match our database. So skip it
        'galaxy j3 v',# The CPU of this phone doesn't match our database. So skip it
        'galaxy m13 5g',# The CPU of this phone doesn't match our database. So skip it
        'w22 5g',
                ]:
        return []

    nameWithoutCPU = stripCpuName(name)
    nameWithoutCPU = nameWithoutCPU.strip()

    if nameWithoutCPU == "galaxy tab s4 10.5":
        nameWithoutCPU = "galaxy tab s4"
    elif nameWithoutCPU == 'galaxy a9':
        nameWithoutCPU = "galaxy a9(2016)"
    elif nameWithoutCPU == 'galaxy j7 2017':
        nameWithoutCPU = "galaxy j7"
    elif nameWithoutCPU == 'galaxy a3 2017':
        nameWithoutCPU = 'galaxy a3 (2017)'
    elif nameWithoutCPU == 'galaxy a7 2017':
        nameWithoutCPU = 'galaxy a7(2017)'
    elif nameWithoutCPU == 'galaxy a5 2017':
        nameWithoutCPU = 'galaxy a5(2017)'

    foundPhones = findPhones(nameWithoutCPU, chip, googleCsvData)

    if len(foundPhones) == 0:
        fixedNoteSpace = fixNoteSpace(nameWithoutCPU)
        foundPhones = findPhones(fixedNoteSpace, chip, googleCsvData)

    if len(foundPhones) == 0:
        fixedWideSpace = fixWidePhoneSpace(nameWithoutCPU)
        foundPhones = findPhones(fixedWideSpace, chip, googleCsvData)
        if len(foundPhones) == 0:
            foundPhones = findPhones(fixedWideSpace+' ', chip, googleCsvData)

    if len(foundPhones) == 0:
        nameWithoutCPU = fixNumberSpace('quantum', nameWithoutCPU)
        foundPhones = findPhones(fixedWideSpace, chip, googleCsvData)

    if len(foundPhones) == 0:
        nameWithoutCPU = fixNumberSpace('xcover', nameWithoutCPU)
        foundPhones = findPhones(fixedWideSpace, chip, googleCsvData)

    if len(foundPhones) == 0:
        nameWithoutNetwork = nameWithoutCPU.replace(" 5g", "").replace(" 4g", "").replace(" lte", "")
        foundPhones = findPhones(nameWithoutNetwork, chip, googleCsvData)

    if len(foundPhones) == 0:
        foundPhones = findPhones(nameWithoutCPU + " 5g", chip, googleCsvData)

    if len(foundPhones) == 0:
        if nameWithoutCPU.endswith(" 2016"):
            nameWithoutCPU = nameWithoutCPU.replace(" 2016", "(2016)")
            foundPhones = findPhones(nameWithoutCPU, chip, googleCsvData)

    if len(foundPhones) == 0:
        foundPhones = findPhones(stripYear(nameWithoutCPU), chip, googleCsvData)

    if len(foundPhones) == 0:
        nameWithoutCPU = nameWithoutCPU.replace(' wi-fi', '')
        nameWithoutCPU = nameWithoutCPU.replace(' wifi', '')
        foundPhones = findPhones(nameWithoutCPU, chip, googleCsvData)

    if len(foundPhones) == 0:
        print(f"Couldn't match samsung phone {name}")  # raise Exception(f"Couldn't match {nameWithoutCpu}")
        raise Exception(f"Couldn't match {name}")

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
        nameWithBrand = benchMarkDataRow['name'].lower()
        brand = nameWithBrand.split()[0]
        name = nameWithBrand[len(brand) + 1:]

        if brand == "apple" or brand == "huawei":
            # Skip apple and huawei devices
            pass
        elif brand == "samsung":
            fullDataRows = handleSamsungQuirks(name, chip, googleCsvData, benchMarkDataRow)
            for phoneData in fullDataRows:
                for k, v in phoneData.items():
                    resultDataFrameDict[k].append(v)
        elif brand == "google":
            if name == "pixel 5a":
                name = "pixel 5a 5g"

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
        elif brand == "oneplus":
            if name in [
                "ace racing",
                'ace 2v',
                'ace 2',
                'ace 2 pro'
            ]:
                continue # We don't have this device????

            foundPhones = googleCsvData[googleCsvData['marketing_name'].str.lower() == nameWithBrand]

            if len(foundPhones) == 0:
                nameWithBrand = nameWithBrand.replace("oneplus 5", "oneplus5")
                nameWithBrand = nameWithBrand.replace("oneplus 6", "oneplus6")
                nameWithBrand = nameWithBrand.replace(" 5g", "")
                foundPhones = googleCsvData[googleCsvData['marketing_name'].str.lower() == f"{nameWithBrand}"]

            if len(foundPhones) == 0:
                if nameWithBrand == 'oneplus nord2t':
                    nameWithBrand = 'oneplus nord 2t'
                elif nameWithBrand == 'oneplus nord 2':
                    nameWithBrand = 'oneplus nord2'

                foundPhones = googleCsvData[googleCsvData['marketing_name'].str.lower() == f"{nameWithBrand} 5g"]

            if len(foundPhones) == 0:
                pass
                print("...")

            merged = dict(foundPhones.iloc[0]) | dict(benchMarkDataRow)
            for k, v in merged.items():
                resultDataFrameDict[k].append(v)

        elif brand == "xiaomi":
            if name in [
                "redmi k50 extreme edition",
                "mi 6",
                "mi mix 2",
                "black shark helo",
                "mi 8 explorer edition",
                "black shark 3",
                "mi 11x",
                "poco x3 gt",
                'mi mix 4',
                'black shark 4',
                'mi 11t',
                'black shark 4s pro',
                'redmi note 11t pro+'
            ]:
                continue # We don't have this device????

            # Fix for redmi not 8 2021
            name = name.replace(" 2021", "")

            # Fix for redmi note 11 pro global
            name = name.replace(" global", "")

            # Fix for poco m4 5g india
            name = name.replace(" india", "")
            name = name.replace(" (india)", "")
            name = name.replace(" (china)", "")

            # Fix for poco m4 pro 4g
            name = name.replace(" 4g", "")

            # Fix for note 11se
            name = name.replace(" 11se", " 11 se")

            # Fix for note 11e pro
            name = name.replace("11e pro", "11e pro ")

            nameWithBrand = nameWithBrand.replace("civi 2", "civi2")

            # Fix for poco x5 5g
            name = name.replace("poco x5 5g", "poco x5 5g ")

            name = name.replace("pocophone f1", "poco f1")
            name = name.replace(" transparent edition", "")
            name = name.replace("redmi k30 pro", "k30 pro")
            name = name.replace("k30 pro zoom", "redmi k30 pro zoom edition")
            name = name.replace('redmi k40 gaming edition', "redmi k40 gaming")
            name = name.replace('redmi k50 gaming edition', "redmi k40 gaming")

            #FIXME: check if this is right
            if name == "black shark": # 'xiaomi black shark 2' is ok
                name = "shark"
            elif name == "redmi k30s":
                name = "redmi k30s ultra"

            cpuCheck = re.findall(r' \(.*\)$', nameWithBrand)
            if len(cpuCheck) > 0:
                #FIXME: this is very messy
                nameWithBrand = nameWithBrand.replace(cpuCheck[0], "")

            foundPhones = googleCsvData[googleCsvData['marketing_name'].str.lower() == nameWithBrand]
            if len(foundPhones) == 0:
                foundPhones = googleCsvData[googleCsvData['marketing_name'].str.lower() == name]

            if len(foundPhones) == 0:
                foundPhones = googleCsvData[googleCsvData['marketing_name'].str.lower() == f"{name} 5g"]

            if len(foundPhones) == 0:
                foundPhones = googleCsvData[googleCsvData['marketing_name'].str.lower() == name.replace(" 5g", "")]

            x = len(foundPhones)
            if x == 0:
                #assert (len(foundPhones) > 0)
                continue

            merged = dict(foundPhones.iloc[0]) | dict(benchMarkDataRow)
            for k, v in merged.items():
                resultDataFrameDict[k].append(v)
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

def startsWithCaseInsensitive(inStr, startSection):
    return bool(re.match(startSection, inStr, re.IGNORECASE))

def main():
    keys = set([
        "name",
        "popularity",
        "url",
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
    print(failedSamsungDevices)
