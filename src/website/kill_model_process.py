import subprocess
import sys


def kill_pid(model_name):

    ps = subprocess.Popen(('ps', '-ax'), stdout=subprocess.PIPE)
    output = subprocess.check_output(('grep', f'model_driver_main.py {model_name}'), stdin=ps.stdout)
    ps.wait()

    print(output)
    active_pid = output.decode('utf-8').split(' ')[1]
    subprocess.call(('kill', active_pid))


if __name__ == '__main__':
    if len(sys.argv) != 2:
        sys.exit(1)

    model_name = sys.argv[1]
    kill_pid(model_name)