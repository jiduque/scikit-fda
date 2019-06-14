"""
Kernel Smoothing
================

This example uses different kernel smoothing methods over the phoneme data
set and shows how cross validations scores vary over a range of different
parameters used in the smoothing methods. It also show examples of
undersmoothing and oversmoothing.
"""

# Author: Miguel Carbajo Berrocal
# License: MIT

import skfda
import skfda.preprocessing.smoothing.kernel_smoothers as ks
import skfda.preprocessing.smoothing.validation as val
import matplotlib.pylab as plt
import numpy as np

###############################################################################
#
# For this example, we will use the
# :func:`phoneme <skfda.datasets.fetch_phoneme>` dataset. This dataset
# contains the log-periodograms of several phoneme pronunciations. The phoneme
# curves are very irregular and noisy, so we usually will want to smooth them
# as a preprocessing step.
#
# As an example, we will smooth the first 300 curves only. In the following
# plot, the first five curves are shown.

dataset = skfda.datasets.fetch_phoneme()
fd = dataset['data'][:300]

fd[0:5].plot()

###############################################################################
# Here we show the general cross validation scores for different values of the
# parameters given to the different smoothing methods.

param_values = np.linspace(start=2, stop=25, num=24)

# Local linear regression kernel smoothing.
llr = val.optimize_smoothing_parameter(
    fd, param_values, smoothing_method=ks.LocalLinearRegressionSmoother())
llr_fd = llr.best_estimator_.transform(fd)

# Nadaraya-Watson kernel smoothing.
nw = skfda.preprocessing.smoothing.validation.optimize_smoothing_parameter(
    fd, param_values, smoothing_method=ks.NadarayaWatsonSmoother())
nw_fd = nw.best_estimator_.transform(fd)

# K-nearest neighbours kernel smoothing.
knn = skfda.preprocessing.smoothing.validation.optimize_smoothing_parameter(
    fd, param_values, smoothing_method=ks.KNeighborsSmoother())
knn_fd = knn.best_estimator_.transform(fd)

plt.plot(param_values, knn.cv_results_['mean_test_score'])
plt.plot(param_values, llr.cv_results_['mean_test_score'])
plt.plot(param_values, nw.cv_results_['mean_test_score'])

###############################################################################
# We can plot the smoothed curves corresponding to the 11th element of the data
# set (this is a random choice) for the three different smoothing methods.

ax = plt.gca()
ax.set_xlabel('Smoothing method parameter')
ax.set_ylabel('GCV score')
ax.set_title('Scores through GCV for different smoothing methods')
ax.legend(['k-nearest neighbours', 'local linear regression',
           'Nadaraya-Watson'],
          title='Smoothing method')

fd[10].plot()
knn_fd[10].plot()
llr_fd[10].plot()
nw_fd[10].plot()
ax = plt.gca()
ax.legend(['original data', 'k-nearest neighbours',
           'local linear regression',
           'Nadaraya-Watson'],
          title='Smoothing method')

###############################################################################
# We can compare the curve before and after the smoothing.

# Not smoothed
fd[10].plot()

# Smoothed
plt.figure()
fd[10].scatter(s=0.5)
nw_fd[10].plot(c='g')

###############################################################################
# Now, we can see the effects of a proper smoothing. We can plot the same 5
# samples from the beginning using the Nadaraya-Watson kernel smoother with
# the best choice of parameter.

plt.figure(4)
nw_fd[0:5].plot()

###############################################################################
# We can also appreciate the effects of undersmoothing and oversmoothing in
# the following plots.

fd_us = ks.NadarayaWatsonSmoother(h=2).fit_transform(fd[10])
fd_os = ks.NadarayaWatsonSmoother(h=15).fit_transform(fd[10])

# Under-smoothed
fd[10].scatter(s=0.5)
fd_us.plot()

# Over-smoothed
plt.figure()
fd[10].scatter(s=0.5)
fd_os.plot()
