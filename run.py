#!python3

# Runs a set of experiments, by varying the <slip_compliance_lateral/longitudinal>
# parameters in the world file.

import subprocess
import time
import yaml
import os
import re
import shutil
import numpy as np

def run_test(world_file='worlds/drawbar_pull_demo.world', config=None):
    
    TIME_PER_TEST_RUN = ((config['max-force']  / config['force-increment']) + 2) * config['interval'] * 2
    print("Time per test run (s): ", TIME_PER_TEST_RUN)
    
    # Launch processes
    gz_process = subprocess.Popen(['gzserver', '--verbose' , world_file], stdout=subprocess.PIPE)
    
    time.sleep(3)
    
    drawbar_pull_publisher = subprocess.Popen(['python3', 'scripts/wheelslip_drawbar_pull_publisher.py',
        '--force-increment', str(config['force-increment']),
        '--interval', str(config['interval']),
        '--max-force', str(config['max-force'])], stdout=subprocess.PIPE)
    
    plotter_0 = subprocess.Popen(['python3', 'scripts/wheelslip_drawbar_pull_plotter.py',
        '--drop-points', str(config['drop-points']),
        '--name', str(config['name']),
        '--xlim', str(config['xlim']),
        '--ylim', str(config['ylim']),
        '--vehicle_name', 'cycle0',
        '--ros-args', '--remap', 'wheel_slip:=/trisphere_cycle_slip0/wheel_slip'], stdout=subprocess.PIPE)
    
    plotter_1 = subprocess.Popen(['python3', 'scripts/wheelslip_drawbar_pull_plotter.py',
        '--drop-points', str(config['drop-points']),
        '--name', str(config['name']),
        '--xlim', str(config['xlim']),
        '--ylim', str(config['ylim']),
        '--vehicle_name', 'cycle1',
        '--ros-args', '--remap', 'wheel_slip:=/trisphere_cycle_slip1/wheel_slip'], stdout=subprocess.PIPE)
    
    # Wait for the test to finish
    start = time.time()
    time_elapsed = 0
    
    while time_elapsed < TIME_PER_TEST_RUN:
        time.sleep(1.0)
        time_elapsed = time.time() - start
    
    # Kill processes
    gz_process.kill()
    drawbar_pull_publisher.kill()
    plotter_0.kill()
    plotter_1.kill()

def generate_world_files(slip_increment, slip_max):
    line_numbers = [40, 41, 50, 51, 55, 56, 96, 97, 106, 107, 111, 112]
    world_names = []

    for current_slip_value in np.arange(0.01, slip_max, slip_increment):
        # Read original file
        with open('worlds/drawbar_pull_demo.world') as f:
            contents = f.readlines()
        
        # Substitute slip compliance value
        for n in line_numbers:
            contents[n-1] = re.sub('0', str(current_slip_value), contents[n-1])

        # Write file
        filename = 'temp/slip_' + str(current_slip_value) + '.world'
        with open(filename, 'w') as f:
            f.writelines(contents)

        world_names.append(filename)

    return world_names

if __name__ == '__main__':
    # Cleanup temp directory
    shutil.rmtree(os.path.join(os.getcwd(), 'temp'), ignore_errors=True)
    os.mkdir(os.path.join(os.getcwd(), 'temp'))

    # Parse test arguments
    with open('config/config.yaml', 'r') as stream:
        config_data = yaml.safe_load(stream)

    # Generate world files, return their names
    world_names = generate_world_files(float(config_data['slip-increment']), 
            float(config_data['slip-max']))

    # Run tests on all world files
    for i, temp_world in enumerate(world_names):
        print('Running world ', i+1, ' of ', len(world_names))
        run_test(world_file = temp_world, config = config_data)
        shutil.move('cycle0_plot.png', 'temp/cycle0_' + re.sub('.world', '.png', temp_world.replace('temp/', '')) )
        shutil.move('cycle1_plot.png', 'temp/cycle1_' + re.sub('.world', '.png', temp_world.replace('temp/', '')) )
