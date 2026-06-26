import random
from unittest.mock import patch
from src.effects import EffectEngine


def test_select_effects_linear_order():
    """Test that EffectEngine.select_effects preserves linear order when order='linear'."""
    configs = [
        {"name": "invert", "chance": 100, "strength_range": (1.0, 1.0)},
        {"name": "blur", "chance": 100, "strength_range": (2.0, 2.0)},
        {"name": "zoomin", "chance": 100, "strength_range": (3.0, 3.0)},
    ]

    selected = EffectEngine.select_effects(configs, order="linear")
    names = [fx["name"] for fx in selected]
    assert names == ["invert", "blur", "zoomin"]


@patch("random.random", return_value=0.0)
def test_select_effects_linear_order_mixed(mock_random):
    """Test that EffectEngine.select_effects preserves linear order with mixed guaranteed and probabilistic effects when order='linear'."""
    configs = [
        {"name": "invert", "chance": 50, "strength_range": (1.0, 1.0)},
        {"name": "blur", "chance": 100, "strength_range": (2.0, 2.0)},
        {"name": "zoomin", "chance": 50, "strength_range": (3.0, 3.0)},
    ]

    selected = EffectEngine.select_effects(configs, order="linear")
    names = [fx["name"] for fx in selected]
    assert names == ["invert", "blur", "zoomin"]


def test_select_effects_random_order():
    """Test that EffectEngine.select_effects randomizes the order when order='random'."""
    configs = [
        {"name": "invert", "chance": 100, "strength_range": (1.0, 1.0)},
        {"name": "blur", "chance": 100, "strength_range": (2.0, 2.0)},
        {"name": "zoomin", "chance": 100, "strength_range": (3.0, 3.0)},
        {"name": "mirror", "chance": 100, "strength_range": (4.0, 4.0)},
        {"name": "speed", "chance": 100, "strength_range": (5.0, 5.0)},
    ]

    # Run up to 50 times with different seeds to ensure we get a shuffled order
    different_order_found = False
    state = random.getstate()
    try:
        for seed in range(50):
            random.seed(seed)
            selected = EffectEngine.select_effects(configs, order="random")
            names = [fx["name"] for fx in selected]
            if names != ["invert", "blur", "zoomin", "mirror", "speed"]:
                different_order_found = True
                break
    finally:
        random.setstate(state)

    assert different_order_found, (
        "Random order should return a shuffled list of effects"
    )
