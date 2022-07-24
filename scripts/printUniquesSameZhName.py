# gems.js
import json


if __name__ == "__main__":
    files = ["../accessories.json", "../armour.json",
             "../flasks.json", "../jewels.json", "../weapons.json"]

    uniques = {}
    for file in files:
        with open(file, 'rt', encoding="utf-8") as f:
            data = json.loads(f.read())

            for baseType, baseType_v in data.items():
                for u_id, u_v in baseType_v["uniques"].items():
                    zhName = u_v["zhName"]
                    unique = {"baseType": baseType,
                              "zhBaseType": baseType_v["zhBaseType"],
                              "name":u_id,
                              "zhName":u_v["zhName"] }
                    if zhName in uniques:
                        if type(uniques[zhName]) is list:
                            uniques[zhName].append(unique)
                        else:
                            uniques[zhName] = [uniques[zhName],unique]
                    else:
                        uniques[zhName] = unique

    for u_id,u_v in uniques.items():
        if type(u_v) is list:
            output = f'{u_id}: '
            for v in u_v:
                output += f'{v["zhBaseType"]} '
            print(output)
