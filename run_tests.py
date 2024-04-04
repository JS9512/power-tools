import json
async def exec_command(cmd,return_error=False):
    import asyncio
    print(f"Executing: {cmd}")
    process = await asyncio.create_subprocess_shell(
        cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )

    stdout, stderr = await process.communicate()
    if return_error:
        return stdout.decode('utf-8').strip(),stderr.decode('utf-8').strip()
    else:
        return  stdout.decode('utf-8').strip()
    

async def run_single_test(test,plugin_name,printgood,counter,sender,send_error,commands):
    template = test["template"]
    output = test["output"]
    for o in output:
        if os.path.exists(o):
            os.remove(o)
   
    testvars = []
    for inp,input in enumerate(test["inputs"]):
        if input["type"]=="file":
            if "formats" not in input:
                return
            testvars.append(input["formats"])
        elif input["type"]=="text":
            to_add = input.get("sample",None)
            if to_add is not None:
                testvars.append(to_add)
            else:
                to_add = {
                    "url":"https://google.com",
                    "word":"hello",
                    "line":"hello world",
                    "ip":"8.8.8.8",
                    "number":"123"

                }[input["format"]]
                testvars.append(to_add)
        elif input["type"] == "filetext":
            testvars.append("tmp.txt")
        elif input["type"] == "button":
            testvars.append(input["options"][0])
    # these have all .pdf .png inside single element, now explode it
    testcases =[]
    for n in range(len(testvars)):
        i = testvars[n]
        if type(i) == list:
            # assume only one input has multiple formats
            for j in i:
                # what we should do is to convert [[.pdf,.png],2] into [[.pdf,2],[.png,2]]
                temp = testvars.copy()
                temp[n] = "."+j
                # print(temp)
                testcases.append(temp)
    if len(testcases)==0:
        testcases = [testvars]
    # print(testcases)

    this_passed = 0
    for testcase in testcases:
        command = template.format(*testcase)
        # printinfo(f"Testing {plugin_name} with command {command}")
        result,error = await exec_command(command,return_error=True)
        if "not found" in error or "No module" in error: 
            if "install_command" in test:
                await sender(f"Installing {plugin_name}...")
                output,error = await exec_command(test["install_command"],return_error=True)
                output,error = await exec_command(command,return_error=True)
        exists = [o for o in output if os.path.exists(o)]
        
        if len(exists):
            this_passed += 1
            commands[command] = "✅"
        elif len([o for o in output if "." in o])==0 and result:
            this_passed += 1
            commands[command] = "✅"
        else:
            commands[command] = "❌"
            try:
                await send_error(f"{plugin_name}\n{result}\n{error}")
            except:
                print(f"{result}\n{error}")
        print("\n\n")
    good = f"✅ {this_passed}/{len(testcases)} #{plugin_name}"
    bad = f"❌{this_passed}/{len(testcases)}  #{plugin_name}"
    if this_passed == len(testcases):
        counter["passed"].append(good)
        await printgood()
    else:
        counter["failed"].append(bad)
        # await sender(f"Failed for {plugin_name}")
    
import os
async def run_all_tests(sender=None,send_error=None):
    os.chdir("../tests")
    if sender is None:
        async def sender(x):
            print(x)
    if send_error is None:
        async def send_error(x):
            print(x)
    with open("../installed.json") as f:
            tests = json.load(f)
    counter = {
        "passed":[],
        "failed":[]
    }
    commands = {}
    tc = 0
    past_passed_tests = []
    async def printgood():
        if len(counter["passed"])%10==0 and len(counter["passed"]):
            tx  = "\n".join(counter["passed"][-10:])
            await sender(tx)

    for plugin_name in tests:
        tc+=1
        # if tc > 5:
        #     continue
        print(f"Testing {tc} {plugin_name}")
        test = tests[plugin_name]
        if test.get("disabled",False):
            # counter["disabled"].append(plugin_name)
            continue
        try:
            await run_single_test(test,plugin_name,printgood,counter,sender,send_error,commands)
            pass
        except Exception as e:
            await send_error(f'CRITICAL: TESTING FAILED for {plugin_name} {e},{e.__traceback__}')
            continue

    if len(past_passed_tests):
        await sender("\n".join(past_passed_tests))

    print("\n".join(counter["passed"]))
    print("\n".join(counter["failed"]))
    await sender("\n".join(counter["passed"]) if counter["passed"] else "No tests passed")
    await sender("\n".join(counter["failed"]) if counter["failed"] else "No tests failed")

    out = ""
    for command in commands:
        out += (f"{commands[command]} : {command}\n")
        if len(out)>3000:
            await send_error(out)
            print(out)
            out = ""
    if len(out):
        await send_error(out)
        print(out)


    os.chdir("../storage")


import asyncio
if __name__=="__main__":
     asyncio.run(run_all_tests())