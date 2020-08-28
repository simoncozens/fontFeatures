from beziers.path import BezierPath
from beziers.line import Line
from beziers.point import Point


def get_bezier_paths(font, glyphname):
    return BezierPath.fromFonttoolsGlyph(font, glyphname)


def find_largest_path(font, glyphname):
    paths = get_bezier_paths(font, glyphname)
    return max(paths, key=lambda p: p.area)


def thickness_at_x(path, x):
    bounds = path.bounds()
    bounds.addMargin(10)
    ray = Line(Point(x - 0.1, bounds.bottom), Point(x + 0.1, bounds.top))
    intersections = []
    for seg in path.asSegments():
        intersections.extend(seg.intersections(ray))
    if len(intersections) < 2:
        return None
    intersections = list(sorted(intersections, key=lambda i: i.point.y))
    i1, i2 = intersections[0:2]
    inorm1 = i1.seg1.normalAtTime(i1.t1)
    ray1 = Line(i1.point + (inorm1 * 1000), i1.point + (inorm1 * -1000))
    iii = i2.seg1.intersections(ray1)
    if iii:
        ll1 = i1.point.distanceFrom(iii[0].point)
    else:
        # Simple, vertical version
        return abs(i1.point.y - i2.point.y)

    inorm2 = i2.seg1.normalAtTime(i2.t1)
    ray2 = Line(i2.point + (inorm2 * 1000), i2.point + (inorm2 * -1000))
    iii = i1.seg1.intersections(ray2)
    if iii:
        ll2 = i2.point.distanceFrom(iii[0].point)
        return (ll1 + ll2) * 0.5
    else:
        return ll1

    # midpoint = (i1.point + i2.point) / 2
    # # Find closest path to midpoint
    # # Find the tangent at that time
    # inorm2 = i2.seg1.normalAtTime(i2.t1)


# from fontTools.ttLib import TTFont

# font = TTFont("fonts/Amiri-Regular.ttf")
# p = find_largest_path(font, "aHaa.medi")
# print(thickness_at_x(p, 128))
