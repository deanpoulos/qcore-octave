""" Script to update state of staged instruments before running any experiment """

from qcore.helpers.stage import Stage

with Stage(remote=True) as remote_stage:
    lo_rr = remote_stage.get("LO_RR")
    lo_rr.frequency = 5e9
    lo_rr.power = 13
