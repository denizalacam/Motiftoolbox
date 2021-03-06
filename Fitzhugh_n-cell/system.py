#!/usr/bin/env python

import time
import sys
sys.path.insert(0, '../Tools')
import window as win
import fitzhugh as model
import tools as tl
import numpy as np


def set_params(**kwargs):

	if len(kwargs) == 0:
		kwargs = default_params

	for k in kwargs.keys():

		for c in ['0', 'b', 'g', 'r']:
			model.params[k+'_'+c] = kwargs[k]

	print '# update params', kwargs


set_params(epsilon=0.3)

class system(win.window):

	title = "System"
	figsize = (12, 6)

	def __init__(self, info=None, position=None):
		win.window.__init__(self, position)

		self.x_orbit, self.y_orbit, self.orbit_period = None, None, None
		self.dt = 0.5
		self.stride = 100
		self.info = info

		self.ax = self.fig.add_subplot(121, yticks=[-1.5, -0.5, 0.5, 1.5])
		self.ax.set_xlim(0., 1.)
		self.x_min, self.x_max = -1.5, 1.5
		self.ax.set_ylim(self.x_min, self.x_max)
		self.ax.set_xlabel(r'membrane voltage $V$', fontsize=15)
		self.ax.set_ylabel(r'state $x$', fontsize=15)
		self.li_traj, = self.ax.plot([], [], 'k-', lw=2.)
		self.li_ncl_x, = self.ax.plot([], [], 'y--', lw=2.)
		self.li_ncl_y, = self.ax.plot([], [], 'm--', lw=2.)
		self.tx_state_space = self.ax.text(0.2, -0.5, '', color='r')


		self.ax_text = self.fig.add_subplot(122, frameon=False, xticks=[], yticks=[])

		model.params['g_inh_0'] = 0.01
		self.paramNames = ['I', 'k', 'x', 'epsilon', 'E', 'm', 'sigma', 'g_inh']

                self.texts = {}
                for (i, k) in enumerate(self.paramNames): # model parameters
                        self.texts[k] = self.ax_text.text(0., i, "%s = %lf" % (k, model.params[k+'_0']), fontsize=20)
                self.ax_text.set_ylim(-2, i+2)
		self.N_TEXTS = len(self.ax_text.texts)

		self.key_func_dict.update(dict(C=set_params))
		self.fig.canvas.mpl_connect('button_press_event', self.on_button)
		self.fig.canvas.mpl_connect('button_release_event', self.off_button)
		self.fig.canvas.mpl_connect('axes_enter_event', self.focus_in)
		
		self.refresh_nullclines()
		self.refresh_orbit()



	def focus_in(self, event=None):
		descriptor = "System Parameters :\n I_0 = %lf \n x_0 = %lf \n epsilon_0 = %lf \n k_0 = %lf \n m_0 = %lf\n\n" % (model.params['I_0'], model.params['x_0'], model.params['epsilon_0'], model.params['k_0'], model.params['m_0'])
		descriptor += "'C': change parameters\n"
		descriptor += "right mouse: nullcline position\n"
		descriptor += "left mouse: nullcline shape\n"
		descriptor += "middle mouse: time scale"

		if self.info == None: print descriptor
		else: self.info.set(descriptor)




	def load_initial_condition(self, x, y): # only one phase:  everything's square!
		X = np.zeros((model.N_EQ3), float)
		phi_x, phi_y = tl.PI2*(1.-x), tl.PI2*(1.-y)
		X[::model.N_EQ1] = self.x_orbit([0., phi_x, phi_y])
		X[1::model.N_EQ1] = self.y_orbit([0., phi_x, phi_y])
		return X


	def load_initial_conditions(self, initial_phase): # only one phase:  everything's square!
		initial_phase = np.asarray(initial_phase)

		n = initial_phase.size
		X = np.zeros((n**2, model.N_EQ3), float)
		phi = tl.PI2*(1.-initial_phase)
		X[:, 0], X[:, 1] = self.x_orbit(0.), self.y_orbit(0.)
	
		for i in xrange(n):
			V_i, H_i = self.x_orbit(phi[i]), self.y_orbit(phi[i])
	
			for j in xrange(n):
				X[i*n+j, model.N_EQ1:] = np.array([V_i, H_i, self.x_orbit(phi[j]), self.y_orbit(phi[j])])
	
		return X


	def refresh_nullclines(self):
		x_i = np.arange(self.x_min, self.x_max, 0.01)
		self.li_ncl_x.set_data(model.nullcline_x(x_i, model.params['I_0'], model.params['m_0']), x_i)
		self.li_ncl_y.set_data(model.nullcline_y(x_i, model.params['x_0'], model.params['k_0']), x_i)

                for (i, k) in enumerate(self.paramNames): # model parameters
                        self.texts[k].set_text("%s = %lf" % (k, model.params[k+'_0']))

		self.fig.canvas.draw()


	def refresh_orbit(self):
	
		try:
			new_x, new_y, new_period = model.single_orbit(N_ORBIT=10**4)
			self.x_orbit, self.y_orbit, self.orbit_period = new_x, new_y, new_period
			self.tx_state_space.set_text("")
	
		except:
			self.tx_state_space.set_text("No closed orbit found!")
			pass
		
		phi = np.arange(500.)/float(499.)
		self.li_traj.set_data(self.y_orbit(tl.PI2*phi), self.x_orbit(tl.PI2*phi))
		self.fig.canvas.draw()



	def on_button(self, event):
                if event.inaxes == self.ax:
		        self.event_start = np.array([event.xdata, event.ydata])
			self.event_axes = self.ax

                elif event.inaxes == self.ax_text:
		        self.event_start = np.array([event.xdata, event.ydata])
			self.event_axes = self.ax_text

			dist = np.zeros((self.N_TEXTS), float)

			for n in xrange(self.N_TEXTS):
				dist[n] = max(abs(np.asarray(self.ax_text.texts[n].get_position())-self.event_start))

			self.i_text = np.argmin(dist)
			self.ax_text.texts[self.i_text].set_color('r')

			self.fig.canvas.draw()




	def off_button(self, event):
		delta_params = np.array([event.xdata, event.ydata])-self.event_start

		if self.event_axes == self.ax:

			if event.button == 1:
				set_params(I=model.params['I_0']+delta_params[0], x=model.params['x_0']+delta_params[1])
	
			elif event.button == 2:
				new_eps = model.params['epsilon_0']+delta_params[0]
				set_params(epsilon=model.params['epsilon_0']*(new_eps<0.)+(new_eps>0.)*new_eps)
				
			elif event.button == 3:
				new_m = model.params['m_0']+delta_params[0]
				set_params(m=model.params['m_0']*(new_m<0.)+(new_m>0.)*new_m, k=model.params['k_0']+delta_params[1]*3.)
			


		elif self.event_axes == self.ax_text:
			self.ax_text.texts[self.i_text].set_color('k')

			paramName = self.paramNames[self.i_text]
			oldParam = model.params[self.paramNames[self.i_text]+'_0']

			set_params(**{paramName: oldParam+delta_params[0]})

			self.fig.canvas.draw()


		self.event_axes = None
		

		self.refresh_nullclines()
		self.refresh_orbit()





	def N_output(self, CYCLES):
		return int(CYCLES*self.orbit_period/self.dt)




if __name__ == "__main__":
	
	import pylab as pl

	sys = system()
	pl.show()






