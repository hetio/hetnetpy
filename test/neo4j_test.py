import pathlib
import textwrap

import pytest
from neo4j import GraphDatabase

import hetnetpy.neo4j
import hetnetpy.readwrite


def test_construct_pdp_query():
    """
    Test the pdp computation on the metapath from https://doi.org/10.1371/journal.pcbi.1004259.g002
    """

    # Since we're working on a known nicotine dependency - Bupropion metapath,
    # we already know the dwpc
    dwpc = 0.03287590886921623

    # Set up the graph for querying

    directory = pathlib.Path(__file__).parent.absolute()
    path = directory.joinpath("data/hetionet-v1.0-metagraph.json")

    metagraph = hetnetpy.readwrite.read_metagraph(path)

    compound = "DB01156"  # Bupropion
    disease = "DOID:0050742"  # nicotine dependency
    damping_exponent = 0.4

    metapath = metagraph.metapath_from_abbrev("CbGpPWpGaD")

    # Calculate the pdp without being provided with the dwpc
    pdp_query = hetnetpy.neo4j.construct_pdp_query(
        metapath, path_style="string", property="identifier", unique_nodes=True
    )

    assert len(pdp_query) > 0
    driver = GraphDatabase.driver("bolt://neo4j.het.io")

    params = {"source": compound, "target": disease, "w": damping_exponent}
    with driver.session() as session:
        results = session.run(pdp_query, params)
        results = results.data()

    # Note that these are en dashes not hyphens
    assert results[0]["path"].split("–")[0] == "Bupropion"
    assert results[0]["path"].split("–")[-1] == "nicotine dependence"

    percent_dwpc_1 = results[0]["percent_of_DWPC"]

    old_pdp_query = pdp_query

    # Calculate the pdp with the provided dwpc
    pdp_query = hetnetpy.neo4j.construct_pdp_query(
        metapath, dwpc, path_style="list", property="identifier", unique_nodes=True
    )

    assert len(pdp_query) > 0
    assert old_pdp_query != pdp_query

    with driver.session() as session:
        results = session.run(pdp_query, params)
        results = results.data()

    assert results[0]["path"][0] == "Bupropion"
    assert results[0]["path"][-1] == "nicotine dependence"

    # We'll check this because it verifies both that the DWPC and the PDP for the path
    # are the same for both queries
    assert percent_dwpc_1 == pytest.approx(results[0]["percent_of_DWPC"])

    sum_percent = 0
    for result in results:
        sum_percent += result["percent_of_DWPC"]

    # The fractions should all add up to around 100 percent
    assert sum_percent == pytest.approx(100)


