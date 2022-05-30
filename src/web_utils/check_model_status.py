import os
import sh


def get_all_status():
    root_dir = '/opt/saltybet/saved_models/'

    try:
        stdout = sh.grep(sh.ps("a"), 'python')
        active_model_full = stdout.split('\n')
        print(active_model_full)
        active_model_names = [x.split(' ')[-1] for x in active_model_full]
        print(active_model_names)
    except sh.ErrorReturnCode_1:
        active_model_names = []
        print("found nothing")

    walker = os.walk(root_dir)
    next(walker)  # skip the first one
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
