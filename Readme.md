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
python src/server.py &
python src/client.py
```


## TODO
- [ ] Remove version hardcoding from manager and instance services (currently hardcoded to "6.0.0")
- [ ] Remove hardcoded flowcell name from manager service (currently hardcoded to "MN12345")
- [ ] Remove hardcoded run_id from protocol (currently hardcoded to "test_run")
- [ ] Fix acquisition progress