# TD MVP Host

This backend-agnostic placeholder records the host responsibilities for the TD MVP.

The concrete first implementation target is:

```text
zk_backend/td_mvp/sp1/host/
```

A future host should load the TD MVP test vector, prepare backend inputs, invoke proving, verify the proof, and record proof metrics. The host should not enforce the TD relation itself; that belongs in the guest.
