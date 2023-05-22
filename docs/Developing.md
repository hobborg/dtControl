
The following are
```bash
# Clone the repo 
git clone git@gitlab.com:live-lab/software/dtcontrol.git
cd dtcontrol
# Initialize and update the examples submodule
# (this would work if you have cloned it using ssh, i.e., not HTTPS)
git submodule update --init examples

# Install the python dependencies
pip install -r docs/requirements.txt
# Run dtControl
./bin/dtcontrol
```

## ToDos
- Add an example command
- Command to execute the web interface

