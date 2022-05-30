import os
import subprocess
import sh

def get_all_status():
    root_dir = '/opt/saltybet/saved_models/'

    # print(sh.grep(sh.ps("aux"), 'python3'))
    ps_grep = subprocess.run(['ps', 'aux'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=True)
    print(ps_grep.args)
    stdout = ps_grep.stdout
    print(stdout)
    active_model_full = stdout.split('\n')
    active_model_names = [x.split(' ')[-1] for x in active_model_full]

    walker = os.walk(root_dir)
    next(walker) # skip the first one
    saved_models = [x[0].split('/')[-1] for x in walker]

    blocks = []
    for model_name in saved_models:
        if model_name in active_model_names:
            blocks.append(create_block(model_name, "Active"))
        else:
            blocks.append(create_block(model_name, "Inactive"))

    return build_table(blocks)


def create_block(name, status):
    return f"""
    <tr>
        <td>{name}</td>
        <td>{status}</td>
        <td><form method="post"><button type="submit" name="spawn_button" value="{name}">Spawn Model
            </button></form></td>
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
