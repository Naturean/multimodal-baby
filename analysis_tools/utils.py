from pathlib import Path
import functools
import numpy as np
import torch


def frac_format(m, n):
    return f'{m} / {n} = {m/n:.2%}'


def identity(x):
    return x


def get_n_rows(n_items, n_cols):
    return (n_items - 1) // n_cols + 1


def get_np_attrs_from_values(values, attr):
    return np.array([getattr(value, attr) for value in values])


def get_tsne_points_from_vectors(
        vectors,
        n_components=2,
        random_state=0,
        perplexity=50,
        learning_rate='auto',
        n_iter=1000,
        metric='cosine',
        **kwargs,
    ):
    from sklearn.manifold import TSNE

    tsne = TSNE(
        n_components=n_components,
        random_state=random_state,
        perplexity=perplexity,
        learning_rate=learning_rate,
        n_iter=n_iter,
        metric=metric,
        **kwargs,
    )
    points = tsne.fit_transform(vectors)
    print('T-SNE done.')
    return points

def get_eigen_points_from_vectors(vectors, print_singular_values=False, **kwargs):
    from scipy.linalg import svd

    U, s, Vh = svd(vectors, full_matrices=False, **kwargs)
    print('SVD done.')
    if print_singular_values:
        print('singular values:')
        print(s)
    return U

def convert_attr_for_each(objs, get_attr='mean_vector', set_attr='tsne_point', converter=get_tsne_points_from_vectors, **kwargs):
    attrs = get_np_attrs_from_values(objs, get_attr)

    new_attrs = converter(attrs, **kwargs)

    for obj, new_attr in zip(objs, new_attrs):
        setattr(obj, set_attr, new_attr)

get_tsne_points = functools.partial(convert_attr_for_each, set_attr='tsne_point', converter=get_tsne_points_from_vectors)
get_eigen_points = functools.partial(convert_attr_for_each, set_attr='eigen_point', converter=get_eigen_points_from_vectors)


def torch_cache(cache_path):
    cache_path = Path(cache_path)

    def decorator(fn):
        def wrapper(*args, **kwargs):
            if cache_path.exists():
                # load from cache
                print(f'load from {cache_path}')
                data = torch.load(cache_path)

            else:
                data = fn(*args, **kwargs)
                # save to cache
                torch.save(data, cache_path)

            return data

        return wrapper

    return decorator


def get_model_device(model):
    return next(model.parameters()).device


default_value_formatter = lambda value: f'{value:5.3f}'
prob_formatter = lambda prob: f'{prob:6.1%}'


def print_top_values(values, idx2word, labels=None, top_k=5, steps=None,
                     value_formatter=default_value_formatter):
    """Print the top k words in values (optionally along with the labels)
    Inputs:
        values: a torch.Tensor of shape [n_steps, vocab_size] or [vocab_size]
        idx2word: mapping word index to word
        labels: a torch.Tensor of shape [n_steps] or []
        top_k: the number of top words to print
        steps: list of int, steps to print; None for all possible steps
        value_formatter: value_formatter(value) should get the formatted string
            of the value
    """

    # unsqueeze singleton inputs
    if values.dim() == 1:
        values = values.unsqueeze(0)
        if labels is not None:
            labels = labels.unsqueeze(0)

    # init default values
    if labels is None:
        labels = [None] * len(values)
    if steps is None:
        steps = list(range(len(labels)))

    top_values, top_indices = values.topk(top_k, -1)

    zipped = list(zip(values, labels, top_values, top_indices))
    for step in steps:
        value, label, top_value, top_index = zipped[step]
        formatter = lambda value, idx: f'{value_formatter(value)} {idx2word[idx]:8}'
        line = (formatter(value[label.item()].item(), label.item()) + ' | ' if label is not None else '') \
             + ' '.join(formatter(value.item(), index.item()) for value, index in zip(top_value, top_index))
        print(line)
