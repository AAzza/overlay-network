University project
====

This is my university project for computer networks.

The program performs simple simulation of mesh network, which consists of
the connected nodes. There is one *source node*, which generates info, and distribute
it over the whole network.

The distribution method is based on the *gossip*-based pull protocol. Each node
maintain information about neighbour's available packages and request the package it requires.

It is greenlet's based implementation. Each node works in separate greenlet,
and communicate with others using Channel. (Actually, each node is represented by three greenlets -
one for message dispatching, one for uploading info to other node and one for downloading).

To run the program:

    python overlay/main.py -n <number_of_nodes> --blocks <total number of packages> -g <algorighm>

By providing the *algorithm* you could select, which algorithm of package selection
node should use. There are 4 options:

- __random__ - node request random package from the available.
- __seq__ - sequential algorithm - node request all packages in order they are generated.
- __beta__ - node request random package, but with beta distribution (a=1, b=3),
            which corresponds to higher probabilities for packages with smaller numbers
            (and thus for generated earlier).
- __priority__ - packages are selected randomly, unless there are some packages
                for which the deadline of the receiving is close - in this case,
                they are selected first.
