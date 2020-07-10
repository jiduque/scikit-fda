"""Module with generic methods"""

import functools
import types

import numpy as np


def check_is_univariate(fd):
    """Checks if an FData is univariate and raises an error

    Args:
        fd (:class:`~skfda.FData`): Functional object to check if is
            univariate.

    Raises:
        ValueError: If it is not univariate, i.e., `fd.dim_domain != 1` or
            `fd.dim_codomain != 1`.

    """
    if fd.dim_domain != 1 or fd.dim_codomain != 1:
        raise ValueError(f"The functional data must be univariate, i.e., " +
                         f"with dim_domain=1 " +
                         (f"" if fd.dim_domain == 1
                          else f"(currently is {fd.dim_domain}) ") +
                         f"and dim_codomain=1 " +
                         (f"" if fd.dim_codomain == 1 else
                          f"(currently is  {fd.dim_codomain})"))


def _to_grid(X, y, eval_points=None):
    """Transform a pair of FDatas in grids to perform calculations."""

    from .. import FDataGrid
    x_is_grid = isinstance(X, FDataGrid)
    y_is_grid = isinstance(y, FDataGrid)

    if eval_points is not None:
        X = X.to_grid(eval_points)
        y = y.to_grid(eval_points)
    elif x_is_grid and not y_is_grid:
        y = y.to_grid(X.sample_points[0])
    elif not x_is_grid and y_is_grid:
        X = X.to_grid(y.sample_points[0])
    elif not x_is_grid and not y_is_grid:
        X = X.to_grid()
        y = y.to_grid()

    return X, y


def _list_of_arrays(original_array):
    """Convert to a list of arrays.

    If the original list is one-dimensional (e.g. [1, 2, 3]), return list to
    array (in this case [array([1, 2, 3])]).

    If the original list is two-dimensional (e.g. [[1, 2, 3], [4, 5]]), return
    a list containing other one-dimensional arrays (in this case
    [array([1, 2, 3]), array([4, 5])]).

    In any other case the behaviour is unespecified.

    """

    unidimensional = False

    try:
        iter(original_array)
    except TypeError:
        original_array = [original_array]

    try:
        iter(original_array[0])
    except TypeError:
        unidimensional = True

    if unidimensional:
        return [np.asarray(original_array)]
    else:
        return [np.asarray(i) for i in original_array]


def _to_array_maybe_ragged(array, *, row_shape=None):
    """
    Convert to an array where each element may or may not be of equal length.

    If each element is of equal length the array is multidimensional.
    Otherwise it is a ragged array.

    """
    def convert_row(row):
        r = np.array(row)

        if row_shape is not None:
            r = r.reshape(row_shape)

        return r

    array_list = [convert_row(a) for a in array]
    shapes = [a.shape for a in array_list]

    if all(s == shapes[0] for s in shapes):
        return np.array(array_list)
    else:
        res = np.empty(len(array_list), dtype=np.object_)

        for i, a in enumerate(array_list):
            res[i] = a

        return res


def _cartesian_product(axes, flatten=True, return_shape=False):
    """Computes the cartesian product of the axes.

    Computes the cartesian product of the axes and returns a numpy array of
    1 dimension with all the possible combinations, for an arbitrary number of
    dimensions.

    Args:
        Axes (array_like): List with axes.

    Return:
        (np.ndarray): Numpy 2-D array with all the possible combinations.
        The entry (i,j) represent the j-th coordinate of the i-th point.

    Examples:

        >>> from skfda.representation._functional_data import _cartesian_product
        >>> axes = [[0,1],[2,3]]
        >>> _cartesian_product(axes)
        array([[0, 2],
               [0, 3],
               [1, 2],
               [1, 3]])

        >>> axes = [[0,1],[2,3],[4]]
        >>> _cartesian_product(axes)
        array([[0, 2, 4],
               [0, 3, 4],
               [1, 2, 4],
               [1, 3, 4]])

        >>> axes = [[0,1]]
        >>> _cartesian_product(axes)
        array([[0],
               [1]])

    """
    cartesian = np.stack(np.meshgrid(*axes, indexing='ij'), -1)

    shape = cartesian.shape

    if flatten:
        cartesian = cartesian.reshape(-1, len(axes))

    if return_shape:
        return cartesian, shape
    else:
        return cartesian


