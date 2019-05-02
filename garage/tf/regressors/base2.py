"""Regressor base classes without Parameterized."""
import abc

import tensorflow as tf

from garage.misc.tensor_utils import flatten_tensors
from garage.misc.tensor_utils import unflatten_tensors


class Regressor2(abc.ABC):
    """
    Regressor base class without Parameterized.

    Args:
        input_shape (tuple): Input shape.
        output_dim (int): Output dimension.
        name (str): Name of the regressor.
    """

    def __init__(self, input_shape, output_dim, name):
        self._input_shape = input_shape
        self._output_dim = output_dim
        self._name = name
        self._variable_scope = None
        self._cached_params = {}
        self._cached_param_dtypes = {}
        self._cached_param_shapes = {}
        self._cached_assign_ops = {}
        self._cached_assign_placeholders = {}

    def fit(self, xs, ys):
        """
        Fit with input data xs and label ys.

        Args:
            xs: Input data.
            ys: Label of input data.
        """
        raise NotImplementedError

    def predict(self, xs):
        """
        Predict ys based on input xs.

        Args:
            xs: Input data.
        """
        raise NotImplementedError

    def get_params_internal(self, **tags):
        """
        Get the list of parameters.

        This internal method does not perform caching, and should
        be implemented by subclasses.
        """
        raise NotImplementedError

    def get_params(self, **tags):
        """
        Get the list of parameters, filtered by the provided tags.

        Some common tags include 'regularizable' and 'trainable'
        """
        tag_tuple = tuple(sorted(list(tags.items()), key=lambda x: x[0]))
        if tag_tuple not in self._cached_params:
            self._cached_params[tag_tuple] = self.get_params_internal(**tags)
        return self._cached_params[tag_tuple]

    def get_param_dtypes(self, **tags):
        """Get the list of dtypes for the parameters."""
        tag_tuple = tuple(sorted(list(tags.items()), key=lambda x: x[0]))
        if tag_tuple not in self._cached_param_dtypes:
            params = self.get_params(**tags)
            param_values = tf.get_default_session().run(params)
            self._cached_param_dtypes[tag_tuple] = [
                val.dtype for val in param_values
            ]
        return self._cached_param_dtypes[tag_tuple]

    def get_param_shapes(self, **tags):
        """Get the list of shapes for the parameters."""
        tag_tuple = tuple(sorted(list(tags.items()), key=lambda x: x[0]))
        if tag_tuple not in self._cached_param_shapes:
            params = self.get_params(**tags)
            param_values = tf.get_default_session().run(params)
            self._cached_param_shapes[tag_tuple] = [
                val.shape for val in param_values
            ]
        return self._cached_param_shapes[tag_tuple]

    def get_param_values(self, **tags):
        """Get the list of values for the parameters."""
        params = self.get_params(**tags)
        param_values = tf.get_default_session().run(params)
        return flatten_tensors(param_values)

    def set_param_values(self, flattened_params, name=None, **tags):
        """Set the values for the parameters."""
        with tf.name_scope(name, 'set_param_values', [flattened_params]):
            debug = tags.pop('debug', False)
            param_values = unflatten_tensors(flattened_params,
                                             self.get_param_shapes(**tags))
            ops = []
            feed_dict = dict()
            for param, dtype, value in zip(
                    self.get_params(**tags), self.get_param_dtypes(**tags),
                    param_values):
                if param not in self._cached_assign_ops:
                    assign_placeholder = tf.placeholder(
                        dtype=param.dtype.base_dtype)
                    assign_op = tf.assign(param, assign_placeholder)
                    self._cached_assign_ops[param] = assign_op
                    self._cached_assign_placeholders[
                        param] = assign_placeholder
                ops.append(self._cached_assign_ops[param])
                feed_dict[self._cached_assign_placeholders[
                    param]] = value.astype(dtype)
                if debug:
                    print('setting value of %s' % param.name)
            tf.get_default_session().run(ops, feed_dict=feed_dict)

    def __getstate__(self):
        """Object.__getstate__."""
        new_dict = self.__dict__.copy()
        del new_dict['_cached_params']
        del new_dict['_cached_param_dtypes']
        del new_dict['_cached_param_shapes']
        del new_dict['_cached_assign_ops']
        del new_dict['_cached_assign_placeholders']
        return new_dict

    def __setstate__(self, state):
        """Object.__setstate__."""
        self._cached_params = {}
        self._cached_param_dtypes = {}
        self._cached_param_shapes = {}
        self._cached_assign_ops = {}
        self._cached_assign_placeholders = {}
        self.__dict__.update(state)


class StochasticRegressor2(Regressor2):
    """
    StochasticRegressor base class.

    Args:
        input_shape (tuple): Input shape.
        output_dim (int): Output dimension.
        name (str): Name of the regressor.
    """

    def __init__(self, input_shape, output_dim, name):
        super().__init__(input_shape, output_dim, name)

    def log_likelihood_sym(self, x_var, y_var, name=None):
        """
        Symbolic graph of the log likelihood.

        Args:
            x_var: Input tf.Tensor for the input data.
            y_var: Input tf.Tensor for the label of data.
            name: Name of the new graph.
        """
        raise NotImplementedError

    def dist_info_sym(self, x_var, name=None):
        """
        Symbolic graph of the distribution.

        Args:
            x_var: Input tf.Tensor for the input data.
            name: Name of the new graph.
        """
        raise NotImplementedError
