import copy
import os
import typing

import numpy as np

from openfisca_core import commons, parameters, periods, tools
from openfisca_core.errors import ParameterParsingError
from openfisca_core.parameters import config, helpers, AtInstantLike
from openfisca_core.taxscales import (
    LinearAverageRateTaxScale,
    MarginalAmountTaxScale,
    MarginalRateTaxScale,
    SingleAmountTaxScale,
    )


class ParameterScale(AtInstantLike):
    """
    A parameter scale (for instance a  marginal scale).
    """

    # 'unit' and 'reference' are only listed here for backward compatibility
    _allowed_keys = config.COMMON_KEYS.union({'brackets'})

    def __init__(self, name, data, file_path):
        """
        :param name: name of the scale, eg "taxes.some_scale"
        :param data: Data loaded from a YAML file. In case of a reform, the data can also be created dynamically.
        :param file_path: File the parameter was loaded from.
        """
        self.name: str = name
        self.file_path: str = file_path
        helpers._validate_parameter(self, data, data_type = dict, allowed_keys = self._allowed_keys)
        self.description: str = data.get('description')
        self.metadata: typing.Dict = {}
        helpers._set_backward_compatibility_metadata(self, data)
        self.metadata.update(data.get('metadata', {}))

        if not isinstance(data.get('brackets', []), list):
            raise ParameterParsingError(
                "Property 'brackets' of scale '{}' must be of type array."
                .format(self.name),
                self.file_path
                )

        brackets = []
        for i, bracket_data in enumerate(data.get('brackets', [])):
            bracket_name = helpers._compose_name(name, item_name = i)
            bracket = parameters.ParameterScaleBracket(name = bracket_name, data = bracket_data, file_path = file_path)
            brackets.append(bracket)
        self.brackets: typing.List[parameters.ParameterScaleBracket] = brackets

    def __getitem__(self, key):
        if isinstance(key, int) and key < len(self.brackets):
            return self.brackets[key]
        else:
            raise KeyError(key)

    def __repr__(self):
        return os.linesep.join(
            ['brackets:']
            + [tools.indent('-' + tools.indent(repr(bracket))[1:]) for bracket in self.brackets]
            )

    def get_descendants(self):
        return iter(())

    def clone(self):
        clone = commons.empty_clone(self)
        clone.__dict__ = self.__dict__.copy()

        clone.brackets = [bracket.clone() for bracket in self.brackets]
        clone.metadata = copy.deepcopy(self.metadata)

        return clone

    def _get_at_instant(self, instant):
        brackets = [bracket.get_at_instant(instant) for bracket in self.brackets]

        if self.metadata.get('type') == 'single_amount':
            scale = SingleAmountTaxScale()
            for bracket in brackets:
                if 'amount' in bracket._children and 'threshold' in bracket._children:
                    amount = bracket.amount
                    threshold = bracket.threshold
                    scale.add_bracket(threshold, amount)
            return scale
        elif any('amount' in bracket._children for bracket in brackets):
            scale = MarginalAmountTaxScale()
            for bracket in brackets:
                if 'amount' in bracket._children and 'threshold' in bracket._children:
                    amount = bracket.amount
                    threshold = bracket.threshold
                    scale.add_bracket(threshold, amount)
            return scale
        elif any('average_rate' in bracket._children for bracket in brackets):
            scale = LinearAverageRateTaxScale()

            for bracket in brackets:
                if 'base' in bracket._children:
                    base = bracket.base
                else:
                    base = 1.
                if 'average_rate' in bracket._children and 'threshold' in bracket._children:
                    average_rate = bracket.average_rate
                    threshold = bracket.threshold
                    scale.add_bracket(threshold, average_rate * base)
            return scale
        else:
            scale = MarginalRateTaxScale()

            for bracket in brackets:
                if 'base' in bracket._children:
                    base = bracket.base
                else:
                    base = 1.
                if 'rate' in bracket._children and 'threshold' in bracket._children:
                    rate = bracket.rate
                    threshold = bracket.threshold
                    scale.add_bracket(threshold, rate * base)
            return scale


class IndexableParameterScale(ParameterScale):
    def _bracket_is_indexed(self, bracket):
        return isinstance(bracket, parameters.ParameterNode)

    def _get_indexable_values(self):
        indices_found = []
        for bracket in self.brackets:
            for key in ("rate", "amount", "threshold"):
                if hasattr(bracket, key):
                    # Determine if the bracket variable is indexed or has time-period children
                    if self._bracket_is_indexed(getattr(bracket, key)):
                        indices_found += list(getattr(bracket, key).children.keys())
        return indices_found

    def _get_indexed_copy(self, index):
        scale = ParameterScale.__new__(ParameterScale)
        for key in super()._allowed_keys:
            if hasattr(self, key):
                setattr(scale, key, getattr(self, key))
        for bracket in self.brackets:
            for key in ("rate", "amount", "threshold"):
                if hasattr(bracket, key):
                    if self._bracket_is_indexed(getattr(bracket, key)):
                        setattr(bracket, key, getattr(getattr(bracket, key), index))
                        del bracket.children[key][index]
        return scale

    def _get_at_instant(self, instant):
        indexable_values = self._get_indexable_values()
        indexed_scales = {
            value: self._get_indexed_copy(value) for value in indexable_values
        }
        scales_at_instant = {value: scale._get_at_instant(instant) for value, scale in indexed_scales.items()}
        return IndexableParameterScaleAtInstant(scales_at_instant)


class IndexableParameterScaleAtInstant:
    allowed_keys = ("value_to_scale",)

    def __init__(self, value_to_scale: dict = None):
        self.value_to_scale = value_to_scale

    def __getitem__(self, key):
        return IndexedParameterScaleAtInstant(self.value_to_scale, key)

class IndexedParameterScaleAtInstant:
    allowed_keys = ("value_to_scale", "index")

    def __init__(self, value_to_scale: dict = None, index = None):
        self.value_to_scale = value_to_scale
        self.index = index
    
    def calc(self, tax_base):
        # Produce a (num_entities x num_categories) array of values
        result_by_index = np.array([scale.calc(tax_base) for scale in self.value_to_scale.values()])
        return result_by_index
