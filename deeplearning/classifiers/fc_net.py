import numpy as np

from deeplearning.layers import *
from deeplearning.layer_utils import *


class TwoLayerNet(object):
    """
    A two-layer fully-connected neural network with ReLU nonlinearity and
    softmax loss that uses a modular layer design. We assume an input dimension
    of D, a hidden dimension of H, and perform classification over C classes.

    The architecure should be affine - relu - affine - softmax.

    Note that this class does not implement gradient descent; instead, it
    will interact with a separate Solver object that is responsible for running
    optimization.

    The learnable parameters of the model are stored in the dictionary
    self.params that maps parameter names to numpy arrays.
    """

    def __init__(self, input_dim=3 * 32 * 32, hidden_dim=100, num_classes=10,
                 weight_scale=1e-3, reg=0.0):
        """
        Initialize a new network.

        Inputs:
        - input_dim: An integer giving the size of the input
        - hidden_dim: An integer giving the size of the hidden layer
        - num_classes: An integer giving the number of classes to classify
        - weight_scale: Scalar giving the standard deviation for random
          initialization of the weights.
        - reg: Scalar giving L2 regularization strength.
        """
        self.params = {
          'W1': None,
          'W2' : None,
          'b1': None,
          'b2': None
        }
        self.reg = reg

        self.params['W1'] = np.random.normal(0, weight_scale, (input_dim, hidden_dim))
        self.params['b1'] = np.zeros((hidden_dim,))
        self.params['W2'] = np.random.normal(0, weight_scale, (hidden_dim, num_classes))
        self.params['b2'] = np.zeros((num_classes,))     


    def loss(self, X, y=None):
        """
        Compute loss and gradient for a minibatch of data.

        Inputs:
        - X: Array of input data of shape (N, d_1, ..., d_k)
        - y: Array of labels, of shape (N,). y[i] gives the label for X[i].

        Returns:
        If y is None, then run a test-time forward pass of the model and return:
        - scores: Array of shape (N, C) giving classification scores, where
          scores[i, c] is the classification score for X[i] and class c.

        If y is not None, then run a training-time forward and backward pass and
        return a tuple of:
        - loss: Scalar value giving the loss
        - grads: Dictionary with the same keys as self.params, mapping parameter
          names to gradients of the loss with respect to those parameters.
        """
        scores = None

        hidden_layer_out, cache_hidden = affine_relu_forward(X, self.params['W1'], self.params['b1'])
        scores, cache_output = affine_forward(hidden_layer_out, self.params['W2'], 
                                         self.params['b2'])

        # If y is None then we are in test mode so just return scores
        if y is None:
            return scores

        loss, grads = 0, {}

        # Loss calculations  
        W1_frobenius_norm_squared = np.linalg.norm(self.params['W1'], 'fro') ** 2
        W2_frobenius_norm_squared = np.linalg.norm(self.params['W2'], 'fro') ** 2
        softmax, dout = softmax_loss(scores, y)
        loss = softmax + self.reg * 0.5 * (W1_frobenius_norm_squared + W2_frobenius_norm_squared)
      
        # Grad calculations 
        dhidden, dW2, db2 = affine_backward(dout, cache_output)
        grads['W2'] = dW2 + self.reg * self.params['W2']
        grads['b2'] = db2

        dx, dW1, db1 = affine_relu_backward(dhidden, cache_hidden)
        grads['W1'] = dW1 + self.reg * self.params['W1']
        grads['b1'] = db1

        return loss, grads


