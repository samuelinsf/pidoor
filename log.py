
import os.path
import lazytable
import time

def log(source, event, log_path):
    prefix = os.path.join(log_path, source)
    uptime = float(open('/proc/uptime').read().split()[0])
    wall_time = time.time()
    human_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(wall_time))

    tolog = {}
    tolog.update(event)
    tolog['wall_time'] = wall_time
    tolog['human_time'] = human_time
    tolog['uptime'] = uptime
    tolog['source'] = source
    logline = '\t'.join(['%s: %s' % (k,v) for k, v in sorted(tolog.items())]) + '\n'
    f = open(prefix + '_log.txt', 'a')
    f.write(logline)
    f.close()
    t = lazytable.open(prefix + '_log.sqlite', 'log')
    t.insert(tolog)
    t.close()
    return logline

