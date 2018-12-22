#!/usr/bin/env python3
"""
skipi is a project for synchronization of WS281x LED strips (aka NeoPixels) 
over an ad-hoc network connection.
"""

import sys
import time
import argparse
import signal
import queue
import subprocess

import skibase

import wd
import kfnet
import butt
import ws281x
import sphat


# ============================= Tasks =======================================
def do_shutdown():
    skibase.log_notice("Calling shutdown")
    cmd = "sudo nohup sh -c 'sleep 5; shutdown -h now' >/dev/null 2>&1 &"
    subprocess.call(cmd, shell=True)
    wd.wd_kick()  # should work with a sleep of 5 seconds and a wd kick

def do_delay_task(task):
    if task > skibase.TASK_DELAY_MS and \
       ((task & skibase.MAJOR_TASK) == skibase.TASK_DELAY_MS):
        delay = task & skibase.MINOR_TASK
        skibase.log_debug("Delay: %d ms" %delay)
        time.sleep(delay / 1000)
    else:
        skibase.log_warning("Delay: task %04x not within limits" %task)

def get_program_from_task(task):
    if task >= skibase.TASK_PROGRAM and \
       ((task & skibase.MAJOR_TASK) == skibase.TASK_PROGRAM):
        program = task & skibase.MINOR_TASK
        skibase.log_debug("Program from task: %02x" % \
          program_id_to_str(program))
        return program
    else:
        skibase.log_warning("Program: task %s not within limits" % \
          skibase.task_to_str(task))
        return 0
        

        
# ============================= Programs ====================================
PROGRAM_DEFAULT = 0
PROGRAM_ID_MAX = 3

def program_id_to_str(program_id):
    return ("%02x" % program_id)

def get_program_id_from_str(program_str):
    return int(program_str, 16)
    
def get_next_program(program_id):
    return (program_id+1) % (PROGRAM_ID_MAX+1)
    

# ============================= argparse ====================================   
def args_add_all(parser):
    # === Logging ===
    parser = skibase.args_add_log(parser)
    # === Watchdog ===
    parser = wd.args_add_wd(parser)
    # === Kesselfall Network ===
    parser = kfnet.args_add_kfnet(parser)
    # === WS281x ===
    parser = ws281x.args_add_ws281x(parser)
    # === Scroll PHAT ===
    parser = sphat.args_add_sphat(parser)
    # === Butt ===
    
    # === Main ===
    # Start program
    parser.add_argument(
      '-m', '--program',
      type=int,
      action="store",
      dest="start_program",
      default=PROGRAM_DEFAULT,
      help="Starting Program ID. Default: %d" %PROGRAM_DEFAULT
    )
    # === Tests ===
    # nettest
    #parser.add_argument( 
    #  '--nettest',
    #  action="store_true",
    #  dest="nettest",
    #  default=False,
    #  help="Run network-only test; (not supported yet)"
    #)
    # ledtest
    #parser.add_argument( 
    #  '--ledtest',
    #  action="store_true",
    #  dest="ledtest",
    #  default=False,
    #  help="Run LED-only test; (not supported yet)"
    #)
    # ledtest
    #parser.add_argument(
    #  '--sphattest',
    #  action="store_true",
    #  dest="sphattest",
    #  default=False,
    #  help="Run sphat-only test; (not supported yet)"
    #)

    return parser

    
    
# ============================= Main ========================================

# ----------------------------- Loop ----------------------------------------
LOOP_SPEED = 0.8

def loop(main_queue, program_id, kfnet_obj, butt_obj):
    next_kick = 0
    
    while not skibase.signal_counter \
      and kfnet_obj.status() \
      and butt_obj.status():
        next_kick = wd.wd_check(next_kick)
        try:
            task = main_queue.get(block=True, timeout=LOOP_SPEED)
        except queue.Empty:
            task = None
        if task is not None:
            if task == skibase.TASK_BUTTON_PRESS:
                program_id = get_next_program(program_id)
                # Add program_id to kfnet as a task that is transmitted
                # Do not execute task yet, but wait for kfnet to relay
                # the task back when it is sent. This should make the
                # network appear more "in sync".
                kfnet_obj.queue_task(skibase.TASK_PROGRAM + program_id)
                skibase.log_info("task: press: %s" % \
                  program_id_to_str(program_id))
            elif task == skibase.TASK_BUTTON_LONG:
                skibase.log_info("task: long press")
                do_shutdown()
                main_queue.task_done()
                break
            elif (task & skibase.MAJOR_TASK) == skibase.TASK_DELAY_MS:
                skibase.log_info("task: delay")
                do_delay_task(task)
            elif (task & skibase.MAJOR_TASK) == skibase.TASK_PROGRAM:
                program_id = get_program_from_task(task)
                skibase.log_notice("task: program: %s" % \
                  program_id_to_str(program_id))
                # todo handle new program
            else:
                skibase.log_warning("skipi got unknown task!")
                try:
                    skibase.log_warning("task: %s" %task_to_str(task))
                except:
                    skibase.log_warning("log task failed...")
                    print(task)
            main_queue.task_done()
           

# ---------------------------------------------------------------------------
def main():
    skibase.set_time_start()
    
    # Arguments
    parser = argparse.ArgumentParser(description=__doc__)
    parser = args_add_all(parser)
    args = parser.parse_args()
    
    # Parse
    skibase.log_config(args.loglevel.upper(), args.syslog)
    
    # Watchdog
    wd.wd_set_handle(args.watchdog)
    
    # Signal
    skibase.signal_setup([signal.SIGINT, signal.SIGTERM])
    
    # Start queue
    main_queue = queue.Queue()
    
    # Expect the main-loop to kick the watchdog again before time runs out.
    wd.wd_kick()
    
    # Start scroll phat

    # Start LED strip (WS281x)
    
    # Start the Kesselfall network protocol
    kfnet_obj = kfnet.kfnet_start(main_queue,
                                  args.interface,
                                  kfnet.MCAST_GRP, 
                                  args.ip_addr,
                                  args.mcast_port)
    # Start button
    butt_obj = butt.butt_start(main_queue)
    

    # Run
    skibase.log_notice("Running skipi")
    loop(main_queue, args.start_program, kfnet_obj, butt_obj)
    
    # Stop
    kfnet_obj = kfnet.kfnet_stop(kfnet_obj)
    butt_obj = butt.butt_stop(butt_obj)
    # Empty queue and stop
    while main_queue.empty() is False:
        main_queue.get()
        main_queue.task_done()
    skibase.log_notice("\nskipi ended...")
    
    
if __name__ == '__main__':
    main()

#EOF
