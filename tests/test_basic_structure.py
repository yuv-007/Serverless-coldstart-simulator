def test_project_modules_are_importable():
    import Controllers
    import Forecasting
    import RL
    import Simulator
    import Traffic

    assert Controllers is not None
    assert Forecasting is not None
    assert RL is not None
    assert Simulator is not None
    assert Traffic is not None
