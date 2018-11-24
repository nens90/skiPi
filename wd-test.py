import time
import sys

WATCHDOG = "/dev/watchdog"
WD_INTERVAL = 5


def log_debug(msg, end='\n'):
    sys.stdout.write(msg + end)

def kick_watchdog():
    log_debug(".", end='')
    with open(WATCHDOG, 'w') as wd_fd:
        wd_fd.write('1')

if __name__ == '__main__':
    
    app_is_running = 1
    kick_watchdog()
    
    while app_is_running:
        time.sleep(WD_INTERVAL - 1) # Watchdog interval minus 1 second
        kick_watchdog()
    log_debug("Exiting...")
