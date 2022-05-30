import subprocess
import sys
import sh


def kill_pid(model_name):

    ps = subprocess.Popen(('ps', '-ax'), stdout=subprocess.PIPE)
    output = subprocess.check_output(('grep', f'model_driver_main.py {model_name}'), stdin=ps.stdout)
    ps.wait()

    active_pid = output.decode('utf-8').split(' ')[0]
    subprocess.call(('kill', active_pid))


if __name__ == '__main__':
    if len(sys.argv) != 2:
        sys.exit(1)

    model_name = sys.argv[1]
    kill_pid(model_name)
