""" Script to update state of staged instruments before running any experiment """

from qcore.helpers.stage import Stage
from qcore.helpers.server import Server
from qcore.instruments import *

# %% run this in a separate kernel to serve Instruments remotely
instruments_config = {LMS: ["25335"]}
server = Server(config=instruments_config)
server.serve()

# %% use this block to retrieve remote instruments and update their parameters
with Stage(remote=True) as remote_stage:
    lo_rr = remote_stage.get("LMS#25335")
    print(lo_rr.snapshot())
    lo_rr.frequency = 5e9
    lo_rr.power = 13
    print(lo_rr.snapshot())
