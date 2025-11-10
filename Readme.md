## Getting Started


```bash
git clone https://github.com/ratschlab/MinknoApiSimulator.git
cd MinknoApiSimulator/certs
./generate.sh
cd ..

# create or activate virtual env if required and then..
pip install .

# Run the server and the client
mksimserver --input <input file or directory> --input <input file or directory> &
mksimclient
```

Run `mksimserver --help` for options.


## TODO
- [ ] Logging
- [x] Graceful exit
- [x] Remove version hardcoding from manager and instance services (currently hardcoded to "6.0.0")
- [x] Remove hardcoded flowcell name from manager service (currently hardcoded to "MN12345")
- [x] Remove hardcoded run_id from protocol (currently hardcoded to "test_run")
- [x] Fix acquisition progress
- [ ] Optional certs directory for pip install