import os
import subprocess
import json


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
    with open('/opt/saltybet/database/gambler_id.json') as f:
        gamblers = json.load(f)

    options = [f"<option value='{uid}'>{name}</option>" for uid, name in gamblers.items()]
    return f"""
    <select id="gamblers">
        {''.join(options)}
    </select>
    """


def get_users():
    with open('/opt/saltybet/database/user_id.json') as f:
        users = json.load(f)['users']

    options = [f"<option value='{user['name']}'>{user['name']}</option>" for user in users]
    return f"""
        <select id="users">
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
            <th>Gambler_id</th>
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
