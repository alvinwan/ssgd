"""Memory-Limited Machine Learning Command-Line Utility

This utility allows you try several algorithms on popular datasets, to compare
with memory-limited equivalents.

Usage:
    mlml.py closed --n=<n> --d=<d> --train=<train> --test=<test> --nt=<nt> [options]
    mlml.py gd --n=<n> --d=<d> --train=<train> --test=<test> --nt=<nt> [options]
    mlml.py sgd --n=<n> --d=<d> --train=<train> --test=<test> --nt=<nt> [options]
    mlml.py ssgd --n=<n> --d=<d> --buffer=<buffer> --train=<train> --test=<test> --nt=<nt> [options]
    mlml.py hsgd --n=<n> --d=<d> --buffer=<buffer> --train=<train> --test=<test> --nt=<nt> [options]
    mlml.py (closed|gd|sgd|ssgd) (mnist|spam|cifar-10) [options]

Options:
    --algo=<algo>       Shuffling algorithm to use [default: external_shuffle]
    --buffer=<num>      Size of memory in megabytes (MB) [default: 10]
    --d=<d>             Number of features
    --damp=<damp>       Amount to multiply learning rate by per epoch [default: 0.99]
    --dtype=<dtype>     The numeric type of each sample [default: float64]
    --epochs=<epochs>   Number of passes over the training data [default: 3]
    --eta0=<eta0>       The initial learning rate [default: 1e-6]
    --iters=<iters>     The number of iterations, used for gd and sgd [default: 5000]
    --logfreq=<freq>    Number of iterations between log entries. 0 for no log. [default: 1000]
    --momentum=<mom>    Momentum to apply to changes in weight [default: 0.9]
    --n=<n>             Number of training samples
    --k=<k>             Number of classes [default: 10]
    --nt=<nt>           Number of testing samples
    --one-hot=<onehot>  Whether or not to use one hot encoding [default: False]
    --nthreads=<nthr>   Number of threads [default: 1]
    --reg=<reg>         Regularization constant [default: 0.1]
    --step=<step>       Number of iterations between each alpha decay [default: 10000]
    --train=<train>     Path to training data binary [default: data/train]
    --test=<test>       Path to test data [default: data/test]
    --simulated         Mark memory constraints as simulated. Allows full accuracy tests.
"""

import docopt

from mlml.algorithm import ClosedForm
from mlml.algorithm import GD
from mlml.algorithm import SGD
from mlml.algorithm import SSGD
from mlml.utils.data import de_one_hot
from mlml.ssgd.blocks import bytes_per_dtype
from mlml.utils.data import read_dataset


def main() -> None:
    """Load data and launch training, then evaluate accuracy."""
    arguments = preprocess_arguments(docopt.docopt(__doc__, version='MLML 1.0'))

    test = read_dataset(
        data_hook=arguments['--data-hook'],
        dtype=arguments['--dtype'],
        num_classes=arguments['--k'],
        one_hot=arguments['--one-hot'],
        path=arguments['--test'],
        shape=(arguments['--nt'], arguments['--d']))
    if arguments['closed']:
        X, Y, model = ClosedForm.from_arguments(arguments, test.X, test.labels)
    elif arguments['gd']:
        X, Y, model = GD.from_arguments(arguments, test.X, test.labels)
    elif arguments['sgd']:
        X, Y, model = SGD.from_arguments(arguments, test.X, test.labels)
    elif arguments['ssgd']:
        X, Y, model = SSGD.from_arguments(arguments, test.X, test.labels)
    elif arguments['hsgd']:
        raise NotImplementedError
    else:
        raise UserWarning('Invalid algorithm specified.')
    labels = de_one_hot(Y)
    train_accuracy = model.accuracy(X, labels)
    test_accuracy = model.accuracy(test.X, test.labels)
    print('Train:', train_accuracy, 'Test:', test_accuracy)


def preprocess_arguments(arguments) -> dict:
    """Preprocessing arguments dictionary by cleaning numeric values.

    Args:
        arguments: The dictionary of command-line arguments
    """

    if arguments['mnist']:
        arguments['--dtype'] = 'uint8'
        arguments['--train'] = 'data/mnist-%s-60000-train' % arguments['--dtype']
        arguments['--test'] = 'data/mnist-%s-10000-test' % arguments['--dtype']
        arguments['--n'] = 60000
        arguments['--nt'] = 10000
        arguments['--k'] = 10
        arguments['--d'] = 784
        arguments['--one-hot'] = 'true'
        arguments['--data-hook'] = lambda X, Y: (X / 255.0, Y)
    if arguments['spam']:
        arguments['--train'] = 'data/spam-%s-2760-train' % arguments['--dtype']
        arguments['--test'] = 'data/spam-%s-690-test' % arguments['--dtype']
        arguments['--n'] = 2760
        arguments['--nt'] = 690
        arguments['--k'] = 1
        arguments['--d'] = 55
    if arguments['cifar-10']:
        arguments['--dtype'] = 'uint8'
        arguments['--train'] = 'data/cifar-10-%s-50000-train' % arguments['--dtype']
        arguments['--test'] = 'data/cifar-10-%s-10000-test' % arguments['--dtype']
        arguments['--n'] = 50000
        arguments['--nt'] = 10000
        arguments['--k'] = 10
        arguments['--d'] = 3072
        arguments['--one-hot'] = 'true'

    arguments['--damp'] = float(arguments['--damp'])
    arguments['--data-hook'] = arguments.get('--data-hook', lambda *args: args)
    arguments['--epochs'] = int(arguments['--epochs'])
    arguments['--eta0'] = float(arguments['--eta0'])
    arguments['--iters'] = int(arguments['--iters'])
    arguments['--logfreq'] = int(arguments['--logfreq'])
    arguments['--momentum'] = float(arguments['--momentum'])
    arguments['--n'] = int(arguments['--n'])
    arguments['--nthreads'] = int(arguments['--nthreads'])
    arguments['--d'] = int(arguments['--d'])
    arguments['--k'] = int(arguments['--k'])
    arguments['--one-hot'] = arguments['--one-hot'].lower() == 'true'
    arguments['--reg'] = float(arguments['--reg'])
    arguments['--step'] = int(arguments['--step'])

    bytes_total = float(arguments['--buffer']) * (10 ** 6)
    bytes_per_sample = (arguments['--d'] + 1) * bytes_per_dtype(arguments['--dtype'])
    arguments['--num-per-block'] = min(
        int(bytes_total // bytes_per_sample),
        arguments['--n'])
    return arguments


if __name__ == '__main__':
    main()
