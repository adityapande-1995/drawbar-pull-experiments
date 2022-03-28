# Generate a report from the experiments (run.py)
import glob
import os
import shutil

with open('summary.md', 'w') as f:
    # Read config
    with open('config/config.yaml', 'r') as config_file:
        content = config_file.readlines()

    f.write('#  --- Results --- \n \n')
    f.writelines(content)
    f.write('\n')

    # Stack the graphs
    f.write('## --- Graphs ---\n')
    cycle0_files = glob.glob('temp/cycle0_*.png')
    cycle1_files = glob.glob('temp/cycle1_*.png')

    cycle0_files.sort()
    cycle1_files.sort()

    for file_c0, file_c1 in zip(cycle0_files, cycle1_files):
        slip_value = file_c0.replace('temp/cycle0_slip_','').replace('.png', '')
        f.write('Plowing effect tricycle (left), Normal tricycle (right) , **slip compliance : ' + slip_value + '**  \n')
        f.write('![image](' +  file_c0 + '){width=350} ![image](' + file_c1 + '){width=350} \\ \n')
        f.write('\n')

os.system('pandoc summary.md -o summary.html')
os.system('rm summary.md')
os.system('xdg-open summary.html')
