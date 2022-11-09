def test_iem_scheduler_importable():
    # Test if BenderLibSIM can be imported
    from bender.sim import SIM

    import iem_scheduler  # noqa: F401

    dir(SIM)
