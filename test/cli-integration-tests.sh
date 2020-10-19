#!/usr/bin/env sh

# Tests to try all splits
# Categorical multi
dtcontrol -i examples/prism/firewire_abst.prism --use-preset avg --rerun

# Categorical single
dtcontrol -i examples/prism/firewire_abst.prism --use-preset singlesplit --rerun

# Axis-aligned
dtcontrol -i examples/cartpole.scs --use-preset mlentropy --rerun

# Linear and multi-dim label
dtcontrol -i examples/10rooms.scs --use-preset maxfreqlc --rerun