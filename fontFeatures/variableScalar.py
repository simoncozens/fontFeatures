"""Tools for representing variable layout."""

from fontTools.varLib.models import VariationModel, normalizeValue

class NormalizedLocation(dict):
    """A location in normalized space (values between -1 and 1)"""
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

    def __repr__(self):
        items = []
        for location,value in self.values.items():
            loc = ",".join(["%s=%i" % (ax,loc) for ax,loc in location.items()])
            items.append("%s:%i" % (loc, value))
        return "("+(" ".join(items))+")"

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
        """Defines a value at a location.

        Args:
            location (dict): A dictionary mapping axis tags to locations.
            value (float): The value of the scalar at this master location."""
        self.values[self._normalized_location(location)] = value

    @property
    def default(self):
        """Returns the default value.

        Returns a float representing the value of this scalar at the default
        location on all axes."""
        key = NormalizedLocation({ax.tag: 0 for ax in self.axes})
        if key not in self.values:
            raise ValueError("Default value could not be found")
            # I *guess* we could interpolate one, but I don't know how.
        return self.values[key]

    def value_at_location(self, location):
        """Returns the value at a given location, interpolating if necessary.

        Args:
            location (dict): A dictionary mapping axis tags to locations.

        Returns a float with the value interpolated at the given location.
        """
        loc = self._normalized_location(location)
        if loc in self.values:
            return self.values[loc]
        values = list(self.values.values())
        return self.model.interpolateFromMasters(loc, values)

    @property
    def model(self):
        """Returns a :py:class:`fontTools.varLib.models.VariationModel` object
        used for interpolating values in this variation space."""
        locations = list(self.values.keys())
        return VariationModel(locations)

    def get_deltas_and_supports(self):
        """Get a list of deltas and supports used when interpolating.

        See the fontTools.varLib documentation to understand this."""
        values = list(self.values.values())
        return self.model.getDeltasAndSupports(values)

    def add_to_variation_store(self, store_builder):
        """Add this variable scalar to a variation store.

        Args:
            store_builder: A :py:class:`fontTools.varLib.varStore.OnlineStoreBuilder` object.

        Returns a two element tuple. The first element is the default value, which
        normally goes in the GPOS table directly; the second is the index of this
        item in the variation store, which normally goes into the Device element
        of the value record."""
        deltas, supports = self.get_deltas_and_supports()
        store_builder.setSupports(supports)
        index = store_builder.storeDeltas(deltas)
        return int(self.default), index
