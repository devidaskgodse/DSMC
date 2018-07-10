# -*- coding: utf-8 -*-
"""
Created on Mon Jun 25 19:03:08 2018

@author: malopez
"""
import numpy as np
from numpy import random_intel
import matplotlib.pyplot as plt
from functions import propagate, findMaximumRelativeVelocity, computeCollisions, printProgressBar, compute_a2
                    

# Simulation variables
m = 1
effective_diameter = 1
effective_radius = effective_diameter/2
# Desired particle density
n_density = 0.0000003
baseStateVelocity = 5
# Normal restitution coefficient
alpha = 0.1
# System size and volume
LX = 2000
LY = 2000
LZ = 2000
V = LX*LY*LZ
# Volume occuppied by one particle
particle_volume = (4/3)*np.pi*(effective_radius**3)
# Total number of particles in the system
N = int(n_density*(V/particle_volume)) # La densidad se usa como volumen ocupado/V
# Effective particles represented by each simulation particle.
# Each particle in the program represents 'Ne' particles in the real system.
Ne = 1

mean_free_path = 1 / (np.sqrt(2)*np.pi*(effective_diameter**2)*n_density)
knudsen_number = mean_free_path / min(LX, LY, LZ)
# Bins not used for the moment
n_bins = 50
bin_size = LZ/n_bins
ratio_bin_mfp = bin_size/mean_free_path


# Using Intel's Math Kernel Library
# https://software.intel.com/en-us/blogs/2016/06/15/faster-random-number-generation-in-intel-distribution-for-python
# 'MCG31' gives the best performance, 'MT2203' provides better randomness
# https://software.intel.com/en-us/mkl-vsnotes-basic-generators
random_intel.seed(brng='MT2203')

results = []
for alpha in (0.05, 0.15, 0.25, 0.35, 0.45, 0.55, 0.65, 0.75, 0.85, 0.90, 0.95, 0.97, 1):
    n_runs = 10
    a2_mean = []
    for c in range(n_runs):
        # Initialize particle positions as a 2D numpy array (uniform).
        # As this is DSMC, some particles may be overlapping and not affect the outcome
        pos = random_intel.uniform(effective_radius, LX-effective_radius, (N, 3))
        # Initialize particle velocities as a 2D numpy array (normal/gaussian).
        vel = random_intel.normal(0, baseStateVelocity, (N, 3))
        #plt.hist(vel[:,0], bins=250)
        #plt.scatter(pos[:,0], pos[:,1])
        
        initial_v = np.sqrt(vel[:,0]**2+vel[:,1]**2+vel[:,2]**2)
        initial_mean_v = initial_v.mean()
        mean_free_time = mean_free_path / initial_mean_v
        
        # Simulation lenght and step_time as multiples of mean free times
        simulation_length = 30
        step_duration = 0.01
        dt = step_duration * mean_free_time
        # Number of steps to simulate
        n_steps = int(simulation_length/step_duration)
        
        # TODO: Maybe here is the error --------------------------------------------------------------
        # Maximum relative Velocity
        rv_max = findMaximumRelativeVelocity(initial_v)
        #rv_max =  int(8.5 * np.linalg.norm(vel, axis=1).mean())
        
        print('Number of particles: ', N)
        print('Coefficient of restitution: ', alpha)
        print('LX = ', LX)
        print('LY = ', LY)
        print('LZ = ', LZ)
        print('Density: ', n_density)
        print('Mean free path: ', mean_free_path)
        print('Knudsen number: ', knudsen_number)
        print('Mean free time: ', mean_free_time)
        print('Simulation length: ', simulation_length, ' mean free times')
        print('Time step length: ', step_duration, ' mean free times')
        print()
        
        temperatures = []
        cumulants = []
        n_collisions = 0
        for i in range(n_steps):
            pos = propagate(dt, pos, vel, LX, LY, LZ)
            vel, cols_current_step = computeCollisions(effective_diameter, 
                                                       effective_radius, alpha, 
                                                       V, N, Ne, dt, rv_max, 
                                                       pos, vel)
            n_collisions += cols_current_step
            cols_per_particle = n_collisions / N
            """
            T = (vel[:,0]**2+vel[:,1]**2+vel[:,2]**2).mean()
            temperatures.append(T)
            # Computing different statistics:
            flux = vel.mean(axis=0)
            mass_density = N*m/V
            mean_momentum = N*m*flux
            mean_energy = N*0.5*m*T
            """
            # TODO: Una de las operaciones que más tarda es el cálculo del a2
            # TODO: por eso es conveniente reducirlo al maximo (cada 10 pasos)
            if i%10==0:
                a2 = compute_a2(vel, 3)
                cumulants.append(a2)
            T = (vel[:,0]**2+vel[:,1]**2+vel[:,2]**2).mean()
            temperatures.append(T)
            
            
            printProgressBar(i, n_steps, prefix='Simulating system:', 
                             suffix='completed  -  T = '+str(T)+' - Run: '+str(c+1))
        # print(T)
        # We average over the last 3rd/5th of the data
        a2_mean.append(np.mean(cumulants[-int(len(cumulants)/5):]))
        
    results.append([alpha, np.mean(a2_mean), np.std(a2_mean)])

print()    
#plt.plot(temperatures)
plt.plot(cumulants)