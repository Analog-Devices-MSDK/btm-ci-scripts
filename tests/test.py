import subprocess

testProc = subprocess.Popen(["bash", "-c", "ocderase max32655_board_B38"])
retCode = testProc.wait()
print(retCode)
