import sys
# split db into 2-2 lines
apps = []
curr = {}
for line in sys.stdin:
    # print(line)
    if len(curr.keys())>0:
        curr["description"] = line.strip()
        apps.append(curr)
        curr = {}
    else:
        # get parameters fromo github.daneren2005.dsub DSub - 5.5.3 (208)
        curr = line.split(" ")
        curr = {
            "package": curr[0].strip(),
            "name": " ".join(curr[1:-3]).strip(),
        }
i=1
for app in apps:
    print(f"{i}. {app['name']} - `{app['package']}`")
    print(f"{app['description']}\n")
    i+=1