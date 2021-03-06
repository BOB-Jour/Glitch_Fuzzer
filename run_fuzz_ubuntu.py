# monitor
import subprocess
import os
import time
import datetime
import threading
import shutil
import argparse
import Dashboard

BROWSER_PATH = ''

METHOD = None

URL = "http://127.0.0.1:8080/flag?" 
MODE1 = "--incognito"  # 시크릿 모드
MODE2 = "--no-sandbox" # 샌드박스 비활성화
MODE3 = "--user-data-dir=./tmp" # debug모드를 할때 FATAL에러 나는걸 피할 수 있다.
TIMEOUT = 300 # 5min
BROWSER_PID = 0
p = None

RUN_FLAG = False
def main():
    global RUN_FLAG, METHOD, DASHBOARD, p
    while(1):
        if RUN_FLAG:
            continue
        RUN_FLAG = True

        chrome_env = os.environ.copy() # ubuntu
        chrome_env['ASAN_OPTIONS'] = "detect_leaks=0,detect_odr_violation=0" # ubuntu

        cmd = []
        cmd.append(BROWSER_PATH)
        cmd.append(URL)
        cmd.append(MODE1)
        cmd.append(MODE2)
        cmd.append(MODE3)
        cmd = " ".join(cmd) # join으로 cmd를 주지 않으면 windows에서와는 다르게 URL 입력이 제대로 되지 않는다.
        p = subprocess.Popen(cmd, env=chrome_env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=1, close_fds=True, shell=True, preexec_fn=os.setsid) 

        BROWSER_PID = p.pid
        DASHBOARD.Chrome_PID = BROWSER_PID 
        while(p.poll() is None): 
            line = p.stderr.readline()
            if (
                (b"AddressSanitizer" in line) 
                or 
                (b"Check failed:".lower() in line.lower()) # for debug mode # case ignore # Check failed:, (dcheck failed:) 
                or
                (b"dcheck" in line.lower()) # for debug mode 
            ): 
                # testcase
                now_time = datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S')
                testcase_copy = './log/crash_%s_'+now_time+'.ttf' 
                shutil.copy2('./templates/glitch_testcase.ttf', testcase_copy % METHOD)

                # dashboard
                if((b"AddressSanitizer" in line)):
                    DASHBOARD.CRSAH_COUNT += 1
                    DASHBOARD.LASTEST_CRASH_TIME = now_time
                elif (b"Check failed:".lower() in line.lower()) or (b"dcheck" in line.lower()):
                    DASHBOARD.DCHECK_COUNT += 1
                    
                # crash log 
                log_path = './log/crash_%s_'+now_time+'.log'
                with open(log_path % METHOD, "wb") as fp:
                    fp.write(line)
                    for line in p.stderr:
                        fp.write(line)

                subprocess.call('pkill -9 chrome', shell=True)
                p.stderr.close()
                p.stdout.close()
                
                DASHBOARD.Chrome_COUNT += 1 

                time.sleep(1)
                RUN_FLAG = False
            
def argparse_init(): 
    parser = argparse.ArgumentParser(description='Glitch Monitor')
    parser.add_argument('--method', '-m', help='METHOD : normal : freetype fuzzing', default='normal')
    
    return parser

def set_fuzzing_type(parser):
    global URL, METHOD
    args = parser.parse_args()
    if(args.method == 'normal'):
        URL += 'freetype_test?ttf=png'
        METHOD = 'freetype'
    elif(args.method == 'freetype'):
        URL += 'freetype_test?ttf=png'
        METHOD = 'freetype'
    else:
        parser.print_help()
        os._exit(1)

if __name__ == '__main__':	
    if(BROWSER_PATH == ''):
        print("[!] Please set the BROWSER_PATH.")
        exit(1)
        
    parser = argparse_init() 
    set_fuzzing_type(parser)
    
    try:
        DASHBOARD = Dashboard.Dashboard()
        DASHBOARD.run_dashboard('./templates/glitch_testcase.ttf')

        while True:
            browser_run_thread = threading.Thread(target=main)
    
            browser_run_thread.start()
            browser_run_thread.join(TIMEOUT) # set timeout 5분 대기

            if browser_run_thread.is_alive():
                subprocess.call('pkill -9 chrome', shell=True)
                p.stderr.close()
                p.stdout.close()
                DASHBOARD.Chrome_COUNT += 1 
                time.sleep(1)
                RUN_FLAG = False
    except KeyboardInterrupt:
        os._exit(0)

