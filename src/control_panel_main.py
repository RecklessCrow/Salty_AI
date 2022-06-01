from website.website_utils import *
import sys

if __name__ == '__main__':

    if len(sys.argv) < 2:
        print("Usage: control_panel_main.py [mode]")
        sys.exit(1)

    mode = sys.argv[1]

    if mode == 'getStatus':
        print(get_all_status())

    elif mode == 'resetHistory':
        if len(sys.argv) < 3:
            print("Usage: control_panel_main.py resetHistory <model_name>")
            sys.exit(1)

        model_name = sys.argv[2]
        reset_table(model_name)

    elif mode == 'killpid':
        if len(sys.argv) < 3:
            print("Usage: control_panel_main.py killpid <model_name>")
            sys.exit(1)

        model_name = sys.argv[2]
        kill_pid(model_name)

    else:
        print("Invalid mode: {}".format(mode))
        sys.exit(1)
