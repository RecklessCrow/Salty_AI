import json
import os
import subprocess


def create_run_config(model_name, gambler, user):
    """
    This function creates a run configuration object.
    :return: run_config
    """
    run_config = {
        "user": user,
        "gambler": type(gambler).__name__,
    }

    with open(f"/opt/saltybet/saved_models/{model_name}/run_config.json", "w") as f:
        json.dump(run_config, f)


def kill_pid(model_name):

    ps = subprocess.Popen(('ps', '-ax'), stdout=subprocess.PIPE)
    output = subprocess.check_output(('grep', f'model_driver_main.py {model_name}'), stdin=ps.stdout)
    ps.wait()

    print(output)
    active_pid = output.decode('utf-8').split(' ')[1]
    subprocess.call(('kill', active_pid))


def reset_table(model_name):
    """
    Reset the table for a particular model.
    """
    from utils.database_handler import ModelDatabaseHandler
    database = ModelDatabaseHandler(model_name)
    database.clear_history()


def get_all_status():
    root_dir = '/opt/saltybet/saved_models/'

    # look up here?
    ps = subprocess.Popen(('ps', '-ax'), stdout=subprocess.PIPE)
    stdout = subprocess.check_output(('grep', 'model_main.py'), stdin=ps.stdout)
    ps.wait()

    active_model_names = [stdout.split()[-3].decode('utf-8') for stdout in stdout.splitlines()]
    saved_models = [f.name for f in os.scandir(root_dir) if f.is_dir()]

    blocks = []
    for model_name in saved_models:
        if model_name in active_model_names:
            blocks.append(create_block(model_name, "Active"))
        else:
            blocks.append(create_block(model_name, "Inactive"))

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


def get_gamblers(name, status):
    with open('/opt/saltybet/database/gambler_id.json') as f:
        gamblers = json.load(f)

    options = [f"<option value='{uid}'>{name}</option>" for uid, name in gamblers.items()]

    if status == 'Inactive':
        return f"""
            <select name="selected_gambler">
                {''.join(options)}
            </select>
            """
    else:
        if not os.path.exists(f'/opt/saltybet/saved_models/{name}/run_config.json'):
            return "<p>Unknown</p>"
        with open(f'/opt/saltybet/saved_models/{name}/run_config.json') as f:
            run_config = json.load(f)
            return f"<p>{run_config['gambler']}</p>"


def get_users(name, status):
    with open('/opt/saltybet/database/user_id.json') as f:
        users = json.load(f)['users']

    options = [f"<option value='{user['name']}'>{user['name']}</option>" for user in users]
    if status == 'Inactive':
        return f"""
            <select name="selected_user">
                {''.join(options)}
            </select>
            """
    else:
        if not os.path.exists(f'/opt/saltybet/saved_models/{name}/run_config.json'):
            return "<p>Unknown</p>"
        with open(f'/opt/saltybet/saved_models/{name}/run_config.json') as f:
            run_config = json.load(f)
            return f"<p>{run_config['user']}</p>"


def create_block(name, status):
    # <td><button type="submit" value="{name}" name="reset_button">Reset History</button></td>
    return f"""
    <tr>
        <td>{name}</td>
        <td>{status}</td>

        <form method="post">
        <td>{get_users(name, status)}</td>
        <td>{get_gamblers(name, status)}</td>
        <td><button type="submit" value="{name}" name="spawn_button" {'disabled' if status != 'Inactive' else ''}>Spawn Model</button></td>
        <td><button type="submit" value="{name}" name="kill_button"  {'disabled' if status == 'Inactive' else ''}>Kill</button></td>
        </form>
    </tr>
    """