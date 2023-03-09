import numpy as np

from morecantile import TileMatrixSet, tms
from affine import Affine

from rasterio import features


def project_geom(geom, t: TileMatrixSet = tms.get("WebMercatorQuad")):
    if geom["type"] == "Polygon":
        return {
            "type": geom["type"],
            "coordinates": [
                [t.xy(*coords) for coords in part]
                for part in geom["coordinates"]
            ],
        }
    elif geom["type"] == "LineString":
        return {
            "type": geom["type"],
            "coordinates": [t.xy(*coords) for coords in geom["coordinates"]],
        }
    elif geom["type"] == "Point":
        return {
            "type": geom["type"],
            "coordinates": t.xy(*geom["coordinates"]),
        }


def _feature_extrema(geometry):
    if geometry["type"] == "Polygon":
        x, y = zip(*[c for part in geometry["coordinates"] for c in part])
    elif geometry["type"] == "LineString":
        x, y = zip(*[c for c in geometry["coordinates"]])
    elif geometry["type"] == "Point":
        x, y = geometry["coordinates"]
        return x, y, x, y

    return min(x), min(y), max(x), max(y)


def find_extrema(features, t: TileMatrixSet = tms.get("WebMercatorQuad")):
    epsilon = 1.0e-10
    min_x, min_y, max_x, max_y = zip(
        *[_feature_extrema(f["geometry"]) for f in features]
    )
    bbox = t.bbox
    return (
        min(min_x) + epsilon,
        max(min(min_y) + epsilon, bbox.bottom),
        max(max_x) - epsilon,
        min(max(max_y) - epsilon, bbox.top),
    )


def tile_extrema(bounds, zoom, t: TileMatrixSet = tms.get("WebMercatorQuad")):
    minimumTile = t.tile(bounds[0], bounds[3], zoom)
    maximumTile = t.tile(bounds[2], bounds[1], zoom)

    return {
        "x": {"min": minimumTile.x, "max": maximumTile.x + 1},
        "y": {"min": minimumTile.y, "max": maximumTile.y + 1},
    }


def make_transform(tilerange, zoom, t: TileMatrixSet = tms.get("WebMercatorQuad")):
    ulx, uly = t.xy(
        *t.ul(tilerange["x"]["min"], tilerange["y"]["min"], zoom)
    )
    lrx, lry = t.xy(
        *t.ul(tilerange["x"]["max"], tilerange["y"]["max"], zoom)
    )
    xcell = (lrx - ulx) / float(tilerange["x"]["max"] - tilerange["x"]["min"])
    ycell = (uly - lry) / float(tilerange["y"]["max"] - tilerange["y"]["min"])
    return Affine(xcell, 0, ulx, 0, -ycell, uly)


def burn(polys, zoom, t: TileMatrixSet = tms.get("WebMercatorQuad")):
    bounds = find_extrema(polys, t=t)

    tilerange = tile_extrema(bounds, zoom, t=t)
    afftrans = make_transform(tilerange, zoom, t=t)

    burn = features.rasterize(
        ((project_geom(geom["geometry"]), 255) for geom in polys),
        out_shape=(
            (
                tilerange["y"]["max"] - tilerange["y"]["min"],
                tilerange["x"]["max"] - tilerange["x"]["min"],
            )
        ),
        transform=afftrans,
        all_touched=True,
    )

    xys = np.fliplr(np.dstack(np.where(burn))[0])

    xys[:, 0] += tilerange["x"]["min"]
    xys[:, 1] += tilerange["y"]["min"]

    return np.append(xys, np.zeros((xys.shape[0], 1), dtype=np.uint8) + zoom, axis=1)
