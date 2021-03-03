from fontTools.varLib.models import VariationModel, normalizeValue


class NormalizedLocation(dict):
    def __hash__(self):
        return hash(frozenset(self))


class VariableScalar:
    """A scalar with different values at different points in the designspace."""

    def __init__(self, axes, location_value={}):
        self.axes = axes
        self.axes_dict = {ax.tag: ax for ax in self.axes}
        self.values = {}
        for location, value in location_value.items():
            self.add_value(location, value)

    def _normalized_location(self, location):
        normalized_location = {}
        for axtag in location.keys():
            if axtag not in self.axes_dict:
                raise ValueError("Unknown axis %s in %s" % axtag, location)
            axis = self.axes_dict[axtag]
            normalized_location[axtag] = normalizeValue(
                location[axtag], (axis.minimum, axis.default, axis.maximum)
            )

        for ax in self.axes:
            if ax.tag not in normalized_location:
                normalized_location[ax.tag] = 0

        return NormalizedLocation(normalized_location)

    def add_value(self, location, value):
        self.values[self._normalized_location(location)] = value

    @property
    def default(self):
        key = NormalizedLocation({ax.tag: 0 for ax in self.axes})
        if key not in self.values:
            raise ValueError("Default value could not be found")
            # I *guess* we could interpolate one, but I don't know how.
        return self.values[key]

    def value_at_location(self, location):
        loc = self._normalized_location(location)
        if loc in self.values:
            return self.values[loc]
        values = list(self.values.values())
        return self.model.interpolateFromMasters(loc, values)

    @property
    def model(self):
        locations = list(self.values.keys())
        return VariationModel(locations)

    def get_deltas_and_supports(self):
        values = list(self.values.values())
        return self.model.getDeltasAndSupports(values)

    def add_to_variation_store(self, store_builder):
        deltas, supports = self.get_deltas_and_supports()
        store_builder.setSupports(supports)
        index = store_builder.storeDeltas(deltas)
        return self.default, index
