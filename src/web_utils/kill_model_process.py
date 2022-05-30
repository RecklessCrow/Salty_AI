import sys
import sh


def kill_pid(model_name):
    try:
        stdout = sh.grep(sh.ps("ax"), model_name)
        active_pid = int(stdout.split(' ')[0])
    except sh.ErrorReturnCode_1:
        print("found nothing")

    sh.kill(active_pid)


if __name__ == '__main__':
    if len(sys.argv) != 2:
        sys.exit(1)

    model_name = sys.argv[1]
    kill_pid(model_name)
