from micrographonia.runtime.artifacts import RunArtifacts

def test_read_run_info(tmp_path):
    ra = RunArtifacts(tmp_path, run_id="abcd1234")
    info = {"inputs_hash": "i", "registry_hash": "r", "created_at": "now"}
    ra.write_run_info(info)
    ra2 = RunArtifacts(tmp_path, run_id="abcd1234")
    assert ra2.read_run_info() == info
