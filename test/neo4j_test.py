from neo4j.v1 import GraphDatabase
import hetio.readwrite
import hetio.neo4j
import pytest

def test_construct_pdp_query():
    """
    Test the pdp computation on the metapath from https://doi.org/10.1371/journal.pcbi.1004259.g002
    """

    # Since we're working on a known nicotine dependency - Bupropion metapath,
    # we already know the dwpc
    dwpc = 0.03287590886921623

    # Set up the graph for querying

    # Should this graph be added to the data directory?
    url = 'https://github.com/dhimmel/hetionet/raw/76550e6c93fbe92124edc71725e8c7dd4ca8b1f5/hetnet/json/hetionet-v1.0.json.bz2'

    graph = hetio.readwrite.read_graph(url)
    assert graph is not None
    metagraph = graph.metagraph

    compound = 'DB01156'  # Bupropion
    disease = 'DOID:0050742'  # nicotine dependency
    damping_exponent = 0.4

    metapath = metagraph.metapath_from_abbrev('CbGpPWpGaD')

    # Calculate the pdp without being provided with the dwpc
    pdp_query = hetio.neo4j.construct_pdp_query(metapath, property='identifier', unique_nodes=True)

    assert len(pdp_query) > 0
    driver = GraphDatabase.driver("bolt://neo4j.het.io")

    params = {
    'source': compound,
    'target': disease,
    'w': damping_exponent,
    }
    with driver.session() as session:
        results = session.run(pdp_query, params)
        results = results.data()

    assert results[0]['path'].start_node['name'] == 'Bupropion'
    assert results[0]['path'].end_node['name'] == 'nicotine dependence'

    percent_dwpc_1 = results[0]['PERCENT_OF_DWPC']

    old_pdp_query = pdp_query

    # Calculate the pdp with the provided dwpc
    pdp_query = hetio.neo4j.construct_pdp_query(metapath, dwpc, property='identifier', unique_nodes=True)

    assert len(pdp_query) > 0
    assert old_pdp_query != pdp_query

    with driver.session() as session:
        results = session.run(pdp_query, params)
        results = results.data()

    assert results[0]['path'].start_node['name'] == 'Bupropion'
    assert results[0]['path'].end_node['name'] == 'nicotine dependence'

    # We'll check this because it verifies both that the DWPC and the PDP for the path
    # are the same for both queries
    assert percent_dwpc_1 == results[0]['PERCENT_OF_DWPC']

    sum_percent = 0
    for result in results:
        sum_percent += result['PERCENT_OF_DWPC']

    # The fractions should all add up to around 100 percent
    assert sum_percent == pytest.approx(100)

def test_construct_dwpc_query():
    url = 'https://github.com/dhimmel/hetionet/raw/76550e6c93fbe92124edc71725e8c7dd4ca8b1f5/hetnet/json/hetionet-v1.0.json.bz2'

    graph = hetio.readwrite.read_graph(url)
    assert graph is not None
    metagraph = graph.metagraph

    compound = 'DB01156'  # Bupropion
    disease = 'DOID:0050742'  # nicotine dependency
    damping_exponent = 0.4

    metapath = metagraph.metapath_from_abbrev('CbGpPWpGaD')

    query = hetio.neo4j.construct_dwpc_query(metapath, property='identifier', unique_nodes=True)
    assert len(query) > 0
    driver = GraphDatabase.driver("bolt://neo4j.het.io")

    params = {
    'source': compound,
    'target': disease,
    'w': damping_exponent,
    }
    with driver.session() as session:
        results = session.run(query, params)
        results = results.single()
        assert results

    dwpc = results['DWPC']
    print(dwpc)

    assert dwpc == pytest.approx(0.03287590886921623)