def test_construct_pdp_query_return_values():
    """
    Test that the construct_pdp_query function returns the expected query for a
    known graph. These tests will not actually execute the query
    """
    q1 = textwrap.dedent(
        """\
            MATCH path = (n0:Compound)-[:BINDS_CbG]-(n1)-[:PARTICIPATES_GpPW]-(n2)-[:PARTICIPATES_GpPW]-(n3)-[:ASSOCIATES_DaG]-(n4:Disease)
            USING JOIN ON n2
            WHERE n0.identifier = { source }
            AND n4.identifier = { target }
            AND n1 <> n3
            WITH
            [
            size((n0)-[:BINDS_CbG]-()),
            size(()-[:BINDS_CbG]-(n1)),
            size((n1)-[:PARTICIPATES_GpPW]-()),
            size(()-[:PARTICIPATES_GpPW]-(n2)),
            size((n2)-[:PARTICIPATES_GpPW]-()),
            size(()-[:PARTICIPATES_GpPW]-(n3)),
            size((n3)-[:ASSOCIATES_DaG]-()),
            size(()-[:ASSOCIATES_DaG]-(n4))
            ] AS degrees, path
            WITH path, reduce(pdp = 1.0, d in degrees| pdp * d ^ -{ w }) AS PDP
            WITH collect({paths: path, PDPs: PDP}) AS data_maps, count(path) AS PC, sum(PDP) AS DWPC
            UNWIND data_maps AS data_map
            WITH data_map.paths AS path, data_map.PDPs AS PDP, PC, DWPC
            RETURN
              substring(reduce(s = '', node IN nodes(path)| s + '–' + node.name), 1) AS path,
              PDP,
              100 * (PDP / DWPC) AS percent_of_DWPC
            ORDER BY percent_of_DWPC DESC
            """
    ).rstrip()

    dwpc = 0.03287590886921623
    q2 = textwrap.dedent(
        """\
            MATCH path = (n0:Compound)-[:BINDS_CbG]-(n1)-[:PARTICIPATES_GpPW]-(n2)-[:PARTICIPATES_GpPW]-(n3)-[:ASSOCIATES_DaG]-(n4:Disease)
            USING JOIN ON n2
            WHERE n0.identifier = { source }
            AND n4.identifier = { target }
            AND n1 <> n3
            WITH
            [
            size((n0)-[:BINDS_CbG]-()),
            size(()-[:BINDS_CbG]-(n1)),
            size((n1)-[:PARTICIPATES_GpPW]-()),
            size(()-[:PARTICIPATES_GpPW]-(n2)),
            size((n2)-[:PARTICIPATES_GpPW]-()),
            size(()-[:PARTICIPATES_GpPW]-(n3)),
            size((n3)-[:ASSOCIATES_DaG]-()),
            size(()-[:ASSOCIATES_DaG]-(n4))
            ] AS degrees, path
            WITH path, reduce(pdp = 1.0, d in degrees| pdp * d ^ -{ w }) AS PDP
            RETURN
            substring(reduce(s = '', node IN nodes(path)| s + '–' + node.name), 1) AS path,
            PDP,
            100 * (PDP / 0.03287590886921623) AS percent_of_DWPC
            ORDER BY percent_of_DWPC DESC
            """
    ).rstrip()

    # Set up the graph for querying
    directory = pathlib.Path(__file__).parent.absolute()
    path = directory.joinpath("data/hetionet-v1.0-metagraph.json")
    metagraph = hetnetpy.readwrite.read_metagraph(path)

    metapath = metagraph.metapath_from_abbrev("CbGpPWpGaD")
    DWPCless_query = hetnetpy.neo4j.construct_pdp_query(
        metapath, path_style="string", property="identifier", unique_nodes=True
    )

    assert DWPCless_query == q1

    DWPC_query = hetnetpy.neo4j.construct_pdp_query(
        metapath, dwpc, path_style="string", property="identifier", unique_nodes=True
    )

    assert DWPC_query == q2


def test_construct_dwpc_query():
    """
    Test dwpc query construction and computation on the metapath from
    https://doi.org/10.1371/journal.pcbi.1004259.g002
    """

    directory = pathlib.Path(__file__).parent.absolute()
    path = directory.joinpath("data/hetionet-v1.0-metagraph.json")

    metagraph = hetnetpy.readwrite.read_metagraph(path)

    compound = "DB01156"  # Bupropion
    disease = "DOID:0050742"  # nicotine dependency
    damping_exponent = 0.4

    metapath = metagraph.metapath_from_abbrev("CbGpPWpGaD")

    query = hetnetpy.neo4j.construct_dwpc_query(
        metapath, property="identifier", unique_nodes=True
    )
    assert len(query) > 0
    driver = GraphDatabase.driver("bolt://neo4j.het.io")

    params = {"source": compound, "target": disease, "w": damping_exponent}
    with driver.session() as session:
        results = session.run(query, params)
        results = results.single()
        assert results

    dwpc = results["DWPC"]

    assert dwpc == pytest.approx(0.03287590886921623)


@pytest.mark.parametrize(
    "style, identifier, expected_output",
    [
        ("list", "name", "[node in nodes(path) | node.name] AS path,"),
        ("list", "identifier", "[node in nodes(path) | node.identifier] AS path,"),
        (
            "string",
            "name",
            "substring(reduce(s = '', node IN nodes(path)| s + '–' + node.name), 1) AS path,",
        ),
        (
            "string",
            "identifier",
            "substring(reduce(s = '', node IN nodes(path)| s + '–' + node.identifier), 1) AS path,",
        ),
        (
            "id_lists",
            None,
            "[node IN nodes(path) | id(node)] AS node_ids,\n[rel IN relationships(path) | id(rel)] AS rel_ids,",
        ),
    ],
)
def test_construct_path_return_clause_returns(style, identifier, expected_output):
    """
    Test the results of construct_path_return_clause with different parameters
    """
    assert (
        hetnetpy.neo4j.create_path_return_clause(style, identifier) == expected_output
    )


def test_construct_path_return_clause_error():
    """
    Ensure that construct_path_return_clause throwns a ValueError when given an invalid style
    """
    with pytest.raises(ValueError):
        hetnetpy.neo4j.create_path_return_clause("invalid_style")