def _same_domain(fd, fd2):
    """Check if the domain range of two objects is the same."""
    return np.array_equal(fd.domain_range, fd2.domain_range)


def _reshape_eval_points(eval_points, *, aligned, n_samples, dim_domain):
    """Convert and reshape the eval_points to ndarray with the
    corresponding shape.

    Args:
        eval_points (array_like): Evaluation points to be reshaped.
        aligned (bool): Boolean flag. True if all the samples
            will be evaluated at the same evaluation_points.
        dim_domain (int): Dimension of the domain.

    Returns:
        (np.ndarray): Numpy array with the eval_points, if
        evaluation_aligned is True with shape `number of evaluation points`
        x `dim_domain`. If the points are not aligned the shape of the
        points will be `n_samples` x `number of evaluation points`
        x `dim_domain`.

    """

    if aligned:
        eval_points = np.asarray(eval_points)
    else:
        eval_points = _to_array_maybe_ragged(
            eval_points, row_shape=(-1, dim_domain))

    # Case evaluation of a single value, i.e., f(0)
    # Only allowed for aligned evaluation
    if aligned and (eval_points.shape == (dim_domain,)
                    or (eval_points.ndim == 0 and dim_domain == 1)):
        eval_points = np.array([eval_points])

    if aligned:  # Samples evaluated at same eval points

        eval_points = eval_points.reshape((eval_points.shape[0],
                                           dim_domain))

    else:  # Different eval_points for each sample

        if eval_points.shape[0] != n_samples:

            raise ValueError(f"eval_points should be a list "
                             f"of length {n_samples} with the "
                             f"evaluation points for each sample.")

    return eval_points


def parameter_aliases(**alias_assignments):
    """Allows using aliases for parameters"""
    def decorator(f):

        if isinstance(f, (types.FunctionType, types.LambdaType)):
            # f is a function
            @functools.wraps(f)
            def aliasing_function(*args, **kwargs):
                nonlocal alias_assignments
                for parameter_name, aliases in alias_assignments.items():
                    aliases = tuple(aliases)
                    aliases_used = [a for a in kwargs
                                    if a in aliases + (parameter_name,)]
                    if len(aliases_used) > 1:
                        raise ValueError(
                            f"Several arguments with the same meaning used: " +
                            str(aliases_used))

                    elif len(aliases_used) == 1:
                        arg = kwargs.pop(aliases_used[0])
                        kwargs[parameter_name] = arg

                return f(*args, **kwargs)
            return aliasing_function

        else:
            # f is a class

            class cls(f):
                pass

            nonlocal alias_assignments
            init = cls.__init__
            cls.__init__ = parameter_aliases(**alias_assignments)(init)

            set_params = getattr(cls, "set_params", None)
            if set_params is not None:  # For estimators
                cls.set_params = parameter_aliases(
                    **alias_assignments)(set_params)

            for key, value in alias_assignments.items():
                def getter(self):
                    return getattr(self, key)

                def setter(self, new_value):
                    return setattr(self, key, new_value)

                for alias in value:
                    setattr(cls, alias, property(getter, setter))

            cls.__name__ = f.__name__
            cls.__doc__ = f.__doc__
            cls.__module__ = f.__module__

            return cls

    return decorator


def _check_estimator(estimator):
    from sklearn.utils.estimator_checks import (
        check_get_params_invariance, check_set_params)

    name = estimator.__name__
    instance = estimator()
    check_get_params_invariance(name, instance)
    check_set_params(name, instance)
