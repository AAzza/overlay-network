from __future__ import division

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
    if len(stats_block):
        first_value = sorted(stats_block.values())[0]
        values = []
        for key, value in stats_block.iteritems():
            value -= first_value
            # value = timedelta2int(value)
            values.append((key, value))
        return dict(values)


def process_stats(stats, to_normalize=None):
    to_normalize = to_normalize or []

    new_stats = {}
    for peer_id, peer_stats in stats.iteritems():
        for key, values in peer_stats.iteritems():
            new_stats.setdefault(key, {})[peer_id] = values
    return new_stats


def normalize(stats, to_normalize):
    new_stats = stats.copy()
    for stats_name in to_normalize:
        stats_block = new_stats[stats_name]
        for peer_id, values in stats_block.iteritems():
            stats_block[peer_id] = normalize_block(values)

    return new_stats


def calc_average(stats):
    total = 0
    count = 0
    for peer_stats in stats.itervalues():
        for value in peer_stats.itervalues():
            total += value
            count += 1
    return total / count


def save_stats_to_image(surface, stats):
    options = {
        'axis': {
            'x':{
                'showLines': True,
            },
            'y':{
                'showLines': True,
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
        surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, 1024, 768)
        save_stats_to_image(surface, stats_values)
        surface.write_to_png(os.path.join(outdir, '%s.png' % stat_name))
