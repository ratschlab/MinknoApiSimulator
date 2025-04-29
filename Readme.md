## Getting Started


```bash
git clone https://github.com/ratschlab/MinknoApiSimulator.git
cd MinknoApiSimulator/certs
./generate.sh
cd ..
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Run the server and the client
source .env.sh
python src/server.py --input <input file or directory> &
python src/client.py
```


## TODO
- [ ] Logging
- [ ] Graceful exit
- [x] Remove version hardcoding from manager and instance services (currently hardcoded to "6.0.0")
- [x] Remove hardcoded flowcell name from manager service (currently hardcoded to "MN12345")
- [x] Remove hardcoded run_id from protocol (currently hardcoded to "test_run")
- [x] Fix acquisition progress