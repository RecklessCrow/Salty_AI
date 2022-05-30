import os
import subprocess
from base.base_gambler import GAMBLER_ID_DICT


def get_all_status():
    root_dir = '/opt/saltybet/saved_models/'

    # look up here?
    ps = subprocess.Popen(('ps', '-ax'), stdout=subprocess.PIPE)
    output = subprocess.check_output(('grep', 'model_driver_main.py'), stdin=ps.stdout)
    ps.wait()

    stdout = output

    active_model_names = [stdout.split()[-1].decode('utf-8') for stdout in stdout.splitlines()]

    saved_models = [f.name for f in os.scandir(root_dir) if f.is_dir()]

    blocks = []
    for model_name in saved_models:
        if model_name in active_model_names:
            blocks.append(create_block(model_name, "Active"))
        else:
            blocks.append(create_block(model_name, "Inactive"))

    return build_table(blocks)


def get_gamblers():
    gamblers = [(i, x.__name__) for i, x in GAMBLER_ID_DICT.values()]
    options = [f"<option value='{x[0]}'>{x[1]}</option>" for x in gamblers]
    return f"""
    <select id="gamblers">
        {''.join(options)}
    </select>
    """


def create_block(name, status):
    return f"""
    <tr>
        <td>{name}</td>
        <td>{status}</td>
        <td>{get_gamblers()}</td>
        <td><form method="post"><button type="submit" 
        name="{'spawn_button' if status == 'Inactive' else 'kill_button'}" 
        value="{name}">{'Spawn Model' if status == 'Inactive' else 'Kill'}</button></form></td>
    </tr>
    """


def build_table(blocks):
    return f"""
<div>
    <h3>Model Status</h3>
    <table>
        <tr>
            <th>Model Name</th>
            <th>Status</th>
        </tr>
        {"".join(blocks)}
    </table>
</div>
"""


if __name__ == '__main__':
    print("TESTING STATUS")
    html_table = get_all_status()
    print(html_table)
    print("Done")
