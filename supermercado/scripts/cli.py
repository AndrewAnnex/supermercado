import click, json
import cligj
from morecantile import tms
from supermercado import edge_finder, uniontiles, burntiles, super_utils


@click.group("supermercado")
def cli():
    pass


@click.command("edges")
@click.argument("inputtiles", default="-", required=False)
@click.option("--parsenames", is_flag=True)
def edges(inputtiles, parsenames):
    """
    For a stream of [<x>, <y>, <z>] tiles, return only those tiles that are on the edge.
    """
    try:
        inputtiles = click.open_file(inputtiles).readlines()
    except IOError:
        inputtiles = [inputtiles]

    # parse the input stream into an array
    tiles = edge_finder.findedges(inputtiles, parsenames)

    for t in tiles:
        click.echo(t.tolist())


cli.add_command(edges)


@click.command("union")
@click.argument("inputtiles", default="-", required=False)
@click.option("--parsenames", is_flag=True)
@click.option("--tmsid", default="WebMercatorQuad", help="TileMatrixSet ID", show_default=True)
def union(inputtiles, parsenames, tmsid):
    """
    Returns the unioned shape of a stream of [<x>, <y>, <z>] tiles in GeoJSON.
    """
    tmss = tms.get(tmsid)
    try:
        inputtiles = click.open_file(inputtiles).readlines()
    except IOError:
        inputtiles = [inputtiles]
    unioned = uniontiles.union(inputtiles, parsenames, t=tmss)
    for u in unioned:
        click.echo(json.dumps(u))


cli.add_command(union)


@click.command("burn")
@cligj.features_in_arg
@cligj.sequence_opt
@click.argument("zoom", type=int)
@click.option("--tmsid", default="WebMercatorQuad", help="TileMatrixSet ID", show_default=True)
def burn(features, sequence, zoom, tmsid):
    """
    Burn a stream of GeoJSONs into a output stream of the tiles they intersect for a given zoom.
    """
    tmss = tms.get(tmsid) 
    features = [f for f in super_utils.filter_features(features)]

    tiles = burntiles.burn(features, zoom, t=tmss)
    for t in tiles:
        click.echo(t.tolist())


cli.add_command(burn)
