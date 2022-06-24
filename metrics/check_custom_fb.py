import psutil
import subprocess

workon = "/usr/bin/python3"
path = "fb_metrics/"
script = "fb_chrome_metrics.py"

names_start = [ workon + path + "|" + script ]
find = []

for name in names_start:
	for proc in psutil.process_iter():
		pinfo = proc.as_dict(attrs=['pid', 'name', 'cmdline'])
		if str(name).split("|")[1] in str(pinfo['cmdline']):
			try:
				pid = pinfo['pid']
				find.append(name)
			except Exception as e:
				print("e", e)
				
print("find", find)
f = open(path + "start_process.sh", "w")
f.write('')

for o in names_start:
	if o not in find:
		print("o", o)
		f.write(o.replace("|", "") + " >>" + o.replace(workon, "").\
		        replace("|", "").replace(".py", ".logs") + " &\n")
		f.write("sleep 3 \n")
f.close()

subprocess.call(path + "start_process.sh", shell=True)
f = open(path + "start_process.sh", "w")
f.write('')
