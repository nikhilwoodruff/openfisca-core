from openfisca_core.parameters import ParameterNode, IndexableParameterScale, IndexedParameterScaleAtInstant
from pathlib import Path

def test_indexed_scale_loaded():
    # Test that indexable parameter scales in the parameter folder are recognised and loaded
    parameter = ParameterNode("indexed_scale_hierarchy", Path(__file__).parents[1] / "parameter_validation" / "indexed_scale_hierarchy")
    assert isinstance(parameter.scale, IndexableParameterScale)


def test_indexable_scale_is_indexable():
    # Test that we can transform an IndexableParameterScale into an IndexedParameterScale and then index into it
    parameter = ParameterNode("indexed_scale_hierarchy", Path(__file__).parents[1] / "parameter_validation" / "indexed_scale_hierarchy")
    index = ["A", "B"]
    assert isinstance(parameter("2021-01-01").scale[index], IndexedParameterScaleAtInstant)
    x = parameter("2021-01-01").scale
    assert x.__dict__ == 1
    assert parameter("2021-01-01").scale[index].calc([5_000]) != 0

test_indexable_scale_is_indexable()