class FullyConnectedNet(object):
    """
    A fully-connected neural network with an arbitrary number of hidden layers,
    ReLU nonlinearities, and a softmax loss function. This will also implement
    dropout and batch normalization as options. For a network with L layers,
    the architecture will be

    {affine - [batch norm] - relu - [dropout]} x (L - 1) - affine - softmax

    where batch normalization and dropout are optional, and the {...} block is
    repeated L - 1 times.

    Similar to the TwoLayerNet above, learnable parameters are stored in the
    self.params dictionary and will be learned using the Solver class.
    """

    def __init__(self, hidden_dims, input_dim=3 * 32 * 32, num_classes=10,
                 dropout=0, use_batchnorm=False, reg=0.0,
                 weight_scale=1e-2, dtype=np.float32, seed=None):
        """
        Initialize a new FullyConnectedNet.

        Inputs:
        - hidden_dims: A list of integers giving the size of each hidden layer.
        - input_dim: An integer giving the size of the input.
        - num_classes: An integer giving the number of classes to classify.
        - dropout: Scalar between 0 and 1 giving dropout strength. If dropout=0 then
          the network should not use dropout at all.
        - use_batchnorm: Whether or not the network should use batch normalization.
        - reg: Scalar giving L2 regularization strength.
        - weight_scale: Scalar giving the standard deviation for random
          initialization of the weights.
        - dtype: A numpy datatype object; all computations will be performed using
          this datatype. float32 is faster but less accurate, so you should use
          float64 for numeric gradient checking.
        - seed: If not None, then pass this random seed to the dropout layers. This
          will make the dropout layers deteriminstic so we can gradient check the
          model.
        """
        self.use_batchnorm = use_batchnorm
        self.use_dropout = dropout > 0
        self.reg = reg
        self.num_layers = 1 + len(hidden_dims)
        self.dtype = dtype
        self.params = {}

        
        for index in range(1, self.num_layers + 1):
            if index == 1:
                # First layer: input_dim -> hidden_dims[0]
                self.params[f"W{index}"] = np.random.normal(0, weight_scale, (input_dim, hidden_dims[index - 1]))
            elif index == self.num_layers:
                # Last layer: hidden_dims[-1] -> num_classes
                self.params[f"W{index}"] = np.random.normal(0, weight_scale, (hidden_dims[index - 2], num_classes))
            else:
                # Intermediate layers: hidden_dims[index - 2] -> hidden_dims[index - 1]
                self.params[f"W{index}"] = np.random.normal(0, weight_scale, (hidden_dims[index - 2], hidden_dims[index - 1]))
            
            # Initialize biases
            if index == self.num_layers:
                # Last layer bias: num_classes
                self.params[f"b{index}"] = np.zeros((num_classes,))
            else:
                # Other layers bias: hidden_dims[index - 1]
                self.params[f"b{index}"] = np.zeros((hidden_dims[index - 1],))

        # When using dropout we need to pass a dropout_param dictionary to each
        # dropout layer so that the layer knows the dropout probability and the mode
        # (train / test). You can pass the same dropout_param to each dropout layer.
        self.dropout_param = {}
        if self.use_dropout:
            self.dropout_param = {'mode': 'train', 'p': dropout}
            if seed is not None:
                self.dropout_param['seed'] = seed

        # With batch normalization we need to keep track of running means and
        # variances, so we need to pass a special bn_param object to each batch
        # normalization layer. You should pass self.bn_params[0] to the forward pass
        # of the first batch normalization layer, self.bn_params[1] to the forward
        # pass of the second batch normalization layer, etc.
        self.bn_params = []
        if self.use_batchnorm:
            self.bn_params = [{'mode': 'train'} for i in range(self.num_layers - 1)]

        # Cast all parameters to the correct datatype
        for k, v in self.params.items():
            self.params[k] = v.astype(dtype)

    def loss(self, X, y=None):
        """
        Compute loss and gradient for the fully-connected net.
        Input / output: Same as TwoLayerNet above.
        """
        X = X.astype(self.dtype)
        mode = 'test' if y is None else 'train'

        # Set train/test mode for batchnorm params and dropout param since they
        # behave differently during training and testing.
        if self.dropout_param is not None:
            self.dropout_param['mode'] = mode
        if self.use_batchnorm:
            for bn_param in self.bn_params:
                bn_param[mode] = mode

        scores = None

        cache_list = []
        output = X  # Input to the first layer

        for index in range(1, self.num_layers + 1):
            if index != self.num_layers:
              # Hidden layers: affine -> ReLU
              output, cache = affine_relu_forward(output, self.params[f'W{index}'], self.params[f'b{index}'])
            else:
              # Output layer: affine (no ReLU)
              scores, cache = affine_forward(output, self.params[f'W{index}'], self.params[f'b{index}'])
            # Store the cache for backpropagation
            cache_list.append(cache)


        # If test mode return early
        if mode == 'test':
            return scores

        loss, grads = 0.0, {}

        # Compute softmax loss and gradient
        softmax, dout = softmax_loss(scores, y)
        # Compute regularization term
        regularization_norms = [np.linalg.norm(self.params[f'W{index}'], 'fro') ** 2
                        for index in range(1, self.num_layers + 1)]
        loss = softmax + 0.5 * self.reg * np.sum(regularization_norms)
        # Backpropagation
        for index in reversed(range(1, self.num_layers + 1)):  # Note the reversed() here
          if index == self.num_layers:
              # Output layer: affine backward pass
              dout, dW, db = affine_backward(dout, cache_list[index - 1])
          else:
              # Hidden layers: affine -> ReLU backward pass
              dout, dW, db = affine_relu_backward(dout, cache_list[index - 1])
          
          # Add regularization to the weight gradients
          grads[f'W{index}'] = dW + self.reg * self.params[f'W{index}']
          grads[f'b{index}'] = db
        return loss, grads
