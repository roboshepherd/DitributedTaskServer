def GetDBusPaths(robots_cfg):
	dbus_paths = []
	f = open(robots_cfg, 'r')
	for line in f.readlines():
		if line.endswith('\n'):
		    line = line[:-1]
		if(line[0] == '/'):
			dbus_paths.append(line)
	f.close()
	return dbus_paths
