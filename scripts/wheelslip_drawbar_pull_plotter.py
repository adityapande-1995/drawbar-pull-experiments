#!/usr/bin/env python3
#
# Copyright 2022 Open Source Robotics Foundation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# Desc: helper script for plotting wheel slip and drawbar pull force
# Author: Steve Peters
#
import argparse
import math
import matplotlib
import numpy as np
import rclpy
import sys
from gazebo_msgs.msg import WheelSlip
from geometry_msgs.msg import Wrench
from matplotlib import pyplot as plt
from rclpy.node import Node

DEFAULT_DATAPOINTS_TO_DROP_AFTER_WRENCH_CHANGE = 10
DEFAULT_PLOT_XLIM = 80
DEFAULT_PLOT_YLIM = 1.1
DEFAULT_WHEEL_SLIP_NAME = 'wheel_rear_left'
DEFAULT_VEHICLE_NAME = 'NONE'

class WheelSlipDrawbarPullPlotter(Node):
    def __init__(self, args):
        super().__init__('wheel_slip_drawbar_pull_plotter')
        parser = argparse.ArgumentParser(
            description='Plot wheel slip as a function of drawbar pull drag forces on the back of a vehicle.')
        parser.add_argument('-d', '--drop-points', type=int, default=DEFAULT_DATAPOINTS_TO_DROP_AFTER_WRENCH_CHANGE,
                            help='The number of data points to drop after a change in the wrench value')
        parser.add_argument('-n', '--name', type=str, default=DEFAULT_WHEEL_SLIP_NAME,
                            help='The name of the wheel for which slip will be plotted.')
        parser.add_argument('--xlim', type=float, default=DEFAULT_PLOT_XLIM,
                            help='The horizontal axis limits.')
        parser.add_argument('--ylim', type=float, default=DEFAULT_PLOT_YLIM,
                            help='The vertical axis limits.')
        parser.add_argument('--vehicle_name', type=str, default=DEFAULT_VEHICLE_NAME,
                            help='The name of the vehicle.')
        self.args = parser.parse_args(args[1:])

        self.init_plot()

        self.wrench_slip_pairs = []
        self.wrench_last_msg = None
        self.slip_messages_to_drop_after_wrench_change = self.args.drop_points
        self.slip_messages_since_wrench_change = 0
        self.slip_messages_since_last_ui_update = 0

        self.slip_subscription = self.create_subscription(WheelSlip, 'wheel_slip', self.slip_cb, 10)
        self.wrench_subscription = self.create_subscription(Wrench, 'drawbar_pull', self.wrench_cb, 10)

    def slip_cb(self, data):
        wrench = self.wrench_last_msg
        if (wrench):
            if self.args.name in data.name:
              self.slip_messages_since_wrench_change += 1
              if self.slip_messages_since_wrench_change > self.slip_messages_to_drop_after_wrench_change:
                  self.wrench_slip_pairs.append([wrench, data])
        self.slip_messages_since_last_ui_update += 1
        if self.slip_messages_since_last_ui_update > 400:
            self.plot_ui()

    def wrench_cb(self, data):
        self.wrench_last_msg = data
        self.slip_messages_since_wrench_change = 0
        print(f'{len(self.wrench_slip_pairs)} data pairs stored')
        self.update_plot()

    def init_plot(self):
        self.fig, self.ax = plt.subplots()
        plt.xlabel('Drawbar pull force (N)')
        plt.ylabel('Longitudinal wheel slip') 
        plt.xlim(self.args.xlim * np.array([-1, 1]))
        plt.ylim(self.args.ylim * np.array([-1, 1]))
        plt.title(f'Wheel slip vs drawbar pull - {self.args.name}')
        plt.grid()
        self.plot_dots, = self.ax.plot([], [], '.')
        self.plot_means, = self.ax.plot([], [], 'r+')
        plt.show(block=False)

    def plot_ui(self):
        self.slip_messages_since_last_ui_update = 0
        plt.pause(0.1)

    def update_plot(self):
        if 0 == len(self.wrench_slip_pairs):
            return
        slip = np.zeros([len(self.wrench_slip_pairs)])
        drawbar_pull = np.zeros([len(self.wrench_slip_pairs)])
        for i, wrench_slip in enumerate(self.wrench_slip_pairs):
            slip_index = wrench_slip[1].name.index(self.args.name)
            slip[i] = wrench_slip[1].longitudinal_slip[slip_index]
            drawbar_pull[i] = wrench_slip[0].force.x
        self.plot_dots.set_data(drawbar_pull, slip)

        # todo: multiply drawbar_pull by sign of vehicle velocity
        # normalize drawbar pull forces by vehicle weight

        # compute mean of slip values at each drawbar pull force
        unique_forces = np.array(list(set(drawbar_pull)))
        mean_slips = np.zeros([len(unique_forces)])
        for i, uf in enumerate(unique_forces):
            where = np.where(uf == drawbar_pull)
            mean_slips[i] = np.mean(slip[where])
        self.plot_means.set_data(unique_forces, mean_slips)

        self.plot_ui()
        plt.savefig(self.args.vehicle_name + '_plot.png')

def main(args=sys.argv):
    rclpy.init(args=args)
    args_without_ros = rclpy.utilities.remove_ros_args(args)
    wheel_slip_drawbar_pull_plotter = WheelSlipDrawbarPullPlotter(args_without_ros)
    wheel_slip_drawbar_pull_plotter.get_logger().info('Wheel Slip Drawbar Pull Plotter started')

    try:
        rclpy.spin(wheel_slip_drawbar_pull_plotter)
    except KeyboardInterrupt:
        pass

    wheel_slip_drawbar_pull_plotter.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
