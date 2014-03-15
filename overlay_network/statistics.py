from __future__ import division

import json

import pycha
import pycha.line
import cairo
import os


def timedelta2int(timedelta):
    return (timedelta.seconds * 10 ** 6 + timedelta.microseconds) / 10 ** 6


def compare2first(stats):
    new_stats = {}
    for key, value in stats.iteritems():
        new_stats[key] = {}
        for inner_key, inner_value in value.iteritems():
            new_stats[key][inner_key] = inner_value - stats[0][inner_key]
    return new_stats


def normalize_block(stats_block):
    if not stats_block:
        return {}
    first_value = min(stats_block.values())
    values = {key: value - first_value for (key, value) in stats_block.items()}
    return values


def to_dict(stats):
    new_stats = {}
    for peer_id, peer_stats in stats.iteritems():
        for key, values in peer_stats.iteritems():
            new_stats.setdefault(key, {})[peer_id] = values
    return new_stats


def normalize(stats, keys):
    new_stats = stats.copy()
    for key in keys:
        stats_block = new_stats[key]
        for peer_id, values in stats_block.iteritems():
            stats_block[peer_id] = normalize_block(values)
    return new_stats


def average(stats):
    """ Compute the average of all values for the next structure:
        {peer1: {block1: value11, block2: value2}, peer2: {...}, ...}
    """
    total = 0
    count = 0
    for peer_stats in stats.itervalues():
        total += sum(peer_stats.itervalues())
        count += len(peer_stats)
    return total / count


def save_stats_to_image(surface, stats):
    options = {
        'axis': {
            'labelFontSize': 12,
            'x':{
                'showLines': True,
            },
            'y':{
                'showLines': True,
                'range': [0, 100],
            }
        },
        'background': {
            'color': '#eeeeff',
            'lineColor':'#444444'
        },
        #'fillOpacity':'0.0',
        'shouldFill' : False,
        'colorScheme': {
            'name': 'rainbow',
            'args': {
                'initialColor': 'blue',
            },
        }
    }
    chart  = pycha.line.LineChart(surface, options)
    # import ipdb; ipdb.set_trace()
    for peer_id, peer_stats in stats.items():
        if not isinstance(peer_stats, dict):
            continue
        dataset = ((str(peer_id), peer_stats.items()), )
        chart.addDataset(dataset)
    chart.render()


def save_stats(stats, outdir='out'):
    for stat_name, stats_values in stats.iteritems():
        with open(os.path.join(outdir, '%s.json' % stat_name), 'w') as out:
            json.dump(stats_values, out, sort_keys=True)
        surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, 800, 600)
        save_stats_to_image(surface, stats_values)
        surface.write_to_png(os.path.join(outdir, '%s.png' % stat_name))
