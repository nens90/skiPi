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
import dbgled


# ============================= Tasks =======================================
def do_shutdown():
    skibase.log_notice("Calling shutdown")
    cmd = "sudo nohup sh -c 'sleep 5 && shutdown -h now' >/dev/null 2>&1 &"
    subprocess.call(cmd, shell=True)
    wd.wd_kick()  # should work with a sleep and a watchdog kick

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
        skibase.log_debug("Program from task: %s" % \
          program_id_to_str(program))
        return program
    else:
        skibase.log_warning("Program: task %s not within limits" % \
          skibase.task_to_str(task))
        return 0
        

        
# ============================= Programs ====================================
PROGRAM_CHANGE_BLOCK_MS = 5000
PROGRAM_DEFAULT = 0
PROGRAM_ID_MAX = 0x0B

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
    parser = butt.args_add_butt(parser)
    # === DbgLed ===
    parser = dbgled.args_add_dbgled(parser)
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
    return parser

    
    
# ============================= Main ========================================

# ----------------------------- Loop ----------------------------------------
LOOP_SPEED = 0.8

def loop(main_queue, program_id,
         kfnet_obj, butt_obj,
         sphat_obj, ws281x_obj, dbgled_obj):
    next_kick = 0
    program_can_change_again = 0
    
    while not skibase.signal_counter \
      and kfnet_obj.status() \
      and butt_obj.status() \
      and sphat_obj.status() \
      and ws281x_obj.status() \
      and dbgled_obj.status():
        next_kick = wd.wd_check(next_kick)
        try:
            task = main_queue.get(block=True, timeout=LOOP_SPEED)
        except queue.Empty:
            task = None
        if task:
            if task == skibase.TASK_BUTTON_PRESS:
                now = skibase.get_time_millis()
                if now >= program_can_change_again:
                    program_id = get_next_program(program_id)
                    # Add program_id to kfnet as a task that is transmitted
                    # Do not execute task yet, but wait for kfnet to relay
                    # the task back when it is sent. This should make the
                    # network appear more "in sync".
                    kfnet_obj.queue_task(skibase.TASK_PROGRAM + program_id)
                    skibase.log_info("task: press: %s" % \
                      program_id_to_str(program_id))
                    program_can_change_again = now + PROGRAM_CHANGE_BLOCK_MS
                else:
                    skibase.log_info("Ignoring program change.")
            elif task == skibase.TASK_BUTTON_LONG_1:
                skibase.log_info("task: long press")
                ws281x_obj.program = 0xff
                sphat_obj.program = 0xff                
                dbgled_obj.program = 0xff
            elif task == skibase.TASK_BUTTON_LONG_2:
                do_shutdown()
                main_queue.task_done()
                break
            elif (task & skibase.MAJOR_TASK) == skibase.TASK_DELAY_MS:
                skibase.log_info("task: delay")
                do_delay_task(task)
            elif (task & skibase.MAJOR_TASK) == skibase.TASK_PROGRAM:
                program_id = get_program_from_task(task)
                ws281x_obj.program = program_id
                sphat_obj.program = program_id
                dbgled_obj.program = program_id
                skibase.log_notice("task: program: %s" % \
                  program_id_to_str(program_id))
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
    
    # Start Debug LED
    dbgled_obj = dbgled.dbgled_start(args.start_program, args.dbgpin)
    # Start scroll phat
    sphat_obj = sphat.sphat_start(args.start_program)
    # Start LED strip (WS281x)
    ws281x_obj = ws281x.ws281x_start(args.start_program, args.color)
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
    loop(main_queue, args.start_program,
         kfnet_obj, butt_obj,
         sphat_obj, ws281x_obj, dbgled_obj)
    
    # Stop
    skibase.log_notice("Stopping skipi")
    kfnet_obj = kfnet.kfnet_stop(kfnet_obj)
    butt_obj = butt.butt_stop(butt_obj)
    sphat_obj = sphat.sphat_stop(sphat_obj)
    ws281x_obj = ws281x.ws281x_stop(ws281x_obj)
    dbgled_obj = dbgled.dbgled_stop(dbgled_obj)
    # Empty queue and stop
    while main_queue.empty() is False:
        main_queue.get()
        main_queue.task_done()
    skibase.log_notice("\nskipi ended...")
    
    
if __name__ == '__main__':
    main()

#EOF
